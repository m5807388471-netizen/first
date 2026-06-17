"""
OCR引擎 — 使用EasyOCR识别截图中的中文文字。
首次加载会自动下载模型，请保持网络畅通。
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 全局单例，避免重复加载模型
_ocr_reader: Optional[object] = None


def get_reader():
    """获取EasyOCR Reader实例（懒加载单例）"""
    global _ocr_reader
    if _ocr_reader is None:
        logger.info("正在加载EasyOCR中文模型（首次较慢，约30秒-1分钟）...")
        try:
            import easyocr
            # ['ch_sim', 'en'] = 简体中文 + 英文
            # gpu=False 使用CPU（兼容性最好）
            _ocr_reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
            logger.info("EasyOCR模型加载完成")
        except ImportError:
            logger.error("EasyOCR未安装，请运行: pip install easyocr")
            raise
    return _ocr_reader


def recognize_text(image) -> str:
    """
    从图片中识别文字，返回合并后的文本字符串。

    Args:
        image: numpy数组(BGR格式) 或 PIL Image

    Returns:
        识别出的文字，多行用换行符分隔。识别失败返回空字符串。
    """
    if image is None:
        return ""

    try:
        reader = get_reader()

        # 转换为RGB numpy数组（EasyOCR需要RGB）
        import numpy as np
        if hasattr(image, 'convert'):
            image = np.array(image.convert('RGB'))
        elif len(image.shape) == 3 and image.shape[2] == 3:
            # 假设是BGR，转RGB
            image = image[:, :, ::-1]

        results = reader.readtext(image)

        if not results:
            return ""

        # 提取文字，过滤低置信度
        lines = []
        for bbox, text, confidence in results:
            if confidence > 0.4:
                lines.append(text)

        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"OCR识别出错: {e}")
        return ""


def extract_latest_message(current_text: str, previous_text: str) -> Optional[str]:
    """
    对比当前和上次的OCR结果，提取新增的消息。

    Args:
        current_text: 当前截图识别出的全部文字
        previous_text: 上次截图识别出的全部文字

    Returns:
        新增的消息文本。如果没有新消息返回None。
    """
    if not current_text:
        return None
    if not previous_text:
        # 首次截图，全部作为"已有"消息，不触发回复
        return None

    # 简单策略：当前文本包含上次文本，则新增部分是current减去previous
    if previous_text in current_text:
        new_part = current_text[len(previous_text):].strip()
        return new_part if new_part else None

    # 如果当前文本和上次差异较大（比如滑动或刷新），取当前最新一行
    current_lines = current_text.strip().split("\n")
    previous_lines = previous_text.strip().split("\n")

    if len(current_lines) > len(previous_lines):
        new_lines = current_lines[len(previous_lines):]
        return "\n".join(new_lines)

    return None
