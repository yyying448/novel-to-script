"""
FastAPI 后端主入口
提供页面渲染 + API 接口
"""

import json
import asyncio
from threading import Thread
from typing import Optional

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="AI小说转剧本工具")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 模板
templates = Jinja2Templates(directory="templates")


# ============================================================
# 请求模型
# ============================================================

class ConvertRequest(BaseModel):
    text: str
    api_key: str
    provider: str = "deepseek"
    base_url: Optional[str] = None
    model: Optional[str] = None
    episode_minutes: float = 0  # 0=不分集，>0=目标单集时长（分钟）


class ReviseRequest(BaseModel):
    chapter_text: str
    existing_yaml: str
    feedback: str
    api_key: str
    provider: str = "deepseek"
    base_url: Optional[str] = None
    model: Optional[str] = None


# ============================================================
# 页面路由
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


# ============================================================
# API：获取可用 LLM 厂商列表
# ============================================================
@app.get("/api/providers")
async def get_providers():
    """返回所有支持的 LLM 厂商及默认配置"""
    from llm_client import get_provider_list
    return JSONResponse({"success": True, "providers": get_provider_list()})


# ============================================================
# API：验证 API Key
# ============================================================
@app.post("/api/validate-key")
async def validate_key(req: ConvertRequest):
    """
    验证 DeepSeek API Key 是否有效
    发送一条极短测试请求，确认 Key 可用
    """
    try:
        from llm_client import test_api_key

        valid, message = test_api_key(
            req.api_key, provider=req.provider, base_url=req.base_url
        )
        return JSONResponse({
            "success": valid,
            "message": message
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"验证异常：{str(e)}"
        }, status_code=500)


