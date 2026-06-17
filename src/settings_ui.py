"""
设置界面 — CustomTkinter GUI，用于配置API Key、人设、截图区域等。
"""
import json
import os
import logging
import threading
import customtkinter as ctk
from tkinter import messagebox

logger = logging.getLogger(__name__)

# CustomTkinter主题设置
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


class SettingsApp:
    """主设置窗口"""

    def __init__(self, on_start=None, on_stop=None, on_update_config=None):
        """
        Args:
            on_start: 开始监控的回调
            on_stop: 停止监控的回调
            on_update_config: 配置变更时回调（传入config dict）
        """
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_update_config = on_update_config
        self._monitoring = False
        self._log_buffer = []

        self.root = ctk.CTk()
        self.root.title("游戏私聊AI助手")
        self.root.geometry("520x720")
        self.root.resizable(False, False)

        self._build_ui()
        self._load_config()

    def _mk_entry(self, parent, textvariable, placeholder_text="", width=400, show="", **kwargs):
        """创建带剪贴板支持的输入框"""
        entry = ctk.CTkEntry(parent, textvariable=textvariable,
                             placeholder_text=placeholder_text, width=width, show=show, **kwargs)
        entry.bind("<Control-c>", lambda e: entry.event_generate("<<Copy>>"))
        entry.bind("<Control-v>", lambda e: entry.event_generate("<<Paste>>"))
        entry.bind("<Control-x>", lambda e: entry.event_generate("<<Cut>>"))
        entry.bind("<Control-a>", lambda e: (entry.select_range(0, "end"), "break"))
        return entry

    def _build_ui(self):
        """构建界面"""
        # === API Key 区域 ===
        api_frame = ctk.CTkFrame(self.root, border_width=1)
        api_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(api_frame, text="🔑 DeepSeek API Key",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))

        key_row = ctk.CTkFrame(api_frame, fg_color="transparent")
        key_row.pack(fill="x", padx=10, pady=5)

        self.api_key_var = ctk.StringVar()
        self.api_key_entry = self._mk_entry(key_row, textvariable=self.api_key_var,
                                            placeholder_text="sk-xxxxxxxxxxxxxxxx",
                                            show="*", width=350)
        self.api_key_entry.pack(side="left")

        self.show_key_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(key_row, text="显示", variable=self.show_key_var,
                        command=self._toggle_key_visibility,
                        width=50).pack(side="left", padx=5)

        # === 人设区域 ===
        persona_frame = ctk.CTkFrame(self.root, border_width=1)
        persona_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(persona_frame, text="🎭 角色人设",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(persona_frame, text="角色名称").pack(anchor="w", padx=10)
        self.char_name_var = ctk.StringVar()
        self._mk_entry(persona_frame, textvariable=self.char_name_var,
                      placeholder_text="例如：赫敏·格兰杰", width=400).pack(padx=10, pady=(0, 5))

        ctk.CTkLabel(persona_frame, text="出自作品（选填）").pack(anchor="w", padx=10)
        self.char_source_var = ctk.StringVar()
        self._mk_entry(persona_frame, textvariable=self.char_source_var,
                      placeholder_text="例如：哈利波特、原神、英雄联盟... 填入后自动搜索角色语气",
                      width=400).pack(padx=10, pady=(0, 5))

        ctk.CTkLabel(persona_frame, text="性格描述").pack(anchor="w", padx=10)
        self.char_personality_var = ctk.StringVar()
        self._mk_entry(persona_frame, textvariable=self.char_personality_var,
                      placeholder_text="例如：聪明、好学、有些急躁但心地善良",
                      width=400).pack(padx=10, pady=(0, 5))

        ctk.CTkLabel(persona_frame, text="说话风格").pack(anchor="w", padx=10)
        self.char_style_var = ctk.StringVar()
        self._mk_entry(persona_frame, textvariable=self.char_style_var,
                      placeholder_text="例如：偶尔引用书本知识，喜欢说'居然连这个都不知道'",
                      width=400).pack(padx=10, pady=(0, 10))

        # === 截图区域 ===
        region_frame = ctk.CTkFrame(self.root, border_width=1)
        region_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(region_frame, text="📸 截图区域（聊天框位置）",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))

        grid = ctk.CTkFrame(region_frame, fg_color="transparent")
        grid.pack(padx=10, pady=5)

        ctk.CTkLabel(grid, text="左边界:").grid(row=0, column=0, sticky="e", padx=2, pady=2)
        self.left_var = ctk.StringVar(value="100")
        self._mk_entry(grid, textvariable=self.left_var, width=70).grid(row=0, column=1, padx=2, pady=2)

        ctk.CTkLabel(grid, text="上边界:").grid(row=1, column=0, sticky="e", padx=2, pady=2)
        self.top_var = ctk.StringVar(value="100")
        self._mk_entry(grid, textvariable=self.top_var, width=70).grid(row=1, column=1, padx=2, pady=2)

        ctk.CTkLabel(grid, text="宽度:").grid(row=0, column=2, sticky="e", padx=2, pady=2)
        self.width_var = ctk.StringVar(value="400")
        self._mk_entry(grid, textvariable=self.width_var, width=70).grid(row=0, column=3, padx=2, pady=2)

        ctk.CTkLabel(grid, text="高度:").grid(row=1, column=2, sticky="e", padx=2, pady=2)
        self.height_var = ctk.StringVar(value="300")
        self._mk_entry(grid, textvariable=self.height_var, width=70).grid(row=1, column=3, padx=2, pady=2)

        ctk.CTkLabel(region_frame,
                     text="💡 将游戏窗口化，用鼠标悬停在聊天区域左上角和右下角查看坐标（可用截图工具辅助）",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=10, pady=(0, 5))

        # === 监控设置 ===
        monitor_frame = ctk.CTkFrame(self.root, border_width=1)
        monitor_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(monitor_frame, text="⚙️ 监控设置",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))

        interval_row = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        interval_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(interval_row, text="检测间隔(秒):").pack(side="left")
        self.interval_var = ctk.StringVar(value="2")
        self._mk_entry(interval_row, textvariable=self.interval_var, width=60).pack(side="left", padx=5)

        # 鼠标追踪开关
        track_row = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        track_row.pack(fill="x", padx=10, pady=(0, 5))
        self.mouse_track_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(track_row, text="鼠标追踪模式（虚线框跟随鼠标，截图以鼠标为中心）",
                        variable=self.mouse_track_var,
                        command=self._on_mouse_track_toggle,
                        width=50).pack(side="left")

        # === 控制按钮 ===
        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn = ctk.CTkButton(btn_frame, text="▶ 开始监控",
                                        command=self._toggle_monitoring,
                                        fg_color="#2e7d32", hover_color="#388e3c",
                                        width=150, height=40)
        self.start_btn.pack(side="left", padx=5)

        self.save_btn = ctk.CTkButton(btn_frame, text="💾 保存设置",
                                       command=self._save_config,
                                       width=120, height=40)
        self.save_btn.pack(side="left", padx=5)

        self.status_var = ctk.StringVar(value="⏸ 已停止")
        ctk.CTkLabel(btn_frame, textvariable=self.status_var,
                     font=ctk.CTkFont(size=13)).pack(side="right", padx=10)

        # === 日志区域 ===
        log_frame = ctk.CTkFrame(self.root, border_width=1)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        ctk.CTkLabel(log_frame, text="📋 运行日志",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(5, 0))

        self.log_text = ctk.CTkTextbox(log_frame, width=460, height=150,
                                        font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

    def _on_mouse_track_toggle(self):
        """鼠标追踪开关切换"""
        pass  # 不需要额外逻辑，get_config/save_config 会读取状态

    def _toggle_key_visibility(self):
        """切换API Key显示/隐藏"""
        if self.show_key_var.get():
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="*")

    def _toggle_monitoring(self):
        """开始/停止监控"""
        if not self._monitoring:
            # 验证配置
            if not self.api_key_var.get().strip():
                messagebox.showerror("错误", "请先填入 DeepSeek API Key")
                return
            if not self.char_name_var.get().strip():
                messagebox.showerror("错误", "请先设置角色名称")
                return

            self._monitoring = True
            self.start_btn.configure(text="⏹ 停止监控", fg_color="#c62828", hover_color="#d32f2f")
            self.status_var.set("▶ 监控中...")

            # 保存配置并通知外部
            self._save_config(silent=True)
            if self._on_start:
                self._on_start()

            self._log("监控已启动")
        else:
            self._monitoring = False
            self.start_btn.configure(text="▶ 开始监控", fg_color="#2e7d32", hover_color="#388e3c")
            self.status_var.set("⏸ 已停止")

            if self._on_stop:
                self._on_stop()

            self._log("监控已停止")

    # --- 配置读写 ---

    def _load_config(self):
        """从config.json加载设置"""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)

                self.api_key_var.set(cfg.get("deepseek_api_key", ""))

                char = cfg.get("character", {})
                self.char_name_var.set(char.get("name", ""))
                self.char_source_var.set(char.get("source_work", ""))
                self.char_personality_var.set(char.get("personality", ""))
                self.char_style_var.set(char.get("speaking_style", ""))

                region = cfg.get("monitor", {}).get("region", {})
                self.left_var.set(str(region.get("left", 100)))
                self.top_var.set(str(region.get("top", 100)))
                self.width_var.set(str(region.get("width", 400)))
                self.height_var.set(str(region.get("height", 300)))

                self.interval_var.set(str(cfg.get("monitor", {}).get("interval_seconds", 2)))
                self.mouse_track_var.set(cfg.get("monitor", {}).get("mouse_tracking", False))

                self._log("配置已加载")
        except Exception as e:
            logger.warning(f"加载配置失败: {e}")

    def _save_config(self, silent=False):
        """保存设置到config.json"""
        try:
            cfg = {
                "deepseek_api_key": self.api_key_var.get().strip(),
                "character": {
                    "name": self.char_name_var.get().strip(),
                    "source_work": self.char_source_var.get().strip(),
                    "personality": self.char_personality_var.get().strip(),
                    "speaking_style": self.char_style_var.get().strip(),
                },
                "monitor": {
                    "region": {
                        "left": int(self.left_var.get() or 0),
                        "top": int(self.top_var.get() or 0),
                        "width": int(self.width_var.get() or 400),
                        "height": int(self.height_var.get() or 300),
                    },
                    "interval_seconds": float(self.interval_var.get() or 2),
                    "mouse_tracking": self.mouse_track_var.get(),
                },
            }
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)

            if self._on_update_config:
                self._on_update_config(cfg)

            if not silent:
                self._log("设置已保存")

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            if not silent:
                messagebox.showerror("错误", f"保存失败: {e}")

    def _log(self, msg: str):
        """添加日志到界面"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        self._log_buffer.append(line)
        # 限制缓冲区
        if len(self._log_buffer) > 500:
            self._log_buffer = self._log_buffer[-200:]
        self.log_text.insert("end", line)
        self.log_text.see("end")

    # --- 公开方法 ---

    def run(self):
        """启动GUI主循环"""
        self.root.mainloop()

    def get_config(self) -> dict:
        """获取当前界面配置"""
        try:
            return {
                "deepseek_api_key": self.api_key_var.get().strip(),
                "character": {
                    "name": self.char_name_var.get().strip(),
                    "source_work": self.char_source_var.get().strip(),
                    "personality": self.char_personality_var.get().strip(),
                    "speaking_style": self.char_style_var.get().strip(),
                },
                "monitor": {
                    "region": {
                        "left": int(self.left_var.get() or 0),
                        "top": int(self.top_var.get() or 0),
                        "width": int(self.width_var.get() or 400),
                        "height": int(self.height_var.get() or 300),
                    },
                    "interval_seconds": float(self.interval_var.get() or 2),
                    "mouse_tracking": self.mouse_track_var.get(),
                },
            }
        except (ValueError, TypeError):
            return {}

    def log_from_thread(self, msg: str):
        """从其他线程安全地添加日志"""
        self.root.after(0, lambda: self._log(msg))

    def set_monitoring_state(self, active: bool):
        """从外部设置监控状态"""
        self.root.after(0, lambda: self._set_state_ui(active))

    def _set_state_ui(self, active: bool):
        self._monitoring = active
        if active:
            self.start_btn.configure(text="⏹ 停止监控", fg_color="#c62828", hover_color="#d32f2f")
            self.status_var.set("▶ 监控中...")
        else:
            self.start_btn.configure(text="▶ 开始监控", fg_color="#2e7d32", hover_color="#388e3c")
            self.status_var.set("⏸ 已停止")
