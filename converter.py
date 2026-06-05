"""
核心转换逻辑
串联章节切分 → 并发 LLM 调用 → YAML 解析 → 结果合并
"""

import re
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional, Dict, Any, List

from chapter_splitter import split_chapters, chunk_long_chapter
from prompts import SYSTEM_PROMPT, CONVERT_CHAPTER_PROMPT, REVISE_SCRIPT_PROMPT

# 并发处理的章节数（同时调用 LLM 的章节上限）
MAX_CONCURRENT_CHAPTERS = 3


def _convert_single_chapter(chapter: Dict[str, str], llm_client) -> List[Dict[str, Any]]:
    """
    转换单个章节，返回该章的所有场景列表（不含 scene_id）

    Args:
        chapter: 包含 title 和 content 的章节字典
        llm_client: OpenAI 客户端实例

    Returns:
        该章的 scenes 列表
    """
    from llm_client import call_llm

    sub_chunks = chunk_long_chapter(chapter)
    chapter_scenes = []

    for chunk in sub_chunks:
        prompt = CONVERT_CHAPTER_PROMPT.format(chapter_text=chunk["content"])
        response_text = call_llm(llm_client, SYSTEM_PROMPT, prompt)
        chunk_scenes = _parse_llm_yaml(response_text)
        chapter_scenes.extend(chunk_scenes)

    return chapter_scenes


def convert_novel_to_script(
    novel_text: str,
    llm_client,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    主转换函数：将小说全文转换为剧本 YAML

    改进点：
    - 并发处理：同时转换 3 个章节（ThreadPoolExecutor）
    - 即时反馈：每章开始时推送"正在处理"、完成时推送"已完成"
    - 保序：场景按原文章节顺序排列

    Args:
        novel_text: 小说全文文本
        llm_client: OpenAI 客户端实例
        progress_callback: 进度回调函数，
            签名: (current: int, total: int, title: str, status: str) -> None
            status 为 "start"（开始处理）或 "done"（处理完成）

    Returns:
        完整的剧本字典，包含 scenes 列表
    """
    # 第一步：切分章节
    chapters = split_chapters(novel_text)

    if not chapters:
        return {"scenes": [], "error": "未能从文本中识别到任何章节"}

    # 过滤掉内容过短的章节（可能是误识别）
    valid_chapters = [ch for ch in chapters if len(ch["content"].strip()) > 100]

    if not valid_chapters:
        valid_chapters = chapters  # 如果都太短，保留所有

    total = len(valid_chapters)

    # 第二步：并发转换各章
    # chapter_results[i] 对应 valid_chapters[i] 的 scenes
    chapter_results: List[Optional[List[Dict]]] = [None] * total

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CHAPTERS) as executor:
        # 提交所有任务，同时在提交时推送"开始"进度
        future_to_idx = {}
        for idx, chapter in enumerate(valid_chapters):
            if progress_callback:
                progress_callback(idx + 1, total, chapter["title"], "start")
            future = executor.submit(_convert_single_chapter, chapter, llm_client)
            future_to_idx[future] = idx

        # 按完成顺序收集结果，推送"完成"进度
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            chapter = valid_chapters[idx]

            try:
                scenes = future.result()
                chapter_results[idx] = scenes
            except Exception as e:
                # 单章失败不中断全局，在 scene_notes 中记录错误
                chapter_results[idx] = [{
                    "location": "未知",
                    "characters_present": [],
                    "summary": f"⚠️ 转换失败：{chapter['title']}",
                    "dialogues": [],
                    "scene_notes": f"LLM 调用出错：{str(e)}"
                }]

            if progress_callback:
                completed_count = sum(1 for r in chapter_results if r is not None)
                progress_callback(completed_count, total, chapter["title"], "done")

    # 第三步：按原章节顺序组装结果，分配全局 scene_id
    all_scenes = []
    scene_id_counter = 1

    for scenes in chapter_results:
        if scenes:
            for scene in scenes:
                scene["scene_id"] = scene_id_counter
                scene_id_counter += 1
            all_scenes.extend(scenes)

    return {"scenes": all_scenes}


def revise_script(
    chapter_text: str,
    existing_yaml: str,
    feedback: str,
    llm_client
) -> Dict[str, Any]:
    """
    根据用户修改意见，二次生成剧本

    Args:
        chapter_text: 原始小说文本
        existing_yaml: 当前版本的 YAML 文本
        feedback: 用户的修改意见
        llm_client: OpenAI 客户端实例

    Returns:
        修改后的剧本字典
    """
    from llm_client import call_llm

    prompt = REVISE_SCRIPT_PROMPT.format(
        chapter_text=chapter_text[:10000],  # 截断，防止超 token 限制
        existing_yaml=existing_yaml,
        user_feedback=feedback
    )

    response_text = call_llm(llm_client, SYSTEM_PROMPT, prompt)
    scenes = _parse_llm_yaml(response_text)

    return {"scenes": scenes}


def _parse_llm_yaml(text: str) -> list:
    """
    从 LLM 返回的文本中提取并解析 YAML

    处理常见情况：
    1. LLM 返回纯 YAML
    2. LLM 返回 markdown 代码块包裹的 YAML
    3. LLM 在 YAML 前后加了解释文字

    Args:
        text: LLM 返回的原始文本

    Returns:
        解析后的 scenes 列表
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    # 尝试1：提取 markdown 代码块中的 YAML
    yaml_pattern = r'```(?:yaml|yml)?\s*\n(.*?)```'
    matches = re.findall(yaml_pattern, text, re.DOTALL)
    if matches:
        text = matches[0].strip()

    # 尝试2：如果文本以 `scenes:` 开头，直接解析
    # 否则尝试找到 `scenes:` 的位置
    if not text.startswith("scenes:"):
        scenes_pos = text.find("\nscenes:")
        if scenes_pos == -1:
            scenes_pos = text.find("scenes:")
        if scenes_pos > 0:
            text = text[scenes_pos:]

    # 解析 YAML
    try:
        result = yaml.safe_load(text)
        if isinstance(result, dict) and "scenes" in result:
            return result["scenes"]
        elif isinstance(result, list):
            # LLM 直接返回了 scenes 列表
            return result
        else:
            return []
    except yaml.YAMLError:
        # 解析失败，尝试修复常见问题后重试
        text = _fix_common_yaml_errors(text)
        try:
            result = yaml.safe_load(text)
            if isinstance(result, dict) and "scenes" in result:
                return result["scenes"]
            return []
        except yaml.YAMLError:
            return []


def _fix_common_yaml_errors(text: str) -> str:
    """
    修复 LLM 在 YAML 输出中的常见错误
    """
    lines = text.split("\n")
    fixed_lines = []

    for line in lines:
        # 修复：行首缺空格缩进
        # 修复：冒号后缺空格
        if ":" in line and not line.strip().startswith("#"):
            parts = line.split(":", 1)
            if len(parts) == 2 and parts[1] and not parts[1].startswith(" "):
                if parts[1].strip() and not parts[1].strip().startswith('"'):
                    line = f"{parts[0]}: {parts[1]}"

        # 修复：中文字符导致的引号问题
        # 不处理，保留原样

        fixed_lines.append(line)

    return "\n".join(fixed_lines)
