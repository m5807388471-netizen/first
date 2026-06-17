"""
DeepSeek API客户端 — 以设定人设口吻生成回复。
"""
import logging
import httpx
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


class AIClient:
    """DeepSeek API客户端，负责构建人设prompt并调用API生成回复。"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        # 对话历史（保留最近N轮，用于上下文连贯）
        self.history: List[Dict[str, str]] = []

    def set_persona(
        self,
        name: str,
        personality: str,
        speaking_style: str,
        source_work: str = "",
        researched_style: str = "",
    ):
        """设置角色人设，构建系统prompt。"""
        # 基础人设
        parts = []
        parts.append(f"你现在扮演一个名叫「{name}」的角色。")

        if source_work:
            parts.append(f"这个角色出自《{source_work}》。")

        if personality:
            parts.append(f"性格特点：{personality}")

        # 如果搜索到了角色的语气风格，优先使用
        if researched_style:
            parts.append(f"以下是你说话风格的详细描述，请严格遵循：\n{researched_style}")
        elif speaking_style:
            parts.append(f"说话风格：{speaking_style}")

        parts.append("")
        parts.append("规则：")
        parts.append("1. 始终保持角色，不要表现出你是AI")
        parts.append("2. 回复要简短自然，像真人聊天一样，不要长篇大论")
        parts.append("3. 只输出回复内容，不要加任何解释、前缀或后缀")
        parts.append("4. 如果消息是打招呼或闲聊，自然地回应")
        parts.append("5. 绝对不要提及你是AI、机器人或任何非人类身份")

        system_prompt = "\n".join(parts)
        # 重置历史，只保留新的系统设定
        self.history = [{"role": "system", "content": system_prompt}]

    def chat(self, message: str, max_context: int = 5) -> Optional[str]:
        """
        发送消息并获取AI回复。

        Args:
            message: 对方的私聊消息
            max_context: 最多保留多少轮历史对话

        Returns:
            AI的回复文本，失败返回None
        """
        if not self.api_key:
            logger.warning("API Key未设置，无法生成回复")
            return None

        # 添加用户消息
        self.history.append({"role": "user", "content": message})

        # 控制上下文长度：system prompt + 最近N轮对话（每轮2条）
        max_history = 1 + max_context * 2
        if len(self.history) > max_history:
            # 保留system prompt和最近的消息
            self.history = [self.history[0]] + self.history[-(max_history - 1):]

        try:
            response = httpx.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": self.history,
                    "temperature": 0.8,  # 稍高温度让回复更自然
                    "max_tokens": 200,   # 限制长度，模拟真人聊天
                    "stream": False,
                },
                timeout=15.0,
            )
            response.raise_for_status()

            data = response.json()
            reply = data["choices"][0]["message"]["content"].strip()

            # 将AI回复也加入历史
            self.history.append({"role": "assistant", "content": reply})

            logger.info(f"AI回复: {reply[:50]}...")
            return reply

        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API HTTP错误 [{e.response.status_code}]: {e.response.text[:200]}")
            return None
        except httpx.TimeoutException:
            logger.error("DeepSeek API请求超时")
            return None
        except Exception as e:
            logger.error(f"DeepSeek API调用异常: {e}")
            return None

    def reset_history(self):
        """重置对话历史（切换人设时调用）"""
        self.history = []
