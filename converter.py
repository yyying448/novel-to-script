"""
核心转换逻辑
串联章节切分 → 并发 LLM 调用 → YAML 解析 → 结果合并

输出结构：每个场景标注所属章节，前端按章节 + 场景层级展示
"""

import re
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional, Dict, Any, List, Tuple

from chapter_splitter import split_chapters, chunk_long_chapter
from prompts import SYSTEM_PROMPT, CONVERT_CHAPTER_PROMPT, REVISE_SCRIPT_PROMPT
from character_manager import CharacterManager

MAX_CONCURRENT_CHAPTERS = 3
PARTIAL_RESULT_INTERVAL = 3


def _convert_single_chapter(
    chapter: Dict[str, str], llm_client, character_profiles: str = "",
    model: str = "deepseek-chat"
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    转换单个章节，返回 (章节标题, 场景列表)
    接受 character_profiles 注入角色一致性约束
    转换单个章节，返回 (章节标题, 场景列表)
    每个场景自动标注所属章节
    """
    from llm_client import call_llm

    sub_chunks = chunk_long_chapter(chapter)
    chapter_title = chapter["title"]
    chapter_scenes = []

    for chunk in sub_chunks:
        prompt = CONVERT_CHAPTER_PROMPT.format(
            character_profiles=character_profiles,
            chapter_text=chunk["content"]
        )
        response_text = call_llm(llm_client, SYSTEM_PROMPT, prompt, model=model)
        chunk_scenes = _parse_llm_yaml(response_text)
        # 为每个场景打上章节标签
        for scene in chunk_scenes:
            scene["chapter"] = chapter_title
        chapter_scenes.extend(chunk_scenes)

    return chapter_title, chapter_scenes


def convert_novel_to_script(
    novel_text: str,
    llm_client,
    progress_callback: Optional[Callable] = None,
    partial_callback: Optional[Callable] = None,
    model: str = "deepseek-chat",
) -> Dict[str, Any]:
    """
    主转换函数：将小说全文转换为剧本
    """
    chapters = split_chapters(novel_text)
    if not chapters:
        return {"scenes": [], "chapter_map": {}, "error": "未能从文本中识别到任何章节"}

    valid_chapters = [ch for ch in chapters if len(ch["content"].strip()) > 100]
    if not valid_chapters:
        valid_chapters = chapters

    total = len(valid_chapters)

    # 构建章节映射（标题 → 原文截断，供修改时参考）
    chapter_map = {}
    for ch in valid_chapters:
        chapter_map[ch["title"]] = ch["content"]

    # ===== 角色一致性引擎 =====
    char_manager = CharacterManager()

    # chapter_results[i] = (title, scenes)
    chapter_results: List[Optional[Tuple[str, List[Dict]]]] = [None] * total
    last_partial_at = 0

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CHAPTERS) as executor:
        future_to_idx = {}
        for idx, chapter in enumerate(valid_chapters):
            if progress_callback:
                progress_callback(idx + 1, total, chapter["title"], "start")

            # 获取当前已知角色档案（第一章为空，后续逐渐积累）
            char_inject = char_manager.get_consistency_prompt(chapter["title"])

            future = executor.submit(
                _convert_single_chapter, chapter, llm_client, char_inject, model
            )
            future_to_idx[future] = idx

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            chapter = valid_chapters[idx]

            try:
                title, scenes = future.result()
                chapter_results[idx] = (title, scenes)
                # 注册本章角色（零额外 LLM 开销）
                char_manager.register_from_scenes(scenes, title)
            except Exception as e:
                chapter_results[idx] = (chapter["title"], [{
                    "chapter": chapter["title"],
                    "location": "未知",
                    "characters_present": [],
                    "summary": f"⚠️ 转换失败：{chapter['title']}",
                    "dialogues": [],
                    "scene_notes": f"LLM 调用出错：{str(e)}"
                }])

            completed_count = sum(1 for r in chapter_results if r is not None)

            if progress_callback:
                progress_callback(completed_count, total, chapter["title"], "done")

            # 每 N 章推送中间结果（含角色数据）
            if partial_callback and completed_count - last_partial_at >= PARTIAL_RESULT_INTERVAL:
                last_partial_at = completed_count
                partial_scenes = _assemble_scenes(chapter_results)
                partial_characters = char_manager.get_summary()
                partial_callback(partial_scenes, partial_characters, completed_count, total)

    # 组装最终结果
    all_scenes = _assemble_scenes(chapter_results)
    characters_summary = char_manager.get_summary()

    # 深度角色分析（性格/动机/外貌等）
    try:
        report = char_manager.deep_analyze(llm_client)
        _apply_deep_analysis(characters_summary, report)
    except Exception:
        pass  # 分析失败不影响主流程

    return {
        "scenes": all_scenes,
        "chapter_map": chapter_map,
        "characters": characters_summary,
        "character_count": len(characters_summary)
    }

def _apply_deep_analysis(characters: list, report: str):
    """将 LLM 生成的角色报告回填到档案中"""
    import re
    for char in characters:
        name = char.get("name", "")
        # 在报告中查找该角色的分析段落
        pattern = rf'###\s*{re.escape(name)}.*?\n(.*?)(?=###\s|\Z)'
        match = re.search(pattern, report, re.DOTALL)
        if match:
            block = match.group(1)
            # 提取各字段
            for field, key in [("性格", "personality"), ("说话风格", "speech_style"),
                               ("身份定位", "identity"), ("核心动机", "motivation"),
                               ("外貌特征", "appearance")]:
                m = re.search(rf'{field}[：:]\s*(.+)', block)
                if m:
                    char[key] = m.group(1).strip()


def _assemble_scenes(
    chapter_results: List[Optional[Tuple[str, List[Dict]]]]
) -> List[Dict]:
    """Assemble chapter results in order, assign global scene IDs"""
    all_scenes = []
    scene_id_counter = 1
    for item in chapter_results:
        if item:
            _title, scenes = item
            for scene in scenes:
                scene["scene_id"] = scene_id_counter
                scene_id_counter += 1
            all_scenes.extend(scenes)
    return all_scenes


def revise_script(
    chapter_text: str,
    existing_yaml: str,
    feedback: str,
    llm_client,
    model: str = "deepseek-chat",
) -> Dict[str, Any]:
    """
    根据用户修改意见，二次生成剧本
    """
    from llm_client import call_llm

    # 截断保护
    truncated_text = chapter_text[:8000]
    truncated_yaml = existing_yaml[:20000]
    if len(existing_yaml) > 20000:
        truncated_yaml += "\n...（截断）"

    prompt = REVISE_SCRIPT_PROMPT.format(
        chapter_text=truncated_text,
        existing_yaml=truncated_yaml,
        user_feedback=feedback
    )

    response_text = call_llm(llm_client, SYSTEM_PROMPT, prompt, model=model)

    # 两阶段容错解析
    scenes = _parse_llm_yaml(response_text)
    if not scenes:
        scenes = _parse_llm_yaml_fallback(response_text)

    if not scenes:
        raise ValueError(
            "AI 未能生成有效剧本。建议：1) 缩小修改范围（如只改一句台词）；2) 试试换个说法描述修改意见"
        )

    return {"scenes": scenes}


# ============================================================
# YAML 解析（两层容错）
# ============================================================

def _parse_llm_yaml(text: str) -> list:
    """第一层：标准 YAML 解析"""
    if not text or not text.strip():
        return []

    text = text.strip()

    yaml_pattern = r'```(?:yaml|yml)?\s*\n(.*?)```'
    matches = re.findall(yaml_pattern, text, re.DOTALL)
    if matches:
        text = matches[0].strip()

    if not text.startswith("scenes:"):
        scenes_pos = text.find("\nscenes:")
        if scenes_pos == -1:
            scenes_pos = text.find("scenes:")
        if scenes_pos > 0:
            text = text[scenes_pos:]

    try:
        result = yaml.safe_load(text)
        if isinstance(result, dict) and "scenes" in result:
            return result["scenes"]
        elif isinstance(result, list):
            return result
        return []
    except yaml.YAMLError:
        return []


def _parse_llm_yaml_fallback(text: str) -> list:
    """第二层：修复常见错误后重试"""
    text = _fix_common_yaml_errors(text)
    try:
        result = yaml.safe_load(text)
        if isinstance(result, dict) and "scenes" in result:
            return result["scenes"]
        elif isinstance(result, list):
            return result
        return []
    except yaml.YAMLError:
        return []


def _fix_common_yaml_errors(text: str) -> str:
    """修复 LLM 输出的常见 YAML 错误"""
    lines = text.split("\n")
    fixed_lines = []
    for line in lines:
        if ":" in line and not line.strip().startswith("#"):
            parts = line.split(":", 1)
            if len(parts) == 2 and parts[1] and not parts[1].startswith(" "):
                if parts[1].strip() and not parts[1].strip().startswith('"'):
                    line = f"{parts[0]}: {parts[1]}"
        fixed_lines.append(line)
    return "\n".join(fixed_lines)
