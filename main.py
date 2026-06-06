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
    episode_minutes: float = 0
    selected_chapters: str = ""   # JSON 数组，空=全选
    requirement: str = ""         # 转换要求，追加到 prompt
    compare_keys: str = ""
    compare_models: str = ""
    compare_providers: str = ""
    compare_urls: str = ""  # JSON 数组，自定义 base_url


class ReviseRequest(BaseModel):
    chapter_text: str
    existing_yaml: str = ""
    feedback: str
    api_key: str
    provider: str = "deepseek"
    base_url: Optional[str] = None
    model: Optional[str] = None
    chapter_title: str = ""


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
        ch_map = {}
        for ch in chapters:
            ch_map[ch["title"]] = ch["content"]

        return JSONResponse({
            "success": True,
            "chapter_count": len(chapters),
            "chapters": summary,
            "chapter_map": ch_map
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
    event_loop = asyncio.get_running_loop()

    # 构建所有待运行的模型配置
    from llm_client import create_client, get_default_model
    import json as _json

    model_configs = [{
        "label": "模型 A",
        "api_key": req.api_key,
        "provider": req.provider,
        "model": req.model or get_default_model(req.provider),
        "base_url": req.base_url,
    }]
    # 对比模型 B, C
    if req.compare_keys:
        try:
            extra_keys = _json.loads(req.compare_keys) if isinstance(req.compare_keys, str) else req.compare_keys
            extra_models = _json.loads(req.compare_models) if isinstance(req.compare_models, str) and req.compare_models else []
            extra_providers = _json.loads(req.compare_providers) if isinstance(req.compare_providers, str) and req.compare_providers else []
            extra_urls = _json.loads(req.compare_urls) if isinstance(req.compare_urls, str) and req.compare_urls else []
        except Exception:
            extra_keys, extra_models, extra_providers, extra_urls = [], [], [], []
        labels = ["模型 B", "模型 C"]
        for i, key in enumerate(extra_keys[:2]):
            if key:
                provider = extra_providers[i] if i < len(extra_providers) else "deepseek"
                model = extra_models[i] if i < len(extra_models) else get_default_model(provider)
                base = extra_urls[i] if i < len(extra_urls) else None
                model_configs.append({
                    "label": labels[i],
                    "api_key": key,
                    "provider": provider,
                    "model": model,
                    "base_url": base or None,
                })

    total_models = len(model_configs)
    all_results = [None] * total_models

    # 统一计算过滤文本（所有模型共享）
    from chapter_splitter import split_chapters as _split
    req_text = req.text
    if req.selected_chapters:
        try:
            selected = _json.loads(req.selected_chapters) if isinstance(req.selected_chapters, str) else req.selected_chapters
            if selected:
                chapters_all = _split(req.text)
                filtered = ""
                for ch in chapters_all:
                    if ch["title"] in selected:
                        filtered += ch["title"] + "\n" + ch["content"] + "\n\n"
                if filtered: req_text = filtered
        except Exception:
            pass

    def run_single_model(idx: int, cfg: dict):
        """在独立线程中运行单个模型的完整转换流程"""
        label = cfg["label"]
        try:
            client = create_client(cfg["api_key"], provider=cfg["provider"], base_url=cfg.get("base_url"))
            model = cfg["model"]

            # 第一个模型负责章节切分和策略
            if idx == 0:
                from chapter_splitter import split_chapters, get_chapter_summary
                chapters = split_chapters(req.text)
                summary = get_chapter_summary(chapters)
                ch_map = {}
                for ch in chapters:
                    ch_map[ch["title"]] = ch["content"]

                _put_sync(queue, {
                    "type": "chapters", "data": summary, "count": len(chapters),
                    "chapter_map": ch_map
                }, event_loop)

                from adaptation_agent import generate_adaptation_strategy
                strategy_report = generate_adaptation_strategy(req.text, summary, client, model=model)
                _put_sync(queue, {"type": "strategy", "report": strategy_report}, event_loop)
            else:
                chapters = []
                ch_map = {}
                strategy_report = None

            from converter import convert_novel_to_script

            def on_progress(current: int, total: int, title: str, status: str):
                _put_sync(queue, {
                    "type": "progress", "label": label,
                    "current": current, "total": total,
                    "title": title, "status": status,
                    "percent": round(current / total * 100) if total > 0 else 0
                }, event_loop)

            def on_partial(scenes: list, characters: list, completed: int, total: int):
                _put_sync(queue, {
                    "type": "partial", "label": label,
                    "scenes": scenes, "characters": characters,
                    "completed": completed, "total": total
                }, event_loop)

            result = convert_novel_to_script(
                req_text, client,
                progress_callback=on_progress,
                partial_callback=on_partial,
                model=model,
                requirement=req.requirement,
            )

            from adaptation_agent import analyze_all_scenes, estimate_total_runtime, split_into_episodes, annotate_conflicts
            result["scenes"] = analyze_all_scenes(result.get("scenes") or [])
            result["scenes"] = annotate_conflicts(result["scenes"])
            runtime = estimate_total_runtime(result["scenes"])
            result["runtime"] = {"min": runtime[0], "likely": runtime[1], "max": runtime[2]}

            if req.episode_minutes > 0:
                result["episodes"] = split_into_episodes(result["scenes"], target_minutes=req.episode_minutes, chapter_map=ch_map or {})
                result["episode_count"] = len(result["episodes"])
            else:
                result["episodes"] = []
                result["episode_count"] = 0

            all_results[idx] = {"label": label, "result": result}
            # 推送完整的单模型结果（含角色/分集/时长）
            _put_sync(queue, {
                "type": "model_done",
                "label": label,
                "idx": idx,
                "scenes": result.get("scenes") or [],
                "characters": result.get("characters") or [],
                "character_count": result.get("character_count") or 0,
                "episodes": result.get("episodes") or [],
                "episode_count": result.get("episode_count") or 0,
                "runtime": result.get("runtime") or {},
            }, event_loop)

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg:
                err_msg = f"{label} 频率限制（429），请稍后重试或更换 API Key"
            elif "401" in err_msg or "403" in err_msg:
                err_msg = f"{label} Key 无效或权限不足"
            all_results[idx] = {"label": label, "error": err_msg}
            _put_sync(queue, {"type": "model_done", "label": label, "idx": idx, "error": err_msg}, event_loop)

    # 并行启动所有模型
    threads = []
    for i, cfg in enumerate(model_configs):
        t = Thread(target=run_single_model, args=(i, cfg), daemon=True)
        t.start()
        threads.append(t)

    # 后台等待所有模型完成，然后推送 done
    def finalize():
        for t in threads:
            t.join()
        # 裁判评分：转换 all_results 格式
        judge_input = []
        for r in all_results:
            if r and "result" in r:
                judge_input.append({"label": r["label"], "scenes": r["result"].get("scenes") or []})
            elif r:
                judge_input.append({"label": r["label"], "scenes": []})
        if len(judge_input) >= 2:
            scores = _judge_results(judge_input, req)
        else:
            scores = {}
        # 找第一个成功的结果作为主结果
        main = next((r for r in all_results if r and "result" in r), all_results[0])
        main_result = main.get("result", {}) if main else {}
        # 组装 compare 数据
        compare_data = []
        for r in all_results:
            if not r: continue
            scenes = r.get("result", {}).get("scenes", []) if "result" in r else []
            compare_data.append({
                "label": r["label"],
                "scene_count": len(scenes),
                "score": scores.get(r["label"], "N/A"),
                "error": r.get("error", ""),
                "preview": scenes[:3],
                "all_scenes": scenes,
            })
        _put_sync(queue, {"type": "compare", "results": compare_data}, event_loop)
        _put_sync(queue, {
            "type": "done",
            "result": main_result,
            "scene_count": len(main_result.get("scenes") or []),
            "character_count": main_result.get("character_count") or 0,
            "runtime": main_result.get("runtime") or {},
            "episode_count": main_result.get("episode_count", 0),
            "all_results": [{
                "label": r["label"],
                "scenes": (r.get("result", {}).get("scenes") or []) if "result" in r else [],
                "characters": (r.get("result", {}).get("characters") or []) if "result" in r else [],
                "episodes": (r.get("result", {}).get("episodes") or []) if "result" in r else [],
                "runtime": (r.get("result", {}).get("runtime") or {}) if "result" in r else {},
                "character_count": (r.get("result", {}).get("character_count") or 0) if "result" in r else 0,
                "episode_count": (r.get("result", {}).get("episode_count") or 0) if "result" in r else 0,
                "error": r.get("error") or ""
            } for r in all_results if r]
        }, event_loop)

    Thread(target=finalize, daemon=True).start()

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
# API：AI 改写/扩写选中文本
# ============================================================
@app.post("/api/ai-edit")
async def ai_edit(req: ReviseRequest):
    """对选中的文本进行 AI 改写或扩写"""
    try:
        from llm_client import create_client, call_llm, get_default_model

        client = create_client(req.api_key, provider=req.provider, base_url=req.base_url)
        model = req.model or get_default_model(req.provider)

        prompt = f"""请根据以下要求处理这段小说文本：

=== 原文 ===
{req.chapter_text}
===

=== 处理要求 ===
{req.feedback}
===

请直接输出处理后的文本，不要添加任何解释。"""

        result = call_llm(client, "你是一位专业的小说编辑，擅长改写和扩写文本。只输出处理后的文本，不要加任何前言后语。", prompt, model=model, max_tokens=2048)
        return JSONResponse({"success": True, "text": result.strip()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


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
            chapter_title=req.chapter_title,
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
# 多模型对比
# ============================================================

def _run_comparison(req: ConvertRequest, main_result: dict, queue: asyncio.Queue, loop):
    """运行对比模型并评分"""
    import json as _json
    from llm_client import create_client, call_llm, get_default_model
    from converter import convert_novel_to_script

    try:
        keys = _json.loads(req.compare_keys) if req.compare_keys else []
        models = _json.loads(req.compare_models) if req.compare_models else []
        providers = _json.loads(req.compare_providers) if req.compare_providers else []
    except Exception:
        return

    if not keys:
        return

    all_results = [{"label": "模型 A", "scenes": main_result.get("scenes", [])}]
    names = ["模型 B", "模型 C"]

    for i, key in enumerate(keys[:2]):
        label = names[i] if i < len(names) else f"模型 {i+2}"
        try:
            provider = providers[i] if i < len(providers) else req.provider
            model = models[i] if i < len(models) else get_default_model(provider)
            client = create_client(key, provider=provider)
            try:
                result = convert_novel_to_script(req.text, client, model=model)
            except Exception as e2:
                result = {"scenes": [], "characters": [], "error": str(e2)}
            all_results.append({"label": label, "scenes": result.get("scenes", [])})
        except Exception as e:
            all_results.append({"label": label, "scenes": [], "error": str(e)})

    # 裁判评分
    if len(all_results) >= 2:
        scores = _judge_results(all_results, req)
        # 每个结果只传前 3 个场景预览，完整数据存 state
        results_preview = []
        for r in all_results:
            if not r: continue
            scenes = (r.get("result", {}) or {}).get("scenes", []) if "result" in r else r.get("scenes", [])
            if not scenes: scenes = []
            preview = scenes[:3]
            results_preview.append({
                "label": r["label"],
                "scene_count": len(scenes),
                "score": scores.get(r["label"], "N/A"),
                "error": r.get("error", ""),
                "preview": preview,
                "all_scenes": scenes
            })
        _put_sync(queue, {
            "type": "compare",
            "results": results_preview
        }, loop)


def _judge_results(results: list, req: ConvertRequest) -> dict:
    """让 LLM 裁判对多个剧本打分"""
    from llm_client import create_client, call_llm

    msg = "请从以下维度为 3 个剧本打分（每项 1-10 分）：\n"
    msg += "1) 对话自然度 2) 场景完整性 3) 叙事流畅度 4) 角色一致性\n\n"

    for r in results:
        sc = r.get("scenes") or []
        scenes = sc[:5]
        preview = "\n".join([
            f"  场景{s.get('scene_id','?')}: {s.get('summary','?')} [{s.get('location','?')}]"
            for s in scenes
        ])
        msg += f"=== {r['label']}（{len(sc)} 场）===\n{preview}\n\n"

    msg += "请输出 JSON。注意：必须给每个模型不同的分数以体现差异，不要打平。格式：{\"模型 A\": {\"总分\": 35, \"评语\": \"优势是...\"}, ...}"

    try:
        client = create_client(req.api_key, provider=req.provider, base_url=req.base_url)
        response = call_llm(client, "你是专业剧本评审。只输出 JSON，不要解释。", msg,
                           model=req.model or "deepseek-v4-pro", max_tokens=1024)
        import json as _json
        # 提取 JSON：尝试多种方式
        text = response.strip()
        if "```" in text:
            # 提取代码块
            import re
            m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
            if m: text = m.group(1).strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return _json.loads(text[start:end])
    except Exception as e:
        print(f"Judge error: {e}")
    return {}


# ================================================================
# 工具函数
# ================================================================

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
