"""
章节自动识别与切分
支持中英文多种章节标题格式
"""

import re
from typing import List, Dict


def split_chapters(text: str) -> List[Dict[str, str]]:
    """
    将小说全文按章节标题自动切分

    支持的格式（按优先级）：
    1. "第X章 ..."（中文数字或阿拉伯数字）
    2. "第X节 ..."
    3. "Chapter X ..."（英文）
    4. 纯数字分隔如 "1. "、"一、"

    Args:
        text: 小说全文文本

    Returns:
        章节列表，每项包含 title 和 content
        如果未识别到章节结构，返回包含全文的单一章节
    """
    # 按优先级尝试多种切割模式
    patterns = [
        # 模式1：第[数字]章 + 可选标题
        r'\n\s*(第[零一二三四五六七八九十百千\d]+章[^\n]*)',
        # 模式2：第[数字]节 + 可选标题
        r'\n\s*(第[零一二三四五六七八九十百千\d]+节[^\n]*)',
        # 模式3：Chapter + 数字
        r'\n\s*(Chapter\s+\d+[^\n]*)',
        # 模式4：卷/部/篇
        r'\n\s*(第[零一二三四五六七八九十百千\d]+[卷部篇][^\n]*)',
    ]

    for pattern in patterns:
        # 在全文前加一个换行，确保开头的章节也能被匹配
        search_text = "\n" + text
        parts = re.split(pattern, search_text)

        if len(parts) > 1:
            chapters = []
            # parts[0] 是第一个标题前的内容（序言/简介）
            if parts[0].strip():
                chapters.append({
                    "title": "序章/前言",
                    "content": parts[0].strip()
                })

            # 后续每两个元素为一组：(标题, 正文)
            for i in range(1, len(parts), 2):
                title = parts[i].strip()
                content = parts[i + 1].strip() if i + 1 < len(parts) else ""
                if content:  # 跳过空章节
                    chapters.append({
                        "title": title,
                        "content": content
                    })

            # 只有识别到至少2个章节才返回（1个说明切割失败）
            if len(chapters) >= 2:
                return chapters

    # 兜底：整文作为一个章节
    if text.strip():
        return [{"title": "全文", "content": text.strip()}]
    return []


def estimate_tokens(text: str) -> int:
    """
    粗略估算文本的 token 数量

    中文：约 1 字 ≈ 1.5 tokens
    英文：约 1 词 ≈ 1.3 tokens
    这里用简化计算：字符数 × 1.5

    Args:
        text: 输入文本

    Returns:
        估算的 token 数量
    """
    return int(len(text) * 1.5)


def chunk_long_chapter(chapter: Dict[str, str], max_chars: int = 50000) -> List[Dict[str, str]]:
    """
    如果单个章节过长（超过 LLM 上下文窗口的安全阈值），按段落进一步切分

    安全阈值设为 50000 字 ≈ 75000 tokens，低于 DeepSeek 的 128K 上限

    Args:
        chapter: 包含 title 和 content 的章节字典
        max_chars: 单块最大字符数

    Returns:
        切分后的章节列表（大多数情况下只有1个元素）
    """
    content = chapter["content"]
    if len(content) <= max_chars:
        return [chapter]

    # 按段落切分
    paragraphs = content.split("\n\n")
    chunks = []
    current_chunk = ""
    chunk_idx = 1

    for para in paragraphs:
        if len(current_chunk) + len(para) > max_chars and current_chunk:
            chunks.append({
                "title": f"{chapter['title']}（第{chunk_idx}段）",
                "content": current_chunk.strip()
            })
            current_chunk = para
            chunk_idx += 1
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        label = f"（第{chunk_idx}段）" if chunk_idx > 1 else ""
        chunks.append({
            "title": chapter["title"] + label,
            "content": current_chunk.strip()
        })

    return chunks


def get_chapter_summary(chapters: List[Dict[str, str]]) -> List[Dict]:
    """
    生成章节摘要信息（供前端预览）

    Args:
        chapters: 章节列表

    Returns:
        包含标题和字数统计的摘要列表
    """
    return [
        {
            "title": ch["title"],
            "char_count": len(ch["content"]),
            "estimated_tokens": estimate_tokens(ch["content"])
        }
        for ch in chapters
    ]
