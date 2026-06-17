"""
OCR引擎 — 使用PaddleOCR识别截图中的中文文字。
PaddleOCR首次加载会下载模型，请保持网络畅通。
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 全局单例，避免重复加载模型
_ocr_instance: Optional[object] = None


def get_ocr():
    """获取OCR实例（懒加载单例）"""
    global _ocr_instance
    if _ocr_instance is None:
        logger.info("正在加载PaddleOCR模型（首次可能较慢，请耐心等待）...")
        try:
            from paddleocr import PaddleOCR
            # cls=True 开启方向分类，处理竖排/倒置文字
            # lang='ch' 中文模型
            _ocr_instance = PaddleOCR(lang='ch', use_angle_cls=True, show_log=False)
            logger.info("PaddleOCR模型加载完成")
        except ImportError:
            logger.error("PaddleOCR未安装，请运行: pip install paddleocr paddlepaddle")
            raise
    return _ocr_instance


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
        ocr = get_ocr()
        # 转换为numpy数组（如果是PIL Image）
        import numpy as np
        if hasattr(image, 'convert'):
            # PIL Image → numpy
            image = np.array(image.convert('RGB'))
            # RGB → BGR (PaddleOCR期望BGR)
            image = image[:, :, ::-1]

        results = ocr.ocr(image, cls=True)

        if not results or not results[0]:
            return ""

        # 提取所有识别到的文字，按行拼接
        lines = []
        for line_info in results[0]:
            if line_info and len(line_info) >= 2:
                text = line_info[1][0]  # line_info[1][0] 是文字内容
                confidence = line_info[1][1]  # line_info[1][1] 是置信度
                if confidence > 0.5:  # 过滤低置信度结果
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
