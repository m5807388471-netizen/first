"""
回复模块 — 将AI生成的文本复制到剪贴板，并模拟Ctrl+V粘贴到游戏窗口。
"""
import time
import logging
import pyperclip
import pyautogui

logger = logging.getLogger(__name__)

# 安全设置：pyautogui的安全失败机制
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # 每个操作间暂停0.1秒


def paste_reply(text: str, delay_before: float = 0.5, delay_after: float = 0.2,
                click_to_focus: bool = True):
    """
    将文本复制到剪贴板，然后模拟Ctrl+V粘贴。

    Args:
        text: 要粘贴的回复内容
        delay_before: 粘贴前等待时间（秒）
        delay_after: 粘贴后等待时间
        click_to_focus: 是否先点击鼠标当前位置以聚焦窗口
    """
    if not text:
        logger.warning("回复内容为空，跳过粘贴")
        return False

    try:
        # 1. 复制到剪贴板
        pyperclip.copy(text)
        logger.info(f"已复制到剪贴板: {text[:50]}...")

        # 2. 点击当前鼠标位置聚焦窗口（鼠标追踪模式下鼠标在聊天框上）
        if click_to_focus:
            time.sleep(0.15)
            pyautogui.click()
            logger.info("已点击聚焦窗口")
            time.sleep(0.15)

        # 3. 等待
        time.sleep(delay_before)

        # 4. 模拟Ctrl+V
        pyautogui.hotkey('ctrl', 'v')
        logger.info("已执行Ctrl+V粘贴")

        time.sleep(delay_after)
        return True

    except Exception as e:
        logger.error(f"粘贴操作失败: {e}")
        return False


def copy_only(text: str) -> bool:
    """
    仅复制到剪贴板，不执行粘贴。
    适合不希望自动按键的用户。

    Args:
        text: 回复内容

    Returns:
        是否成功
    """
    if not text:
        return False
    try:
        pyperclip.copy(text)
        logger.info(f"已复制到剪贴板（手动粘贴模式）: {text[:50]}...")
        return True
    except Exception as e:
        logger.error(f"复制失败: {e}")
        return False
