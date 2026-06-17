"""
角色搜索模块 — 当用户填写了"出自作品"时，通过DeepSeek搜索角色信息并分析其语气风格。
"""
import logging
import httpx

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def research_character(api_key: str, name: str, source_work: str) -> str:
    """
    搜索角色信息，分析其说话风格和语气特点。

    Args:
        api_key: DeepSeek API Key
        name: 角色名称
        source_work: 出自作品（如"哈利波特"）

    Returns:
        角色的语气风格描述文本，可直接用于人设prompt。
        搜索失败返回空字符串，不影响程序继续运行。
    """
    if not api_key or not name or not source_work:
        return ""

    prompt = (
        f"请详细分析《{source_work}》中「{name}」这个角色的说话风格。\n\n"
        f"请从以下方面回答：\n"
        f"1. 惯用的口头禅和语气词\n"
        f"2. 说话时常用的句式结构（简短/长句、命令式/疑问式等）\n"
        f"3. 标志性的语言习惯（如引用名言、使用特定比喻等）\n"
        f"4. 情绪表达方式（兴奋时说什幺、生气时说什幺、害羞时说什幺）\n\n"
        f"请尽可能具体，给出典型对话例句。用中文回答，控制在300字以内。"
    )

    try:
        logger.info(f"正在搜索角色信息: 《{source_work}》的 {name}")
        response = httpx.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.5,
                "max_tokens": 500,
                "stream": False,
            },
            timeout=20.0,
        )
        response.raise_for_status()

        data = response.json()
        result = data["choices"][0]["message"]["content"].strip()
        logger.info(f"角色研究完成，获取到 {len(result)} 字")
        return result

    except httpx.HTTPStatusError as e:
        logger.warning(f"角色搜索HTTP错误 [{e.response.status_code}]: {e.response.text[:150]}")
        return ""
    except httpx.TimeoutException:
        logger.warning("角色搜索超时，将使用基础人设")
        return ""
    except Exception as e:
        logger.warning(f"角色搜索异常: {e}")
        return ""
