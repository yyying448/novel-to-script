"""
文件解析模块
支持 txt / docx / pdf 三种格式的文本提取
"""

import io
from typing import Tuple


def parse_uploaded_file(file_content: bytes, filename: str) -> Tuple[str, str]:
    """
    解析上传的文件，提取文本内容

    Args:
        file_content: 文件的原始字节内容
        filename: 原始文件名（用于判断格式）

    Returns:
        (提取的文本, 文件格式类型)

    Raises:
        ValueError: 不支持的文件格式
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".txt"):
        text = _parse_txt(file_content)
        return text, "txt"

    elif filename_lower.endswith(".docx"):
        text = _parse_docx(file_content)
        return text, "docx"

    elif filename_lower.endswith(".pdf"):
        text = _parse_pdf(file_content)
        return text, "pdf"

    else:
        raise ValueError(f"不支持的文件格式：{filename}。请上传 .txt / .docx / .pdf 文件。")


def _parse_txt(content: bytes) -> str:
    """
    解析 TXT 文件，自动检测编码
    常见中文编码：UTF-8, GBK, GB2312, GB18030
    """
    # 按优先级尝试不同编码
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "utf-16", "latin-1"]

    for encoding in encodings:
        try:
            text = content.decode(encoding)
            # 简单验证：解码后的文本中应该包含常见中文字符或标点
            # 如果不包含且文件不小，可能是编码错误
            if len(text) > 100:
                return text
            # 短文件直接返回
            return text
        except (UnicodeDecodeError, UnicodeError):
            continue

    # 所有编码都失败，用 UTF-8 忽略错误字符
    return content.decode("utf-8", errors="ignore")


def _parse_docx(content: bytes) -> str:
    """
    解析 Word 文档（.docx 格式）
    提取所有段落的文本，用双换行分隔
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError("请安装 python-docx：pip install python-docx")

    doc = Document(io.BytesIO(content))
    paragraphs = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def _parse_pdf(content: bytes) -> str:
    """
    解析 PDF 文件
    逐页提取文本，用双换行分隔页面
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("请安装 pdfplumber：pip install pdfplumber")

    text_parts = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        total_pages = len(pdf.pages)

        # 最多处理 200 页（防止超大 PDF 导致内存溢出）
        max_pages = min(total_pages, 200)

        for i in range(max_pages):
            page = pdf.pages[i]
            page_text = page.extract_text()

            if page_text and page_text.strip():
                text_parts.append(page_text.strip())

        if total_pages > max_pages:
            text_parts.append(f"\n[注意：PDF 共 {total_pages} 页，仅提取了前 {max_pages} 页]")

    return "\n\n".join(text_parts)
