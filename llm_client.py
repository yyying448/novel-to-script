"""
LLM 多模型适配层

支持 5 个厂商 + 自定义 OpenAI 兼容接口：
- DeepSeek（默认，性价比高，中文强）
- OpenAI（GPT-4o，结构化输出最强）
- 智谱 GLM（国内，中文优化）
- 月之暗面 Kimi（超长上下文）
- 通义千问（阿里，中文强）
- 自定义（任意 OpenAI 兼容 API）

用户切换模型无需改代码，前端选择即可。
"""

from openai import OpenAI
from typing import Tuple, Optional

# ================================================================
# 厂商注册表（新增厂商只需加一条）
# ================================================================

PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
        "help": "platform.deepseek.com",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "help": "platform.openai.com",
    },
    "zhipu": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
        "help": "open.bigmodel.cn",
    },
    "moonshot": {
        "name": "月之暗面 Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
        "help": "platform.moonshot.cn",
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "help": "dashscope.aliyun.com",
    },
    "custom": {
        "name": "自定义",
        "base_url": "",
        "model": "",
        "help": "输入兼容 OpenAI 接口的地址",
    },
}


def get_provider_list() -> list:
    """返回厂商列表供前端渲染"""
    return [
        {"key": k, "name": v["name"], "model": v["model"], "help": v["help"]}
        for k, v in PROVIDERS.items()
    ]


def get_default_model(provider: str) -> str:
    """获取厂商默认模型名"""
    cfg = PROVIDERS.get(provider, PROVIDERS["deepseek"])
    return cfg["model"]


# ================================================================
# 客户端工厂
# ================================================================

def create_client(
    api_key: str,
    provider: str = "deepseek",
    base_url: Optional[str] = None,
) -> OpenAI:
    """
    创建 LLM 客户端

    Args:
        api_key: API Key
        provider: 厂商标识（deepseek/openai/zhipu/moonshot/qwen/custom）
        base_url: 自定义接口地址（provider=custom 时必填）

    Returns:
        OpenAI 兼容客户端实例
    """
    if provider not in PROVIDERS:
        raise ValueError(f"不支持的厂商：{provider}。可选：{list(PROVIDERS.keys())}")

    cfg = PROVIDERS[provider]
    url = base_url or cfg["base_url"]

    if not url:
        raise ValueError("自定义厂商需要提供 base_url")

    return OpenAI(api_key=api_key, base_url=url)


# ================================================================
# LLM 调用
# ================================================================

def call_llm(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    timeout: float = 120.0,
) -> str:
    """
    调用 LLM，返回生成的文本

    Args:
        client: OpenAI 兼容客户端实例
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        model: 模型名称（None 则用厂商默认）
        temperature: 创造性参数
        max_tokens: 最大输出 token 数
        timeout: 超时秒数

    Returns:
        LLM 生成的文本内容
    """
    response = client.chat.completions.create(
        model=model or "deepseek-v4-pro",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    return response.choices[0].message.content


# ================================================================
# Key 验证（兼容多厂商）
# ================================================================

def test_api_key(
    api_key: str,
    provider: str = "deepseek",
    base_url: Optional[str] = None,
    timeout: float = 15.0,
) -> Tuple[bool, str]:
    """
    验证 API Key 是否有效（跨厂商）

    Returns:
        (是否有效, 消息)
    """
    try:
        client = create_client(api_key, provider, base_url)
        model = get_default_model(provider) or "deepseek-v4-pro"
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "回复OK"}],
            max_tokens=5,
            timeout=timeout,
        )
        name = PROVIDERS.get(provider, {}).get("name", provider)
        return True, f"{name} 连接成功"
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return False, "API Key 无效（401），请检查"
        elif "403" in error_msg or "Forbidden" in error_msg:
            return False, "API Key 无权限（403）"
        elif "429" in error_msg:
            return False, "请求频繁（429），请稍后重试"
        elif "Arrearage" in error_msg or "overdue" in error_msg.lower():
            return False, "账户欠费，请登录厂商平台充值"
        elif "timeout" in error_msg.lower() or "connect" in error_msg.lower():
            return False, "网络连接失败，请检查 API 地址或网络"
        else:
            return False, f"验证失败：{error_msg}"
