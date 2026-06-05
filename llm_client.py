"""
LLM API 调用封装
支持 DeepSeek API（兼容 OpenAI SDK）
"""

from openai import OpenAI


def create_client(api_key: str) -> OpenAI:
    """
    创建 LLM 客户端实例

    Args:
        api_key: DeepSeek API Key（从 platform.deepseek.com 获取）

    Returns:
        OpenAI 客户端实例（已配置 DeepSeek base_url）
    """
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


def call_llm(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    timeout: float = 120.0,
) -> str:
    """
    调用 LLM，返回生成的文本

    Args:
        client: OpenAI 客户端实例
        system_prompt: 系统提示词（设定角色和行为）
        user_prompt: 用户提示词（具体任务）
        model: 模型名称，默认 deepseek-chat
        temperature: 创造性参数（0=保守，1=自由）
        max_tokens: 最大输出 token 数
        timeout: 超时秒数，默认 120 秒（防止无限等待）

    Returns:
        LLM 生成的文本内容
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    return response.choices[0].message.content


def test_api_key(api_key: str, timeout: float = 15.0) -> tuple:
    """
    验证 API Key 是否有效

    Args:
        api_key: DeepSeek API Key
        timeout: 超时秒数

    Returns:
        (是否有效, 信息)
    """
    try:
        client = create_client(api_key)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "你好，请回复'OK'。"}],
            max_tokens=5,
            timeout=timeout,
        )
        return True, "API Key 验证成功"
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return False, "API Key 无效（401 未授权），请检查 Key 是否正确"
        elif "403" in error_msg or "Forbidden" in error_msg:
            return False, "API Key 无权限（403），请检查账户状态"
        elif "429" in error_msg:
            return False, "请求过于频繁（429），请稍后再试"
        elif "timeout" in error_msg.lower():
            return False, "连接超时，请检查网络"
        else:
            return False, f"验证失败：{error_msg}"
