"""
游戏私聊AI助手 — 主入口
自动识别游戏私聊画面，用DeepSeek API以设定人设口吻回复。
"""
import sys
import os
import json
import logging
from src.ocr_engine import recognize_text
from src.ai_client import AIClient
from src.monitor import ScreenMonitor
from src.responder import paste_reply
from src.character_research import research_character
from src.settings_ui import SettingsApp, CONFIG_PATH

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "app.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("main")


class AppController:
    """主控制器，协调各模块"""

    def __init__(self):
        self.ai_client: AIClient = None
        self.monitor: ScreenMonitor = None
        self.ui: SettingsApp = None
        self._config: dict = {}

    def load_config(self) -> dict:
        """加载配置文件"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                return self._config
        except Exception as e:
            logger.warning(f"读取配置文件失败: {e}")
        return {}

    def apply_config(self, config: dict):
        """应用新配置（UI配置变更时调用）"""
        self._config = config

        # 重新初始化AI客户端
        api_key = config.get("deepseek_api_key", "")
        char = config.get("character", {})
        if api_key and char.get("name"):
            self.ai_client = AIClient(api_key)

            source_work = char.get("source_work", "")
            researched_style = ""

            # 如果填了出自作品，搜索角色语气
            if source_work:
                self.ui.log_from_thread(f"正在搜索《{source_work}》中 {char['name']} 的语气风格...")
                researched_style = research_character(api_key, char["name"], source_work)
                if researched_style:
                    self.ui.log_from_thread(f"角色语气研究完成（{len(researched_style)}字）")
                else:
                    self.ui.log_from_thread("角色搜索失败，使用基础人设")

            self.ai_client.set_persona(
                name=char.get("name", ""),
                personality=char.get("personality", ""),
                speaking_style=char.get("speaking_style", ""),
                source_work=source_work,
                researched_style=researched_style,
            )
            logger.info(f"人设已更新: {char.get('name')}")

        # 更新监控参数
        if self.monitor:
            region = config.get("monitor", {}).get("region", {})
            interval = config.get("monitor", {}).get("interval_seconds", 2)
            self.monitor.set_region(
                region.get("left", 100),
                region.get("top", 100),
                region.get("width", 400),
                region.get("height", 300),
            )
            self.monitor.set_interval(interval)

    def start_monitoring(self):
        """开始监控"""
        config = self.ui.get_config()
        if not config:
            logger.error("配置无效，无法启动")
            return

        # 确保配置已应用
        self.apply_config(config)

        if not self.ai_client:
            logger.error("AI客户端初始化失败，请检查API Key和人设")
            self.ui.set_monitoring_state(False)
            return

        # 创建监控器
        region = config.get("monitor", {}).get("region", {})
        interval = config.get("monitor", {}).get("interval_seconds", 2)

        self.monitor = ScreenMonitor({
            "left": region.get("left", 100),
            "top": region.get("top", 100),
            "width": region.get("width", 400),
            "height": region.get("height", 300),
        })
        self.monitor.set_interval(interval)

        # 设置新消息回调：收到回复后粘贴
        self.monitor.set_callback(lambda reply: paste_reply(reply, delay_before=0.5))

        # 启动监控线程
        self.monitor.start(
            ocr_func=recognize_text,
            ai_func=lambda msg: self.ai_client.chat(msg) if self.ai_client else None,
        )

        logger.info("监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        if self.monitor:
            self.monitor.stop()
            self.monitor = None

    def run(self):
        """启动应用"""
        # 预加载配置
        self.load_config()

        # 创建UI
        self.ui = SettingsApp(
            on_start=self.start_monitoring,
            on_stop=self.stop_monitoring,
            on_update_config=self.apply_config,
        )

        # 如果有已保存的API key和人设，预初始化AI客户端
        if self._config:
            self.apply_config(self._config)

        # 进入GUI主循环
        self.ui.run()


if __name__ == "__main__":
    app = AppController()
    app.run()