# ============================================================
# API：文件解析
# ============================================================
@app.post("/api/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """
    解析上传的小说文件（支持 .txt / .docx / .pdf）
    返回提取的文本内容
    """
    try:
        from file_parser import parse_uploaded_file

        content = await file.read()
        text, file_type = parse_uploaded_file(content, file.filename)

        return JSONResponse({
            "success": True,
            "text": text,
            "char_count": len(text),
            "file_type": file_type,
            "filename": file.filename
        })

    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "error": f"文件解析失败：{str(e)}"}, status_code=500)


# ============================================================
# API：预览章节切分
# ============================================================
@app.post("/api/preview-chapters")
async def preview_chapters(req: ConvertRequest):
    """
    预览章节切分结果（不调用 LLM，仅展示章节识别结果）
    用于用户在转换前确认章节切分是否正确
    """
    try:
        from chapter_splitter import split_chapters, get_chapter_summary

        chapters = split_chapters(req.text)
        summary = get_chapter_summary(chapters)

        return JSONResponse({
            "success": True,
            "chapter_count": len(chapters),
            "chapters": summary
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ============================================================
# API：转换小说为剧本（SSE 流式推送进度）
# ============================================================
@app.post("/api/convert")
async def convert(req: ConvertRequest):
    """
    将小说文本转换为剧本 YAML

    使用 SSE (Server-Sent Events) 流式返回：
    - {"type": "chapters", "data": [...]}       → 章节识别结果
    - {"type": "progress", "current": N, ...}   → 逐章进度
    - {"type": "done", "result": {...}}         → 最终结果
    - {"type": "error", "message": "..."}       → 错误
    """
    queue: asyncio.Queue = asyncio.Queue()
    # 在异步上下文中捕获事件循环引用（工作线程里拿不到，必须在这里拿）
    event_loop = asyncio.get_running_loop()

    def run_conversion():
        """在独立线程中运行转换（避免阻塞事件循环）"""
        try:
            # 创建 LLM 客户端（多厂商适配）
            from llm_client import create_client, get_default_model
            client = create_client(req.api_key, provider=req.provider, base_url=req.base_url)
            model = req.model or get_default_model(req.provider)

            # 切分章节
            from chapter_splitter import split_chapters, get_chapter_summary
            chapters = split_chapters(req.text)
            summary = get_chapter_summary(chapters)

            # 构建章节标题→原文映射（供前端修改时精准定位章节）
            ch_map = {}
            for ch in chapters:
                ch_map[ch["title"]] = ch["content"][:8000]

            # 推送章节识别结果（携带章节原文映射）
            _put_sync(queue, {
                "type": "chapters",
                "data": summary,
                "count": len(chapters),
                "chapter_map": ch_map
            }, event_loop)

            # ===== 改编策略报告 =====
            from adaptation_agent import generate_adaptation_strategy
            strategy_report = generate_adaptation_strategy(
                req.text, summary, client, model=model
            )
            _put_sync(queue, {
                "type": "strategy",
                "report": strategy_report
            }, event_loop)

            # 执行转换
            from converter import convert_novel_to_script

            def on_progress(current: int, total: int, title: str, status: str):
                """进度回调：每章开始时推送"开始处理"，完成时推送"已完成" """
                _put_sync(queue, {
                    "type": "progress",
                    "current": current,
                    "total": total,
                    "title": title,
                    "status": status,
                    "percent": round(current / total * 100) if total > 0 else 0
                }, event_loop)

            def on_partial(scenes: list, characters: list, completed: int, total: int):
                """每完成 N 章推送一次中间结果（含角色档案）"""
                _put_sync(queue, {
                    "type": "partial",
                    "scenes": scenes,
                    "characters": characters,
                    "completed": completed,
                    "total": total
                }, event_loop)

            result = convert_novel_to_script(
                req.text, client,
                progress_callback=on_progress,
                partial_callback=on_partial,
                model=model,
            )

            # ===== 场景分析（时长/难度/不可拍内容/戏剧功能）=====
            from adaptation_agent import analyze_all_scenes, estimate_total_runtime, split_into_episodes
            result["scenes"] = analyze_all_scenes(result.get("scenes", []))
            runtime = estimate_total_runtime(result["scenes"])
            result["runtime"] = {
                "min": runtime[0], "likely": runtime[1], "max": runtime[2]
            }

            # ===== 分集拆分 =====
            if req.episode_minutes > 0:
                episodes = split_into_episodes(
                    result["scenes"],
                    target_minutes=req.episode_minutes,
                    chapter_map=ch_map,
                )
                result["episodes"] = episodes
                result["episode_count"] = len(episodes)
            else:
                result["episodes"] = []
                result["episode_count"] = 0

            # 推送最终结果（含所有分析数据）
            scene_count = len(result.get("scenes", []))
            char_count = result.get("character_count", 0)
            _put_sync(queue, {
                "type": "done",
                "result": result,
                "scene_count": scene_count,
                "chapter_count": len(chapters),
                "chapter_map": ch_map,
                "character_count": char_count,
                "strategy_report": strategy_report,
                "runtime": result.get("runtime", {}),
                "episode_count": result.get("episode_count", 0)
            }, event_loop)

        except Exception as e:
            _put_sync(queue, {
                "type": "error",
                "message": str(e)
            }, event_loop)

    # 启动转换线程
    Thread(target=run_conversion, daemon=True).start()

    # SSE 生成器
    async def generate():
        while True:
            data = await queue.get()
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            if data["type"] in ("done", "error"):
                break

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        }
    )


# ============================================================
# API：根据意见修改剧本
# ============================================================
@app.post("/api/revise")
async def revise(req: ReviseRequest):
    """
    根据用户意见二次生成剧本
    """
    try:
        from llm_client import create_client, get_default_model
        from converter import revise_script

        client = create_client(req.api_key, provider=req.provider, base_url=req.base_url)
        model = req.model or get_default_model(req.provider)
        result = revise_script(
            chapter_text=req.chapter_text,
            existing_yaml=req.existing_yaml,
            feedback=req.feedback,
            llm_client=client,
            model=model,
        )

        scene_count = len(result.get("scenes", []))
        return JSONResponse({
            "success": True,
            "result": result,
            "scene_count": scene_count
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ============================================================
# 工具函数
# ============================================================

def _put_sync(queue: asyncio.Queue, data: dict, loop: asyncio.AbstractEventLoop):
    """
    线程安全地向 asyncio.Queue 写入数据
    从同步线程中调用此函数来向异步队列推送事件

    Args:
        queue: asyncio 队列
        data: 要推送的数据
        loop: 主线程的事件循环（必须在异步上下文中预先捕获后传入）
    """
    loop.call_soon_threadsafe(queue.put_nowait, data)


# ============================================================
# 启动入口
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
