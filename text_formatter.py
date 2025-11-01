import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import re
import os
import json
import tempfile
import threading
import requests
import random
import string
import time

# 尝试导入pydub，用于音频拼接
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

class TextFormatter:
    def __init__(self, root):
        self.root = root
        self.root.title("文本格式化工具")
        self.root.geometry("1200x700")
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        # 数字转英文的映射
        self.number_words = {
            0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
            6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
            11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
            16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
            20: "twenty", 30: "thirty", 40: "forty", 50: "fifty",
            60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety"
        }
        
        # 初始化模型变量字典（在setup_ui之前初始化）
        self.tts_vars = {}  # 格式: {"f5tts": {...}, "e2tts": {...}}
        self.current_tts_model = "f5tts"  # 默认选中F5-TTS
        
        self.setup_ui()
        self.load_config()
        
        # 绑定变量变化事件以自动保存配置
        self.setup_auto_save()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)  # 左列
        main_frame.columnconfigure(2, weight=1)  # 右列
        main_frame.rowconfigure(1, weight=1)     # 文本框行
        
        # 输入标签
        input_label = ttk.Label(main_frame, text="输入文本:", font=("Arial", 12, "bold"))
        input_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 预览标签
        preview_label = ttk.Label(main_frame, text="预览结果:", font=("Arial", 12, "bold"))
        preview_label.grid(row=0, column=2, sticky=tk.W, pady=(0, 5))
        
        # 输入文本框
        self.input_text = scrolledtext.ScrolledText(main_frame, height=15, wrap=tk.WORD, font=("Arial", 10))
        self.input_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        self.input_text.bind('<KeyRelease>', self.on_text_change)
        
        # 中间按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=1, sticky=(tk.N, tk.S), padx=10)
        
        # 按钮垂直排列
        self.process_btn = ttk.Button(button_frame, text="处理文本", command=self.process_text, width=12)
        self.process_btn.pack(pady=(0, 10))
        
        self.export_btn = ttk.Button(button_frame, text="导出", command=self.export_text, width=12)
        self.export_btn.pack(pady=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="清空", command=self.clear_text, width=12)
        self.clear_btn.pack()
        
        # 预览文本框
        self.preview_text = scrolledtext.ScrolledText(main_frame, height=15, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10))
        self.preview_text.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ========== 配音区域（标签页）==========
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky=(tk.E, tk.W), pady=(12, 8))
        
        # 创建标签页容器
        tts_notebook = ttk.Notebook(main_frame)
        tts_notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=0, pady=(0, 4))
        
        # 创建E2TTS标签页（放在前面）
        e2tts_frame = ttk.Frame(tts_notebook, padding="8")
        tts_notebook.add(e2tts_frame, text="E2TTS")
        
        # 创建F5-TTS标签页
        f5tts_frame = ttk.Frame(tts_notebook, padding="8")
        tts_notebook.add(f5tts_frame, text="F5-TTS")
        
        # 为每个标签页构建UI（使用通用函数）
        self._build_tts_tab(e2tts_frame, "e2tts")
        self._build_tts_tab(f5tts_frame, "f5tts")
        
        # 保存当前选中的标签页（已在 __init__ 中初始化，这里只需要绑定事件）
        def on_tab_changed(event):
            selected = tts_notebook.index(tts_notebook.select())
            self.current_tts_model = "e2tts" if selected == 0 else "f5tts"
            self.log(f"[TTS] 切换到模型: {self.current_tts_model.upper()}")
        tts_notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
        
        # 默认选中第一个标签页（E2TTS）
        tts_notebook.select(0)
        self.current_tts_model = "e2tts"
        
        # 为了向后兼容，将F5-TTS的变量作为默认变量（供其他地方引用）
        # 这样原有的代码可以继续工作，同时新代码可以使用模型特定的变量
        # 注意：变量访问将通过属性方法动态获取当前模型的变量
        # 注意：self.tts_vars 已在 __init__ 中初始化

        # ========== 底部日志 ==========
        log_frame = ttk.LabelFrame(main_frame, text="日志")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(6, 0))
        main_frame.rowconfigure(4, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def on_text_change(self, event=None):
        # 实时预览功能
        self.process_text()
        
    def number_to_words(self, num):
        """将数字转换为英文单词"""
        if num in self.number_words:
            return self.number_words[num]
        
        if num < 100:
            tens = (num // 10) * 10
            ones = num % 10
            if ones == 0:
                return self.number_words[tens]
            else:
                return f"{self.number_words[tens]}-{self.number_words[ones]}"
        
        elif num < 1000:
            hundreds = num // 100
            remainder = num % 100
            if remainder == 0:
                return f"{self.number_words[hundreds]} hundred"
            else:
                return f"{self.number_words[hundreds]} hundred {self.number_to_words(remainder)}"
        
        elif num < 1000000:
            thousands = num // 1000
            remainder = num % 1000
            if remainder == 0:
                return f"{self.number_to_words(thousands)} thousand"
            else:
                return f"{self.number_to_words(thousands)} thousand {self.number_to_words(remainder)}"
        
        else:
            # 对于更大的数字，简化处理
            return str(num)
    
    def is_year(self, num):
        """判断是否为年份（1900-2099）"""
        return 1900 <= num <= 2099
    
    def process_text(self):
        """处理文本，将数字转换为英文"""
        input_content = self.input_text.get("1.0", tk.END).strip()
        if not input_content:
            self.update_preview("")
            return
        
        # 查找所有数字
        def replace_number(match):
            num_str = match.group(1)  # 获取数字部分
            suffix = match.group(2)   # 获取后缀部分
            num = int(num_str)
            
            # 如果是四位数，按照年份格式处理
            if 1000 <= num <= 9999:
                if num < 2000:
                    year_part1 = num // 100
                    year_part2 = num % 100
                    result = f"{self.number_to_words(year_part1)} {self.number_to_words(year_part2)}"
                else:
                    year_part1 = num // 100
                    year_part2 = num % 100
                    if year_part2 == 0:
                        result = f"two thousand"
                    else:
                        result = f"two thousand {self.number_to_words(year_part2)}"
            else:
                # 其他数字直接转换
                result = self.number_to_words(num)
            
            return result + suffix
        
        # 使用正则表达式替换数字
        # 匹配1位以上的数字，包括可能的后缀（如s, th, st, nd, rd等）
        processed_text = re.sub(r'\b(\d+)([a-zA-Z]*)\b', replace_number, input_content)
        
        self.update_preview(processed_text)
    
    def update_preview(self, text):
        """更新预览框"""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", text)
        self.preview_text.config(state=tk.DISABLED)
    
    def export_text(self):
        """导出处理后的文本"""
        processed_text = self.preview_text.get("1.0", tk.END).strip()
        if not processed_text:
            messagebox.showwarning("警告", "没有可导出的内容！")
            return
        
        # 弹出保存对话框
        file_path = filedialog.asksaveasfilename(
            title="保存文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(processed_text)
                messagebox.showinfo("成功", f"文件已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件时出错: {str(e)}")
    
    def clear_text(self):
        """清空所有文本"""
        self.input_text.delete("1.0", tk.END)
        self.update_preview("")

    # ========== 日志 ==========
    def log(self, msg: str):
        def _append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def _build_tts_tab(self, parent_frame, model_name):
        """
        为给定的标签页框架构建TTS UI
        model_name: "f5tts" 或 "e2tts"
        """
        # 配置列权重
        for i in range(6):
            parent_frame.columnconfigure(i, weight=1)
        
        # 存储该模型的所有变量
        model_vars = {}
        
        # 服务器地址
        ttk.Label(parent_frame, text="服务地址:").grid(row=0, column=0, sticky=tk.W, padx=(8, 6), pady=(8, 4))
        server_var = tk.StringVar(value="http://127.0.0.1:7860")
        server_entry = ttk.Entry(parent_frame, textvariable=server_var)
        server_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 8), pady=(8, 4))
        model_vars['server_var'] = server_var
        
        # 参考音频
        ttk.Label(parent_frame, text="参考音频:").grid(row=1, column=0, sticky=tk.W, padx=(8, 6))
        ref_audio_var = tk.StringVar()
        ref_audio_entry = ttk.Entry(parent_frame, textvariable=ref_audio_var)
        ref_audio_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 8))
        
        def browse_ref_audio():
            file_path = filedialog.askopenfilename(title="选择参考音频", filetypes=[("音频文件", "*.wav;*.mp3;*.flac;*.m4a;*.ogg"), ("所有文件", "*.*")])
            if file_path:
                ref_audio_var.set(file_path)
                filename = os.path.splitext(os.path.basename(file_path))[0]
                ref_text_var.set(filename)
                self.log(f"[{model_name.upper()}] 已选择参考音频: {file_path}, 参考文本已自动设置为文件名: {filename}")
        
        ttk.Button(parent_frame, text="选择...", command=browse_ref_audio, width=10).grid(row=1, column=3, sticky=tk.W, padx=(0, 8))
        model_vars['ref_audio_var'] = ref_audio_var
        
        # 参考文本
        ttk.Label(parent_frame, text="参考文本:").grid(row=2, column=0, sticky=tk.W, padx=(8, 6), pady=(6, 0))
        ref_text_var = tk.StringVar()
        ref_text_entry = ttk.Entry(parent_frame, textvariable=ref_text_var)
        ref_text_entry.grid(row=2, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=(0, 8), pady=(6, 0))
        model_vars['ref_text_var'] = ref_text_var
        
        # 生成文本
        ttk.Label(parent_frame, text="生成文本:").grid(row=3, column=0, sticky=tk.NW, padx=(8, 6), pady=(6, 6))
        gen_text = scrolledtext.ScrolledText(parent_frame, height=4, wrap=tk.WORD)
        gen_text.grid(row=3, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=(0, 8), pady=(6, 6))
        
        def use_preview_text():
            text = self.preview_text.get("1.0", tk.END).strip()
            if not text:
                text = self.input_text.get("1.0", tk.END).strip()
            gen_text.delete("1.0", tk.END)
            gen_text.insert("1.0", text)
            if not self._loading_config:
                self.save_config()
        
        ttk.Button(parent_frame, text="使用预览文本", command=use_preview_text).grid(row=3, column=4, sticky=tk.NE, padx=(0, 8), pady=(6, 6))
        model_vars['gen_text'] = gen_text
        
        # 高级设置参数
        adv_frame = ttk.LabelFrame(parent_frame, text="高级设置")
        adv_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E), padx=8, pady=(6, 6))
        for i in range(4):
            adv_frame.columnconfigure(i, weight=1)
        
        # 随机种子
        randomize_seed_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(adv_frame, text="随机种子", variable=randomize_seed_var).grid(row=0, column=0, sticky=tk.W, padx=(8, 4))
        ttk.Label(adv_frame, text="种子:").grid(row=0, column=1, sticky=tk.W, padx=(8, 4))
        default_seed = random.randint(1000000000, 9999999999)
        seed_var = tk.IntVar(value=default_seed)
        seed_entry = ttk.Entry(adv_frame, textvariable=seed_var, width=10)
        seed_entry.grid(row=0, column=2, sticky=tk.W, padx=(0, 8))
        
        def validate_seed(*args):
            try:
                seed_val = seed_var.get()
                if seed_val < 0:
                    seed_var.set(0)
                elif seed_val > 9999999999:
                    seed_var.set(9999999999)
            except (ValueError, TypeError):
                seed_var.set(0)
        
        seed_var.trace('w', validate_seed)
        model_vars['randomize_seed_var'] = randomize_seed_var
        model_vars['seed_var'] = seed_var
        
        # 移除静音
        remove_silences_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv_frame, text="移除静音", variable=remove_silences_var).grid(row=0, column=3, sticky=tk.W, padx=(8, 8))
        model_vars['remove_silences_var'] = remove_silences_var
        
        # 播放速度
        ttk.Label(adv_frame, text="播放速度:").grid(row=1, column=0, sticky=tk.W, padx=(8, 4), pady=(6, 0))
        speed_var = tk.DoubleVar(value=1.0)
        speed_val_label = ttk.Label(adv_frame, text="1.0", width=6)
        speed_val_label.grid(row=1, column=2, sticky=tk.W, padx=(0, 8), pady=(6, 0))
        
        speed_scale = ttk.Scale(adv_frame, from_=0.1, to=2.0, variable=speed_var, orient=tk.HORIZONTAL)
        speed_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(8, 4), pady=(6, 0))
        
        speed_save_timer = None
        def update_speed_display_and_save(*args):
            val = speed_var.get()
            snapped = round(val / 0.1) * 0.1
            if snapped < 0.1:
                snapped = 0.1
            elif snapped > 2.0:
                snapped = 2.0
            speed_val_label.config(text=f"{snapped:.1f}")
            if not self._loading_config:
                nonlocal speed_save_timer
                if speed_save_timer:
                    self.root.after_cancel(speed_save_timer)
                speed_save_timer = self.root.after(500, self.save_config)
        
        speed_var.trace('w', update_speed_display_and_save)
        model_vars['speed_var'] = speed_var
        
        # NFE Steps
        ttk.Label(adv_frame, text="NFE步数:").grid(row=2, column=0, sticky=tk.W, padx=(8, 4), pady=(6, 0))
        nfe_steps_var = tk.IntVar(value=32)
        nfe_scale = ttk.Scale(adv_frame, from_=4, to=64, variable=nfe_steps_var, orient=tk.HORIZONTAL)
        nfe_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(8, 4), pady=(6, 0))
        nfe_val_label = ttk.Label(adv_frame, textvariable=nfe_steps_var, width=6)
        nfe_val_label.grid(row=2, column=2, sticky=tk.W, padx=(0, 8), pady=(6, 0))
        
        nfe_save_timer = None
        def update_nfe_display_and_save(*args):
            nfe_val_label.config(text=str(int(nfe_steps_var.get())))
            if not self._loading_config:
                nonlocal nfe_save_timer
                if nfe_save_timer:
                    self.root.after_cancel(nfe_save_timer)
                nfe_save_timer = self.root.after(500, self.save_config)
        
        nfe_steps_var.trace('w', update_nfe_display_and_save)
        model_vars['nfe_steps_var'] = nfe_steps_var
        
        # 交叉淡入淡出
        ttk.Label(adv_frame, text="交叉淡入淡出:").grid(row=3, column=0, sticky=tk.W, padx=(8, 4), pady=(6, 6))
        crossfade_var = tk.DoubleVar(value=0.15)
        crossfade_scale = ttk.Scale(adv_frame, from_=0.0, to=1.0, variable=crossfade_var, orient=tk.HORIZONTAL)
        crossfade_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(8, 4), pady=(6, 6))
        crossfade_val_label = ttk.Label(adv_frame, text="0.15", width=6)
        crossfade_val_label.grid(row=3, column=2, sticky=tk.W, padx=(0, 8), pady=(6, 6))
        
        crossfade_save_timer = None
        def update_crossfade_display_and_save(*args):
            crossfade_val_label.config(text=f"{crossfade_var.get():.2f}")
            if not self._loading_config:
                nonlocal crossfade_save_timer
                if crossfade_save_timer:
                    self.root.after_cancel(crossfade_save_timer)
                crossfade_save_timer = self.root.after(500, self.save_config)
        
        crossfade_var.trace('w', update_crossfade_display_and_save)
        model_vars['crossfade_var'] = crossfade_var
        
        # 自动保存目录选项
        ttk.Label(adv_frame, text="自动保存目录:").grid(row=4, column=0, sticky=tk.W, padx=(8, 4), pady=(6, 6))
        auto_save_dir_var = tk.StringVar(value="")
        auto_save_dir_entry = ttk.Entry(adv_frame, textvariable=auto_save_dir_var, width=40)
        auto_save_dir_entry.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(8, 4), pady=(6, 6))
        
        def browse_auto_save_dir():
            dir_path = filedialog.askdirectory(title="选择自动保存目录")
            if dir_path:
                auto_save_dir_var.set(dir_path)
                if not self._loading_config:
                    self.save_config()
        
        ttk.Button(adv_frame, text="选择...", command=browse_auto_save_dir).grid(row=4, column=3, sticky=tk.W, padx=(0, 8), pady=(6, 6))
        
        auto_save_dir_save_timer = None
        def on_auto_save_dir_change(*args):
            if not self._loading_config:
                nonlocal auto_save_dir_save_timer
                if auto_save_dir_save_timer:
                    self.root.after_cancel(auto_save_dir_save_timer)
                auto_save_dir_save_timer = self.root.after(500, self.save_config)
        auto_save_dir_var.trace('w', on_auto_save_dir_change)
        model_vars['auto_save_dir_var'] = auto_save_dir_var
        
        # 操作按钮
        def start_tts():
            self._start_tts_for_model(model_name)
        
        def reset_to_defaults():
            self._reset_to_defaults_for_model(model_name)
        
        def save_audio():
            self._save_audio_for_model(model_name)
        
        def open_audio():
            self._open_audio_for_model(model_name)
        
        tts_btn = ttk.Button(parent_frame, text="生成语音", command=start_tts)
        tts_btn.grid(row=5, column=1, sticky=tk.W, padx=(0, 8), pady=(0, 8))
        model_vars['tts_btn'] = tts_btn
        
        tts_save_btn = ttk.Button(parent_frame, text="保存音频...", command=save_audio, state=tk.DISABLED)
        tts_save_btn.grid(row=5, column=2, sticky=tk.W, padx=(0, 8), pady=(0, 8))
        model_vars['tts_save_btn'] = tts_save_btn
        
        tts_open_btn = ttk.Button(parent_frame, text="打开音频", command=open_audio, state=tk.DISABLED)
        tts_open_btn.grid(row=5, column=3, sticky=tk.W, padx=(0, 8), pady=(0, 8))
        model_vars['tts_open_btn'] = tts_open_btn
        
        reset_btn = ttk.Button(parent_frame, text="恢复默认设置", command=reset_to_defaults)
        reset_btn.grid(row=5, column=0, sticky=tk.W, padx=(8, 8), pady=(0, 8))
        
        tts_status_var = tk.StringVar(value="就绪")
        ttk.Label(parent_frame, textvariable=tts_status_var, foreground="#666").grid(row=5, column=4, columnspan=2, sticky=tk.E)
        model_vars['tts_status_var'] = tts_status_var
        model_vars['tts_audio_path'] = None
        
        # 保存该模型的所有变量
        self.tts_vars[model_name] = model_vars
        
        # 为了向后兼容，将F5-TTS的变量作为默认变量
        if model_name == "f5tts":
            self.server_var = server_var
            self.ref_audio_var = ref_audio_var
            self.ref_text_var = ref_text_var
            self.gen_text = gen_text
            self.randomize_seed_var = randomize_seed_var
            self.seed_var = seed_var
            self.remove_silences_var = remove_silences_var
            self.speed_var = speed_var
            self.nfe_steps_var = nfe_steps_var
            self.crossfade_var = crossfade_var
            self.auto_save_dir_var = auto_save_dir_var
            self.tts_btn = tts_btn
            self.tts_save_btn = tts_save_btn
            self.tts_open_btn = tts_open_btn
            self.tts_status_var = tts_status_var
            self.tts_audio_path = None

    # ========== F5-TTS 相关方法 ==========
    def browse_ref_audio(self):
        file_path = filedialog.askopenfilename(title="选择参考音频", filetypes=[("音频文件", "*.wav;*.mp3;*.flac;*.m4a;*.ogg"), ("所有文件", "*.*")])
        if file_path:
            self.ref_audio_var.set(file_path)
            # 导入音频时，reference text 默认显示音频文件名（不含路径和扩展名）
            filename = os.path.splitext(os.path.basename(file_path))[0]  # 获取文件名（不含扩展名）
            self.ref_text_var.set(filename)
            self.log(f"[TTS] 已选择参考音频: {file_path}, 参考文本已自动设置为文件名: {filename}")

    def use_preview_text(self):
        text = self.preview_text.get("1.0", tk.END).strip()
        if not text:
            text = self.input_text.get("1.0", tk.END).strip()
        self.gen_text.delete("1.0", tk.END)
        self.gen_text.insert("1.0", text)
        # 手动触发保存配置（因为代码修改文本不会触发KeyRelease事件）
        if not self._loading_config:
            self.save_config()

    def _start_tts_for_model(self, model_name):
        """为指定模型启动TTS生成"""
        model_vars = self.tts_vars.get(model_name)
        if not model_vars:
            self.log(f"[{model_name.upper()}][ERROR] 未找到模型变量")
            return
        
        # 如果选中了随机种子，每次生成时自动生成新的随机种子
        if model_vars['randomize_seed_var'].get():
            new_seed = random.randint(1000000000, 9999999999)
            model_vars['seed_var'].set(new_seed)
            self.log(f"[{model_name.upper()}] 已自动生成新随机种子: {new_seed}")
        
        # 防止阻塞UI，开线程
        model_vars['tts_btn'].config(state=tk.DISABLED)
        model_vars['tts_status_var'].set(f"正在请求{model_name.upper()}...")
        self.log(f"[{model_name.upper()}] start request")
        threading.Thread(target=lambda: self._run_tts_safe_for_model(model_name), daemon=True).start()
    
    def start_tts(self):
        """向后兼容的方法，使用当前选中的模型"""
        self._start_tts_for_model(self.current_tts_model)

    def _generate_auto_save_filename(self, save_dir: str) -> str:
        """
        生成自动保存文件名：日期_编号.wav
        例如：2025-11-01_001.wav
        """
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 查找该日期下已有的文件编号
        pattern = re.compile(rf"^{re.escape(date_str)}_(\d{{3}})\.wav$")
        max_num = 0
        
        if os.path.isdir(save_dir):
            for filename in os.listdir(save_dir):
                match = pattern.match(filename)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
        
        # 生成下一个编号（3位数字，不足补0）
        next_num = max_num + 1
        filename = f"{date_str}_{next_num:03d}.wav"
        return os.path.join(save_dir, filename)
    
    def _auto_save_audio_for_model(self, model_name: str, audio_path: str) -> bool:
        """为指定模型自动保存音频"""
        model_vars = self.tts_vars.get(model_name)
        if not model_vars:
            return False
        
        auto_save_dir = model_vars['auto_save_dir_var'].get().strip()
        if not auto_save_dir:
            return False
        
        try:
            if not os.path.isdir(auto_save_dir):
                os.makedirs(auto_save_dir, exist_ok=True)
                self.log(f"[{model_name.upper()}] 已创建自动保存目录: {auto_save_dir}")
            
            save_path = self._generate_auto_save_filename(auto_save_dir)
            
            with open(audio_path, "rb") as src, open(save_path, "wb") as dst:
                dst.write(src.read())
            
            self.log(f"[{model_name.upper()}] 已自动保存音频: {save_path}")
            return True
        except Exception as e:
            self.log(f"[{model_name.upper()}][ERROR] 自动保存音频失败: {e}")
            return False
    
    def _auto_save_audio(self, audio_path: str) -> bool:
        """向后兼容的方法，使用当前选中的模型"""
        return self._auto_save_audio_for_model(self.current_tts_model, audio_path)

    def _run_tts_safe_for_model(self, model_name):
        """为指定模型运行TTS生成（线程安全）"""
        model_vars = self.tts_vars.get(model_name)
        if not model_vars:
            self.log(f"[{model_name.upper()}][ERROR] 未找到模型变量")
            return
        
        try:
            audio_path = self._call_tts_for_model(model_name)
            def _ok():
                if audio_path:
                    model_vars['tts_audio_path'] = audio_path
                    model_vars['tts_status_var'].set(f"已生成: {os.path.basename(audio_path)}")
                    model_vars['tts_save_btn'].config(state=tk.NORMAL)
                    model_vars['tts_open_btn'].config(state=tk.NORMAL)
                    
                    # 自动保存
                    self._auto_save_audio_for_model(model_name, audio_path)
                else:
                    model_vars['tts_status_var'].set("未获取到音频结果")
                model_vars['tts_btn'].config(state=tk.NORMAL)
            self.root.after(0, _ok)
        except Exception as e:
            err_msg = str(e)
            def _err(msg=err_msg):
                model_vars['tts_status_var'].set(f"错误: {msg}")
                self.log(f"[{model_name.upper()}][ERROR] {msg}")
                model_vars['tts_btn'].config(state=tk.NORMAL)
            self.root.after(0, _err)
    
    def _run_tts_safe(self):
        """向后兼容的方法，使用当前选中的模型"""
        self._run_tts_safe_for_model(self.current_tts_model)

    def _split_text_into_chunks(self, text: str, max_chars_per_chunk: int = 3000) -> list:
        """
        将文本智能分割成多个块
        优先在段落边界分割，其次在句子边界分割
        """
        if len(text) <= max_chars_per_chunk:
            return [text]
        
        chunks = []
        # 首先按段落分割（双换行）
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前段落本身就超过限制，需要进一步分割
            if len(para) > max_chars_per_chunk:
                # 先保存当前chunk（如果有内容）
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 按句子分割大段落
                sentences = re.split(r'([.!?]\s+)', para)
                current_sentence = ""
                for sent in sentences:
                    if not sent:
                        continue
                    if len(current_sentence + sent) <= max_chars_per_chunk:
                        current_sentence += sent
                    else:
                        # 保存当前句子块
                        if current_sentence:
                            chunks.append(current_sentence.strip())
                        # 如果单个句子就超过限制，强制分割
                        if len(sent) > max_chars_per_chunk:
                            # 按单词分割
                            words = sent.split()
                            current_word = ""
                            for word in words:
                                if len(current_word + " " + word) <= max_chars_per_chunk:
                                    current_word += (" " + word) if current_word else word
                                else:
                                    if current_word:
                                        chunks.append(current_word.strip())
                                    current_word = word
                            current_sentence = current_word
                        else:
                            current_sentence = sent
                if current_sentence:
                    chunks.append(current_sentence.strip())
                    current_sentence = ""
            else:
                # 检查添加这个段落后是否超过限制
                if len(current_chunk + "\n\n" + para) <= max_chars_per_chunk:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    # 保存当前chunk，开始新chunk
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para
        
        # 保存最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]
    
    def _call_f5tts_single(self, model_name: str, gen_text: str, ref_text: str = None) -> str:
        """
        调用TTS生成单个音频块（内部方法，不读取UI）
        返回临时文件路径
        """
        model_vars = self.tts_vars.get(model_name)
        if not model_vars:
            raise ValueError(f"未找到模型变量: {model_name}")
        
        server = model_vars['server_var'].get().rstrip('/')
        ref_audio = model_vars['ref_audio_var'].get().strip()
        if ref_text is None:
            ref_text = model_vars['ref_text_var'].get().strip()
        
        # 使用现有的call_f5tts逻辑，但只处理单个文本块
        file_part = None
        if ref_audio and ref_audio.strip().lower().startswith(("http://", "https://")):
            file_part = {"path": ref_audio.strip(), "meta": {"_type": "gradio.FileData"}}
        elif ref_audio and os.path.isfile(ref_audio):
            try:
                file_part = self._upload_ref_to_gradio(server, ref_audio)
            except Exception as up_err:
                self.log(f"[TTS][WARN] upload failed, fallback sample: {up_err}")
                file_part = {"path": "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav", "meta": {"_type": "gradio.FileData"}}
        else:
            file_part = {"path": "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav", "meta": {"_type": "gradio.FileData"}}
        
        # 获取模型特定的变量
        remove_silences_var = model_vars['remove_silences_var']
        randomize_seed_var = model_vars['randomize_seed_var']
        seed_var = model_vars['seed_var']
        speed_var = model_vars['speed_var']
        nfe_steps_var = model_vars['nfe_steps_var']
        crossfade_var = model_vars['crossfade_var']
        
        # 根据模型名称决定API端点
        if model_name == "e2tts":
            api_endpoint = "/gradio_api/call/basic_tts"  # 暂时使用相同的端点
        else:
            api_endpoint = "/gradio_api/call/basic_tts"  # F5-TTS端点
        
        # 辅助函数
        def get_aligned_speed():
            val = float(speed_var.get())
            snapped = round(val / 0.1) * 0.1
            if snapped < 0.1:
                snapped = 0.1
            elif snapped > 2.0:
                snapped = 2.0
            result = float(f"{snapped:.1f}")
            return result
        
        def get_valid_seed():
            try:
                seed_val = int(seed_var.get())
                if seed_val < 0:
                    seed_val = 0
                elif seed_val > 9999999999:
                    seed_val = 9999999999
                return seed_val
            except (ValueError, TypeError):
                return 0
        
        valid_seed = get_valid_seed()
        aligned_speed = get_aligned_speed()
        nfe_steps = int(nfe_steps_var.get())
        crossfade = round(crossfade_var.get(), 2)
        
        data_array = [
            file_part,
            ref_text or "",
            gen_text,
            remove_silences_var.get(),
            randomize_seed_var.get(),
            valid_seed,
            crossfade,
            nfe_steps,
            aligned_speed
        ]
        
        url_call = f"{server}{api_endpoint}"
        import json as json_module
        req_body = {"data": data_array}
        
        resp = requests.post(url_call, json=req_body, headers={"Content-Type": "application/json"}, timeout=60)
        resp.raise_for_status()
        
        event_id = None
        try:
            j = resp.json()
            event_id = j.get("event_id") or j.get("eventId") or j.get("event")
        except Exception:
            text = resp.text
            tokens = re.findall(r'"([^"]+)"', text)
            if len(tokens) >= 2:
                event_id = tokens[1]
            elif tokens:
                event_id = tokens[0]
        
        if not event_id:
            raise RuntimeError("未获取到事件ID(event_id)")
        
        # 轮询获取音频
        url_stream = f"{server}{api_endpoint}/{event_id}"
        audio_url = None
        transcribed_ref_text = None
        
        for _ in range(60):
            if audio_url and transcribed_ref_text:
                break
            try:
                r = requests.get(url_stream, timeout=30)
                r.raise_for_status()
                chunk = r.text
                if chunk:
                    import json as json_module
                    lines = chunk.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith('data: '):
                            line = line[6:].strip()
                        try:
                            msg_json = json_module.loads(line)
                            if isinstance(msg_json, dict) and msg_json.get("msg") == "process_completed":
                                output = msg_json.get("output", {})
                                data = output.get("data", [])
                                if isinstance(data, list) and len(data) >= 1:
                                    audio_item = data[0]
                                    if isinstance(audio_item, dict):
                                        audio_url = audio_item.get("url") or audio_item.get("path")
                                        if audio_url:
                                            if '\\' in audio_url or audio_url.startswith('C:'):
                                                audio_url = f"{server}/gradio_api/file={audio_url}"
                                            elif audio_url.startswith('/'):
                                                audio_url = f"{server}{audio_url}"
                                        if len(data) >= 3 and isinstance(data[2], str):
                                            transcribed_ref_text = data[2].strip()
                        except Exception:
                            continue
                    if "event: complete" in chunk:
                        data_match = re.search(r'data:\s*(\[.*?\])', chunk, re.DOTALL)
                        if data_match:
                            try:
                                data_json_str = data_match.group(1)
                                data_array = json_module.loads(data_json_str)
                                if isinstance(data_array, list) and len(data_array) > 0:
                                    first_item = data_array[0]
                                    if isinstance(first_item, dict):
                                        audio_url = first_item.get("url") or first_item.get("path")
                                        if audio_url and '\\' in audio_url:
                                            audio_url = f"{server}/gradio_api/file={audio_url}"
                                        if len(data_array) >= 3 and isinstance(data_array[2], str):
                                            transcribed_ref_text = data_array[2].strip()
                            except Exception:
                                pass
            except Exception:
                pass
            if audio_url:
                break
            time.sleep(2)
        
        if not audio_url:
            raise RuntimeError("未获取到音频结果")
        
        # 下载音频
        wav_resp = requests.get(audio_url, timeout=120)
        wav_resp.raise_for_status()
        fd, tmp_path = tempfile.mkstemp(prefix="f5tts_chunk_", suffix=".wav")
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(wav_resp.content)
        
        return tmp_path
    
    def _merge_audio_files(self, audio_files: list, output_path: str) -> str:
        """
        合并多个音频文件
        返回输出文件路径
        """
        if not PYDUB_AVAILABLE:
            raise RuntimeError("需要安装pydub库才能合并音频文件。请运行: pip install pydub")
        
        if not audio_files:
            raise ValueError("没有音频文件可合并")
        
        self.log(f"[TTS] 开始合并 {len(audio_files)} 个音频文件...")
        combined = None
        
        for i, audio_file in enumerate(audio_files):
            self.log(f"[TTS] 合并第 {i+1}/{len(audio_files)} 个文件: {os.path.basename(audio_file)}")
            try:
                audio = AudioSegment.from_wav(audio_file)
                if combined is None:
                    combined = audio
                else:
                    combined += audio
            except Exception as e:
                self.log(f"[TTS][ERROR] 读取音频文件失败: {audio_file}, 错误: {e}")
                raise
        
        combined.export(output_path, format="wav")
        self.log(f"[TTS] 合并完成，输出文件: {output_path}, 时长: {len(combined)/1000:.2f} 秒")
        return output_path

    def _call_tts_for_model(self, model_name):
        """为指定模型调用TTS API"""
        model_vars = self.tts_vars.get(model_name)
        if not model_vars:
            raise ValueError(f"未找到模型变量: {model_name}")
        
        server = model_vars['server_var'].get().rstrip('/')
        ref_audio = model_vars['ref_audio_var'].get().strip()
        ref_text = model_vars['ref_text_var'].get().strip()
        gen_text = model_vars['gen_text'].get("1.0", tk.END).strip()
        if not gen_text:
            raise ValueError("请先填写生成文本，或点击‘使用预览文本’")
        
        # 重要提示：ref_text为空时，TTS会用Whisper自动转写参考音频
        # 转写结果只用于学习参考音频特征，不应出现在生成的音频中
        # 如果生成的音频中出现了参考音频的内容，建议手动填写ref_text以避免自动转写
        if not ref_text:
            self.log(f"[{model_name.upper()}][INFO] ref_text为空，{model_name.upper()}将使用Whisper自动转写参考音频")
            self.log(f"[{model_name.upper()}][INFO] 提示：如果生成的音频中出现了参考音频的内容，建议手动填写ref_text以避免自动转写的影响")
        
        # 检查文本长度，如果过长则自动分割
        # 估算：约150-200字符/分钟，20分钟约3000-4000字符
        # 为了安全，设置每个块最大3000字符（约15-20分钟）
        MAX_CHARS_PER_CHUNK = 3000
        
        if len(gen_text) > MAX_CHARS_PER_CHUNK:
            self.log(f"[{model_name.upper()}] 检测到长文本（{len(gen_text)}字符），将自动分割成多个块")
            
            # 检查pydub是否可用
            if not PYDUB_AVAILABLE:
                raise RuntimeError("检测到长文本，需要安装pydub库才能合并音频文件。\n请运行: pip install pydub")
            
            chunks = self._split_text_into_chunks(gen_text, MAX_CHARS_PER_CHUNK)
            self.log(f"[{model_name.upper()}] 文本已分割成 {len(chunks)} 个块")
            
            if len(chunks) > 1:
                # 批量生成音频
                audio_files = []
                chunk_temp_files = []  # 记录临时文件，最后清理
                
                try:
                    for i, chunk in enumerate(chunks):
                        chunk_num = i + 1
                        self.log(f"[{model_name.upper()}] 开始生成第 {chunk_num}/{len(chunks)} 块（{len(chunk)}字符）...")
                        # 使用默认参数避免闭包问题
                        def update_status(n=chunk_num, total=len(chunks)):
                            model_vars['tts_status_var'].set(f"正在生成第 {n}/{total} 块...")
                        self.root.after(0, update_status)
                        
                        # 为每个块生成音频（使用相同的参考文本和参考音频）
                        chunk_audio_path = self._call_f5tts_single(model_name, chunk, ref_text)
                        audio_files.append(chunk_audio_path)
                        chunk_temp_files.append(chunk_audio_path)
                        self.log(f"[{model_name.upper()}] 第 {chunk_num}/{len(chunks)} 块生成完成: {chunk_audio_path}")
                    
                    # 合并所有音频块
                    self.log(f"[{model_name.upper()}] 开始合并 {len(audio_files)} 个音频块...")
                    def update_merge_status():
                        model_vars['tts_status_var'].set("正在合并音频...")
                    self.root.after(0, update_merge_status)
                    
                    # 创建最终输出文件
                    fd, final_path = tempfile.mkstemp(prefix="f5tts_merged_", suffix=".wav")
                    os.close(fd)
                    
                    # 合并音频
                    self._merge_audio_files(audio_files, final_path)
                    
                    # 清理临时文件
                    for temp_file in chunk_temp_files:
                        try:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                        except Exception as e:
                            self.log(f"[TTS][WARN] 清理临时文件失败: {temp_file}, 错误: {e}")
                    
                    self.log(f"[{model_name.upper()}] 所有音频块合并完成: {final_path}")
                    return final_path
                    
                except Exception as e:
                    # 清理已生成的临时文件
                    for temp_file in chunk_temp_files:
                        try:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                        except Exception:
                            pass
                    raise Exception(f"批量生成音频时出错: {str(e)}")
            else:
                # 只有一个块，直接生成（虽然被分割了但只有一个块，继续使用原来的逻辑）
                self.log(f"[TTS] 文本只有一个块，继续使用单块生成逻辑")
        
        # 以下是原来的单块生成逻辑（当文本长度不超过MAX_CHARS_PER_CHUNK时，或者只有一个块时）
        
        # 检查生成文本是否包含可疑内容
        if "destruction" in gen_text.lower() or "distruction" in gen_text.lower():
            self.log(f"[TTS][WARN] 生成文本包含 'destruction' 或 'distruction': {gen_text[:100]}")
        
        # 检查参考文本是否包含destruction（这不应该影响生成结果）
        if ref_text and ("destruction" in ref_text.lower() or "distruction" in ref_text.lower()):
            self.log(f"[TTS][INFO] 参考文本包含 'destruction'，这是正常的（参考文本只用于学习特征）")

        # 构造与示例一致的payload
        # 参考F5-TTS Gradio API：/gradio_api/call/basic_tts
        file_part = None
        if ref_audio and ref_audio.strip().lower().startswith(("http://", "https://")):
            # 直接使用云端音频链接
            file_part = {"path": ref_audio.strip(), "meta": {"_type": "gradio.FileData"}}
            self.log(f"[TTS] using remote ref audio: {ref_audio.strip()}")
        elif ref_audio and os.path.isfile(ref_audio):
            # 本地文件，先上传到 Gradio
            try:
                self.root.after(0, lambda: self.tts_status_var.set("正在上传参考音频..."))
                self.log(f"[TTS] uploading local ref audio: {ref_audio}")
                file_part = self._upload_ref_to_gradio(server, ref_audio)
            except Exception as up_err:
                # 如果上传失败，退回到示例音频
                self.log(f"[TTS][WARN] upload failed, fallback sample: {up_err}")
                file_part = {"path": "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav", "meta": {"_type": "gradio.FileData"}}
        else:
            # 无输入或非URL，使用示例音频
            file_part = {"path": "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav", "meta": {"_type": "gradio.FileData"}}

        # 获取模型特定的变量
        remove_silences_var = model_vars['remove_silences_var']
        randomize_seed_var = model_vars['randomize_seed_var']
        seed_var = model_vars['seed_var']
        speed_var = model_vars['speed_var']
        nfe_steps_var = model_vars['nfe_steps_var']
        crossfade_var = model_vars['crossfade_var']
        
        # 根据模型名称决定API端点
        # TODO: 如果E2TTS使用不同的端点，需要在这里修改
        if model_name == "e2tts":
            api_endpoint = "/gradio_api/call/basic_tts"  # 暂时使用相同的端点，可能需要根据实际情况修改
            self.log(f"[{model_name.upper()}] 使用E2TTS端点: {api_endpoint}")
        else:
            api_endpoint = "/gradio_api/call/basic_tts"  # F5-TTS端点
        
        # 辅助函数：获取对齐后的速度值（四舍五入到0.1的倍数，确保精确对齐）
        def get_aligned_speed():
            val = float(speed_var.get())
            # 精确对齐到0.1的倍数，避免浮点数精度问题
            snapped = round(val / 0.1) * 0.1
            if snapped < 0.1:
                snapped = 0.1
            elif snapped > 2.0:
                snapped = 2.0
            # 确保返回值是精确的浮点数，避免精度问题（例如0.7可能变成0.70000000001）
            # 使用format后再转换，确保精度正确
            result = float(f"{snapped:.1f}")
            return result
        
        # 辅助函数：获取有效的种子值（支持10位数字：0-9999999999），与前端保持一致
        def get_valid_seed():
            try:
                seed_val = int(seed_var.get())
                # 限制种子值在10位数字范围内（0-9999999999）
                if seed_val < 0:
                    seed_val = 0
                    self.log(f"[TTS][WARN] 种子值小于0，已调整为0")
                elif seed_val > 9999999999:
                    seed_val = 9999999999
                    self.log(f"[TTS][WARN] 种子值超过最大值，已调整为9999999999")
                # 注意：即使 randomize_seed 为 True，也应该传递实际的种子值
                # F5-TTS 会根据 randomize_seed 标志决定是否使用这个种子值
                self.log(f"[{model_name.upper()}] 使用种子值: {seed_val} (randomize_seed={randomize_seed_var.get()})")
                return seed_val
            except (ValueError, TypeError) as e:
                # 如果种子值无效，返回0并记录错误
                self.log(f"[{model_name.upper()}][ERROR] 种子值无效: {seed_var.get()}, 错误: {e}, 使用默认值0")
                return 0
        
        # 根据 F12 payload 的正确参数顺序：ref_audio, ref_text, gen_text, remove_silences, randomize_seed, seed, crossfade_duration, nfe_steps, speed
        # 注意：从错误看，参数顺序应该是：remove_silences, randomize_seed, seed, crossfade, nfe_steps, speed
        valid_seed = get_valid_seed()  # 先获取，确保是整数
        aligned_speed = get_aligned_speed()  # 先获取，确保是浮点数
        nfe_steps = int(nfe_steps_var.get())  # 确保是整数
        crossfade = round(crossfade_var.get(), 2)  # 确保是浮点数
        
        # 验证参数类型和值
        self.log(f"[{model_name.upper()}] 参数验证:")
        self.log(f"  - ref_text: '{ref_text[:100]}...' (长度: {len(ref_text)}, 完整内容: {repr(ref_text[:200])})")
        self.log(f"  - gen_text: '{gen_text[:100]}...' (长度: {len(gen_text)}, 完整内容: {repr(gen_text[:200])})")
        self.log(f"  - remove_silences: {remove_silences_var.get()} (类型: {type(remove_silences_var.get())})")
        self.log(f"  - randomize_seed: {randomize_seed_var.get()} (类型: {type(randomize_seed_var.get())})")
        self.log(f"  - seed: {valid_seed} (类型: {type(valid_seed)})")
        self.log(f"  - crossfade: {crossfade} (类型: {type(crossfade)})")
        self.log(f"  - nfe_steps: {nfe_steps} (类型: {type(nfe_steps)})")
        self.log(f"  - speed: {aligned_speed} (类型: {type(aligned_speed)}, 原始值: {speed_var.get()}, 对齐后: {aligned_speed})")
        
        # 验证速度值的有效性
        if aligned_speed < 0.1 or aligned_speed > 2.0:
            self.log(f"[TTS][WARN] 速度值超出范围: {aligned_speed}, 应该限制在0.1-2.0范围内")
        if aligned_speed != 1.0:
            self.log(f"[TTS][INFO] 使用非默认速度: {aligned_speed} (默认速度为1.0)")
            # 重要提示：当速度不是1.0且ref_text为空时，F5-TTS可能混入参考音频的转写结果
            if not ref_text:
                self.log(f"[TTS][WARN] 速度值为 {aligned_speed} 且参考文本为空，这可能导致参考音频的转写内容混入生成结果")
                self.log(f"[TTS][WARN] 建议：手动填写参考文本以避免自动转写的影响")
        
        # 检查是否ref_text和gen_text位置错误
        if "destruction" in ref_text.lower() and "destruction" not in gen_text.lower():
            self.log(f"[TTS][WARN] ref_text包含'destruction'但gen_text不包含，请确认参数顺序正确")
        
        data_array = [
            file_part,
            ref_text or "",
            gen_text,
            remove_silences_var.get(),  # remove_silences (bool)
            randomize_seed_var.get(),   # randomize_seed (bool)
            valid_seed,                 # seed (int)
            crossfade,                   # crossfade_duration (float)
            nfe_steps,                   # nfe_steps (int)
            aligned_speed                # speed (float)
        ]

        # 安全兜底：如果用户直接输入了本地路径（非上传后的路径），则拦截
        # 上传后的路径已经是 /file= 格式，应该可以直接使用
        try:
            p = data_array[0].get("path", "") if isinstance(data_array[0], dict) else ""
            # 只拦截用户直接输入的本地路径（包含完整Windows路径且不是 /file= 格式）
            if p and (re.match(r"^[A-Za-z]:\\", p) or re.match(r"^[A-Za-z]:/", p)) and not p.startswith('/file='):
                # 检查是否是上传后返回的格式（包含gradio目录）
                if 'gradio' not in p.lower():
                    # 用户直接输入的本地路径，强制改为示例音频
                    self.log(f"[TTS][WARN] user provided local path directly, using sample instead: {p}")
                    data_array[0] = {"path": "https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav", "meta": {"_type": "gradio.FileData"}}
        except Exception:
            pass

        url_call = f"{server}/gradio_api/call/basic_tts"
        # 完全按你提供的 curl 流程：先 /gradio_api/call/basic_tts 取 event_id，再流式拉取
        def update_status():
            model_vars['tts_status_var'].set("已发送请求，等待事件ID...")
        self.root.after(0, update_status)
        # 打印完整请求体用于对比F12
        import json as json_module
        # 确保所有参数类型正确，特别是数值类型
        # 检查每个参数的实际类型和值
        type_check = {
            "file_part": type(data_array[0]).__name__,
            "ref_text": type(data_array[1]).__name__,
            "gen_text": type(data_array[2]).__name__,
            "remove_silences": type(data_array[3]).__name__,
            "randomize_seed": type(data_array[4]).__name__,
            "seed": type(data_array[5]).__name__,
            "crossfade": type(data_array[6]).__name__,
            "nfe_steps": type(data_array[7]).__name__,
            "speed": type(data_array[8]).__name__
        }
        self.log(f"[{model_name.upper()}] 参数类型检查: {type_check}")
        
        req_body = {"data": data_array}
        self.log(f"[{model_name.upper()}] POST {url_call}")
        self.log(f"[{model_name.upper()}] 参数: randomize_seed={randomize_seed_var.get()}, seed={valid_seed}, speed={aligned_speed}, nfe_steps={nfe_steps}, crossfade={crossfade}")
        self.log(f"[{model_name.upper()}] REQUEST BODY: {json_module.dumps(req_body, indent=2, ensure_ascii=False)}")
        # 特别检查速度值，因为用户反馈速度不是1时有问题
        if aligned_speed != 1.0:
            self.log(f"[{model_name.upper()}][DEBUG] 速度值详情: 原始={speed_var.get()}, 对齐后={aligned_speed}, 类型={type(aligned_speed)}, JSON序列化后={json_module.dumps(aligned_speed)}")
            self.log(f"[{model_name.upper()}][DEBUG] data_array[8] (speed) = {data_array[8]}, 类型={type(data_array[8])}")
        resp = requests.post(url_call, json=req_body, headers={"Content-Type": "application/json"}, timeout=60)
        resp.raise_for_status()
        event_id = None
        # 优先解析 JSON
        try:
            j = resp.json()
            self.log(f"[TTS] event json: {j}")
            event_id = j.get("event_id") or j.get("eventId") or j.get("event")
        except Exception:
            text = resp.text
            self.log(f"[TTS] event text: {text[:300]}")
            # 用和 awk -F '"' {print $4} 等价的思路，抓第一个被引号包裹的 token
            tokens = re.findall(r'"([^"]+)"', text)
            if len(tokens) >= 2:
                # 常见结构 {"event_id":"<id>"}，第2个是 id
                event_id = tokens[1]
            elif tokens:
                event_id = tokens[0]
        if not event_id:
            raise RuntimeError("未获取到事件ID(event_id)")

        # 流式读取结果
        url_stream = f"{server}{api_endpoint}/{event_id}"
        def update_status3():
            model_vars['tts_status_var'].set("已获取事件ID，正在生成音频...")
        self.root.after(0, update_status3)
        self.log(f"[{model_name.upper()}] stream url: {url_stream}")
        # 轮询查询，直到生成完成拿到 wav（最多等待 ~120 秒）
        audio_url = None
        content = ""
        transcribed_ref_text = None  # 用于存储Whisper转写的参考文本
        for _ in range(60):  # 60 次 * 2s = 120s
            # 如果已经获取到音频URL和转写文本，可以退出循环
            # 但如果只有音频URL而没有转写文本，继续解析寻找转写文本
            if audio_url and transcribed_ref_text:
                self.log(f"[TTS] 已获取到音频URL和转写文本，退出轮询")
                break
            try:
                r = requests.get(url_stream, timeout=30)
                r.raise_for_status()
                # 优先尝试 JSON（许多部署直接返回 JSON 状态）
                parsed_json = None
                try:
                    parsed_json = r.json()
                except Exception:
                    parsed_json = None
                if parsed_json is not None:
                    # 常见结构：{"success": true, "data": [ {"filepath": "/file=...wav"} ]}
                    if isinstance(parsed_json, dict):
                        self.log(f"[TTS] poll json: {parsed_json}")
                        data = parsed_json.get("data")
                        if isinstance(data, list) and data:
                            first = data[0]
                            # 支持三种形态
                            if isinstance(first, str) and first.endswith('.wav'):
                                audio_url = first
                            elif isinstance(first, dict):
                                audio_url = first.get("url") or first.get("path") or first.get("filepath")
                            if audio_url:
                                if audio_url.startswith("/file="):
                                    audio_url = f"{server}{audio_url}"
                                break
                # 若不是 JSON，则当作文本内容追加并做正则匹配
                chunk = r.text
                if chunk:
                    content += ("\n" + chunk)
                    self.log(f"[TTS] poll text chunk: {chunk[:200]}")
                    
                    # 优先解析JSON消息格式（web端使用的格式）
                    # 检查是否有 process_completed 消息（JSON格式）
                    # 事件流可能是逐行的JSON消息，每行一个JSON对象
                    try:
                        import json as json_module
                        # 逐行解析（处理SSE格式或逐行JSON格式）
                        lines = chunk.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            # 跳过SSE格式的前缀（如 "data: "）
                            if line.startswith('data: '):
                                line = line[6:].strip()
                            # 尝试解析为JSON
                            try:
                                msg_json = json_module.loads(line)
                                if isinstance(msg_json, dict) and msg_json.get("msg") == "process_completed":
                                    self.log(f"[{model_name.upper()}] 检测到process_completed消息（JSON格式）")
                                    output = msg_json.get("output", {})
                                    data = output.get("data", [])
                                    self.log(f"[{model_name.upper()}][DEBUG] output.data长度: {len(data) if isinstance(data, list) else 'N/A'}")
                                    if isinstance(data, list):
                                        self.log(f"[{model_name.upper()}][DEBUG] data内容预览: {str(data)[:500]}")
                                    if isinstance(data, list) and len(data) >= 1:
                                        # data[0] 是音频文件对象
                                        audio_item = data[0]
                                        if isinstance(audio_item, dict):
                                            audio_url = audio_item.get("url") or audio_item.get("path")
                                            if audio_url:
                                                # 处理Windows路径：如果URL字段包含Windows路径（带反斜杠），直接使用
                                                # 根据web端数据：url字段是 "http://127.0.0.1:7860/gradio_api/file=C:\\Users\\..."
                                                if audio_url.startswith('http'):
                                                    # 已经是完整URL（包含Windows路径）
                                                    pass
                                                elif '\\' in audio_url or audio_url.startswith('C:'):
                                                    # Windows路径，转换为URL格式
                                                    audio_url = f"{server}/gradio_api/file={audio_url}"
                                                elif audio_url.startswith('/'):
                                                    # 相对路径，添加server
                                                    audio_url = f"{server}{audio_url}"
                                                self.log(f"[{model_name.upper()}] 从process_completed提取到音频URL: {audio_url}")
                                                # 提取转写的参考文本（output.data[2]是转写的参考文本）
                                                self.log(f"[{model_name.upper()}][DEBUG] 尝试提取转写文本，data长度={len(data)}")
                                                if len(data) >= 3:
                                                    self.log(f"[{model_name.upper()}][DEBUG] data[2]类型: {type(data[2])}, 值预览: {str(data[2])[:100]}")
                                                    if isinstance(data[2], str):
                                                        transcribed_ref_text = data[2].strip()
                                                        if transcribed_ref_text:
                                                            self.log(f"[{model_name.upper()}] 从process_completed提取到转写的参考文本: {transcribed_ref_text[:100]}")
                                                        else:
                                                            self.log(f"[{model_name.upper()}][WARN] data[2]存在但为空字符串")
                                                    else:
                                                        self.log(f"[{model_name.upper()}][WARN] data[2]不是字符串，类型={type(data[2])}")
                                                else:
                                                    self.log(f"[{model_name.upper()}][WARN] data数组长度不足，len={len(data)}, 需要至少3个元素（音频、图片、转写文本）")
                                                # 找到音频URL，跳出内层循环，外层循环会在下次迭代时检查audio_url并退出
                                                break
                            except json_module.JSONDecodeError:
                                # 不是JSON，继续下一行
                                continue
                    except Exception as e:
                        self.log(f"[TTS] JSON消息解析异常: {e}")
                        pass
                    
                    # 尝试从事件流中提取Whisper转写的参考文本
                    # 检查日志消息中是否包含转写结果
                    if "msg" in chunk and "log" in chunk:
                        # 尝试解析日志消息
                        try:
                            import json as json_module
                            # 查找包含转写结果的日志消息
                            log_match = re.search(r'"msg":\s*"log",\s*"log":\s*"([^"]+)"', chunk)
                            if log_match:
                                log_content = log_match.group(1)
                                # 如果日志中包含转写相关的信息，尝试提取
                                if "reference text" in log_content.lower() or "transcribed" in log_content.lower() or "whisper" in log_content.lower():
                                    self.log(f"[TTS] 检测到转写相关日志: {log_content[:100]}")
                        except Exception:
                            pass
                    
                    # 尝试从完整的响应中提取转写结果（如果有的话）
                    # 有些API可能会在事件流中返回转写结果
                    if "reference_text" in chunk.lower() or "transcribed_text" in chunk.lower():
                        try:
                            import json as json_module
                            # 尝试解析JSON格式的转写结果
                            json_match = re.search(r'\{[^}]*"reference_text"[^}]*\}', chunk, re.IGNORECASE)
                            if json_match:
                                trans_json = json_module.loads(json_match.group(0))
                                if "reference_text" in trans_json:
                                    transcribed_ref_text = trans_json["reference_text"]
                                    self.log(f"[TTS] 从事件流中提取到转写结果: {transcribed_ref_text[:100]}")
                        except Exception:
                            pass
                    
                    # 检查错误事件
                    if "event: error" in chunk:
                        # 提取错误消息
                        error_match = re.search(r'event:\s*error\s*\n\s*data:\s*(.+)', chunk, re.MULTILINE)
                        if error_match:
                            error_msg = error_match.group(1).strip()
                            self.log(f"[TTS][ERROR] API返回错误: {error_msg}")
                        else:
                            self.log(f"[TTS][ERROR] API返回错误事件，但无法解析错误消息")
                    # 解析 SSE 格式：event: complete\ndata: [{"path":"...","url":"..."}]
                    if "event: complete" in chunk:
                        # 查找 data: 后面的 JSON
                        data_match = re.search(r'data:\s*(\[.*?\])', chunk, re.DOTALL)
                        if data_match:
                            try:
                                data_json_str = data_match.group(1)
                                import json as json_module
                                data_array = json_module.loads(data_json_str)
                                if isinstance(data_array, list) and len(data_array) > 0:
                                    first_item = data_array[0]
                                    if isinstance(first_item, dict):
                                        # 优先使用 url，其次使用 path
                                        audio_url = first_item.get("url")
                                        if not audio_url:
                                            path_val = first_item.get("path")
                                            if path_val:
                                                # 如果是 Windows 路径，尝试转换为 /file= 格式
                                                if '\\' in path_val or path_val.startswith('C:'):
                                                    # Windows路径，转换为URL格式
                                                    audio_url = f"{server}/gradio_api/file={path_val}"
                                                elif path_val.startswith('/file='):
                                                    audio_url = f"{server}{path_val}"
                                                else:
                                                    audio_url = path_val
                                        if audio_url:
                                            self.log(f"[TTS] extracted audio_url from SSE: {audio_url}")
                                        # 尝试从SSE格式的data数组中提取转写文本（data[2]可能是转写文本）
                                        if len(data_array) >= 3 and isinstance(data_array[2], str):
                                            transcribed_ref_text = data_array[2].strip()
                                            if transcribed_ref_text:
                                                self.log(f"[TTS] 从SSE格式的data数组中提取到转写文本: {transcribed_ref_text[:100]}")
                                        # 注意：即使提取到了音频URL，也不要立即break，继续解析寻找process_completed消息
                                        # 因为process_completed消息包含完整的转写文本
                            except Exception as parse_err:
                                self.log(f"[TTS] SSE parse error: {parse_err}")
                    # 旧的正则匹配兜底（仅在未找到音频URL时使用）
                    if not audio_url:
                        murl = re.search(r'(https?://[^\s"\\]+\.wav)', content)
                        if murl:
                            audio_url = murl.group(1)
                        mfile = re.search(r'(\/file=[^\s"\\]+\.wav)', content)
                        if mfile:
                            audio_url = f"{server}{mfile.group(1)}"
                    # 注意：即使找到了音频URL，也不要break，继续解析寻找process_completed消息
            except Exception:
                pass
            time.sleep(2)
        # 如果事件流直接返回错误且使用的是远程URL，自动回退为：本机下载 -> 上传到gradio -> 重试一次
        if not audio_url and ("event: error" in content) and (ref_audio and ref_audio.lower().startswith(("http://", "https://"))):
            try:
                self.log("[TTS][FALLBACK] remote URL failed on server side, try local-download + gradio-upload then retry once")
                bin_resp = requests.get(ref_audio, timeout=60)
                bin_resp.raise_for_status()
                ext = os.path.splitext(ref_audio.split('?')[0])[1] or '.mp3'
                fd2, tmp2 = tempfile.mkstemp(prefix="tts_ref_", suffix=ext)
                os.close(fd2)
                with open(tmp2, 'wb') as f:
                    f.write(bin_resp.content)
                uploaded = self._upload_ref_to_gradio(server, tmp2)
                # 辅助函数：获取对齐后的速度值（四舍五入到0.1的倍数，确保精确对齐）
                def get_aligned_speed_retry():
                    val = float(self.speed_var.get())
                    # 精确对齐到0.1的倍数，避免浮点数精度问题
                    snapped = round(val / 0.1) * 0.1
                    if snapped < 0.1:
                        snapped = 0.1
                    elif snapped > 2.0:
                        snapped = 2.0
                    # 确保返回值是精确的浮点数，避免精度问题
                    result = float(f"{snapped:.1f}")
                    return result
                
                # 辅助函数：获取有效的种子值（支持10位数字：0-9999999999），与前端保持一致
                def get_valid_seed_retry():
                    try:
                        seed_val = int(self.seed_var.get())
                        # 限制种子值在10位数字范围内（0-9999999999）
                        if seed_val < 0:
                            seed_val = 0
                        elif seed_val > 9999999999:
                            seed_val = 9999999999
                        # 注意：即使 randomize_seed 为 True，也应该传递实际的种子值
                        # F5-TTS 会根据 randomize_seed 标志决定是否使用这个种子值
                        return seed_val
                    except (ValueError, TypeError):
                        # 如果种子值无效，返回0
                        return 0
                
                # 重试时也使用高级参数（与主请求参数顺序一致）
                data_array2 = [
                    uploaded,
                    ref_text or "",
                    gen_text,
                    self.remove_silences_var.get(),
                    self.randomize_seed_var.get(),
                    get_valid_seed_retry(),  # seed (有效范围：0-9999999999，10位数字)
                    round(self.crossfade_var.get(), 2),
                    int(self.nfe_steps_var.get()),
                    get_aligned_speed_retry()  # speed (范围0.1-2.0，最小单位0.1)
                ]
                self.log(f"[TTS] POST {url_call} (retry with uploaded)")
                resp2 = requests.post(url_call, json={"data": data_array2}, headers={"Content-Type": "application/json"}, timeout=60)
                resp2.raise_for_status()
                try:
                    j2 = resp2.json()
                    self.log(f"[TTS] event json (retry): {j2}")
                    event_id2 = j2.get("event_id") or j2.get("eventId") or j2.get("event")
                except Exception:
                    t2 = resp2.text
                    self.log(f"[TTS] event text (retry): {t2[:300]}")
                    tokens2 = re.findall(r'"([^"]+)"', t2)
                    event_id2 = tokens2[1] if len(tokens2) >= 2 else (tokens2[0] if tokens2 else None)
                if not event_id2:
                    return None
                url_stream2 = f"{server}/gradio_api/call/basic_tts/{event_id2}"
                self.log(f"[TTS] stream url (retry): {url_stream2}")
                content2 = ""
                for _ in range(60):
                    try:
                        r2 = requests.get(url_stream2, timeout=30)
                        r2.raise_for_status()
                        try:
                            pj2 = r2.json()
                        except Exception:
                            pj2 = None
                        if pj2 is not None and isinstance(pj2, dict):
                            self.log(f"[TTS] poll json (retry): {pj2}")
                            d2 = pj2.get("data")
                            if isinstance(d2, list) and d2:
                                first2 = d2[0]
                                if isinstance(first2, str) and first2.endswith('.wav'):
                                    audio_url = first2
                                elif isinstance(first2, dict):
                                    audio_url = first2.get("url") or first2.get("path") or first2.get("filepath")
                                if audio_url:
                                    if audio_url.startswith("/file="):
                                        audio_url = f"{server}{audio_url}"
                                    break
                        chunk2 = r2.text
                        if chunk2:
                            content2 += ("\n" + chunk2)
                            self.log(f"[TTS] poll text chunk (retry): {chunk2[:200]}")
                        murl2 = re.search(r'(https?://[^\s"\\]+\.wav)', content2)
                        if murl2:
                            audio_url = murl2.group(1)
                            break
                        mfile2 = re.search(r'(\/file=[^\s"\\]+\.wav)', content2)
                        if mfile2:
                            audio_url = f"{server}{mfile2.group(1)}"
                            break
                    except Exception:
                        pass
                    time.sleep(2)
            except Exception as fb_e:
                self.log(f"[TTS][FALLBACK][ERROR] {fb_e}")
        if not audio_url:
            return None

        # 尝试从完整的事件流内容中提取转写结果
        # 有些F5-TTS实现会在事件流中返回转写结果
        if transcribed_ref_text is None:
            # 尝试从完整的content中搜索转写结果
            # 可能是格式：{"reference_text": "..."} 或其他格式
            try:
                import json as json_module
                # 尝试解析完整的content中可能包含的转写结果
                # 搜索可能的JSON格式
                ref_text_patterns = [
                    r'"reference_text":\s*"([^"]+)"',
                    r'"transcribed_text":\s*"([^"]+)"',
                    r'"ref_text":\s*"([^"]+)"',
                    r'Using cached reference text[^"]*"([^"]+)"',
                    r'reference text[^"]*"([^"]+)"'
                ]
                for pattern in ref_text_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        transcribed_ref_text = match.group(1)
                        self.log(f"[TTS] 从事件流中提取到转写结果: {transcribed_ref_text[:100]}")
                        break
            except Exception as e:
                self.log(f"[TTS] 尝试提取转写结果时出错: {e}")
        
        # 如果获取到转写结果，更新reference text框
        # 无论当前ref_text是什么，都用服务器返回的转写结果更新
        self.log(f"[{model_name.upper()}][DEBUG] 检查转写文本: transcribed_ref_text={transcribed_ref_text}")
        if transcribed_ref_text and transcribed_ref_text.strip():
            transcribed_text = transcribed_ref_text.strip()
            self.log(f"[{model_name.upper()}] 准备更新参考文本为转写结果: {transcribed_text[:100]}")
            def update_ref_text():
                # 更新对应模型的参考文本字段
                model_vars['ref_text_var'].set(transcribed_text)
                self.log(f"[{model_name.upper()}] 已自动更新参考文本为转写结果: {transcribed_text[:100]}")
                # 延迟保存配置，确保ref_text也被保存
                self.root.after(500, self.save_config)
            self.root.after(0, update_ref_text)
        else:
            self.log(f"[{model_name.upper()}][WARN] 未获取到转写文本，transcribed_ref_text={transcribed_ref_text}")

        # 下载到临时文件
        def update_download_status():
            model_vars['tts_status_var'].set("正在下载音频...")
        self.root.after(0, update_download_status)
        self.log(f"[{model_name.upper()}] download: {audio_url}")
        wav_resp = requests.get(audio_url, timeout=120)
        wav_resp.raise_for_status()
        fd, tmp_path = tempfile.mkstemp(prefix="f5tts_", suffix=".wav")
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(wav_resp.content)
        self.log(f"[{model_name.upper()}] saved: {tmp_path} size={len(wav_resp.content)} bytes")
        return tmp_path

    def _upload_ref_to_gradio(self, server: str, local_path: str):
        """将本地参考音频上传到 Gradio 缓存，返回 gradio.FileData 所需的 {path, meta} 结构。
        按照 F12 看到的格式：/gradio_api/upload?upload_id=xxx，使用 multipart/form-data，字段名为 files。
        """
        filename = os.path.basename(local_path)
        # 生成 upload_id（Gradio 格式：随机字符串）
        upload_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))
        
        # 按 F12 看到的格式：/gradio_api/upload?upload_id=xxx
        upload_url = f"{server}/gradio_api/upload?upload_id={upload_id}"
        
        try:
            self.log(f"[TTS][UPLOAD] upload_url: {upload_url}, file: {filename}")
            # 使用 multipart/form-data，字段名为 files（复数）
            with open(local_path, 'rb') as fh:
                mime = 'audio/mpeg' if local_path.lower().endswith('.mp3') else 'audio/wav'
                files = {'files': (filename, fh, mime)}
                resp = requests.post(upload_url, files=files, timeout=60)
            resp.raise_for_status()
            
            # 从 F12 Response 看，返回的是 JSON 字符串数组，例如：["C:\\Users\\...\\tts.mp3"]
            try:
                data = resp.json()
                self.log(f"[TTS][UPLOAD] response json: {data}")
            except Exception:
                text = resp.text.strip()
                self.log(f"[TTS][UPLOAD] response text: {text[:200]}")
                # 尝试解析为 JSON（可能是字符串形式的数组）
                try:
                    import json as json_module
                    data = json_module.loads(text)
                except Exception:
                    # 如果不是 JSON，尝试提取路径字符串
                    m = re.search(r'"([^"]+\.(mp3|wav|flac|m4a|ogg))"', text)
                    if m:
                        data = [m.group(1)]
                    else:
                        raise RuntimeError(f"无法解析上传响应: {text[:200]}")
            
            # 解析返回的路径
            path_val = None
            if isinstance(data, list) and len(data) > 0:
                # 返回格式：["C:\\Users\\...\\file.mp3"] 或 ["/file=xxx"]
                path_val = data[0]
                # 去掉可能的引号
                if isinstance(path_val, str):
                    path_val = path_val.strip('"\'')
            elif isinstance(data, dict):
                # 也可能是 {"files": [{"path": "..."}]}
                if 'files' in data and isinstance(data['files'], list) and data['files']:
                    first = data['files'][0]
                    if isinstance(first, dict):
                        path_val = first.get('path') or first.get('filepath')
                    elif isinstance(first, str):
                        path_val = first
                elif 'path' in data:
                    path_val = data['path']
            
            if not path_val:
                raise RuntimeError(f"上传响应中未找到路径: {data}")
            
            # 根据F12 payload，path应该直接使用Windows路径（不需要转换为/file=格式）
            # path字段：直接使用Windows路径，反斜杠需要转义为双反斜杠（JSON格式）
            # url字段：http://server/gradio_api/file=Windows路径（路径中的反斜杠也需要转义）
            
            self.log(f"[TTS][UPLOAD] raw path from gradio: {path_val}")
            
            # 构建完整的文件对象，包含所有必要字段（按正常工作的请求格式和顺序）
            # 正常工作的请求字段顺序：path, url, orig_name, size, mime_type, meta
            file_obj = {
                "path": path_val  # 直接使用Windows路径（JSON序列化时会自动转义反斜杠）
            }
            
            # 构建url（按正常工作的请求格式：http://server/gradio_api/file=Windows路径）
            # 注意：根据用户提供的正常工作的请求，URL中保持反斜杠：http://127.0.0.1:7860/gradio_api/file=C:\\Users\\...
            if path_val and ('\\' in path_val or path_val.startswith('C:') or path_val.startswith('/')):
                # URL中保持反斜杠，与正常工作的请求格式一致（Gradio内部会处理）
                file_obj["url"] = f"{server}/gradio_api/file={path_val}"
            elif path_val.startswith('http'):
                file_obj["url"] = path_val
            
            # 添加orig_name、size、mime_type（按正常工作的请求顺序）
            file_obj["orig_name"] = filename
            try:
                file_size = os.path.getsize(local_path)
                file_obj["size"] = file_size
            except Exception:
                file_obj["size"] = 0
            
            file_obj["mime_type"] = 'audio/mpeg' if local_path.lower().endswith('.mp3') else 'audio/wav'
            
            # meta字段放在最后，与正常工作的请求格式一致
            file_obj["meta"] = {"_type": "gradio.FileData"}
            
            self.log(f"[TTS][UPLOAD] file object: {file_obj}")
            return file_obj
            
        except Exception as e:
            self.log(f"[TTS][UPLOAD][ERROR] {e}")
            raise RuntimeError(f"参考音频上传失败: {e}")

    def _save_audio_for_model(self, model_name):
        """为指定模型保存音频"""
        model_vars = self.tts_vars.get(model_name)
        if not model_vars or not model_vars.get('tts_audio_path') or not os.path.isfile(model_vars['tts_audio_path']):
            messagebox.showwarning("提示", "没有可保存的音频。")
            return
        out_path = filedialog.asksaveasfilename(title="保存音频", defaultextension=".wav", filetypes=[("WAV 音频", "*.wav"), ("所有文件", "*.*")])
        if not out_path:
            return
        try:
            with open(model_vars['tts_audio_path'], "rb") as src, open(out_path, "wb") as dst:
                dst.write(src.read())
            messagebox.showinfo("成功", f"已保存到: {out_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def _open_audio_for_model(self, model_name):
        """为指定模型打开音频"""
        model_vars = self.tts_vars.get(model_name)
        if model_vars and model_vars.get('tts_audio_path') and os.path.isfile(model_vars['tts_audio_path']):
            try:
                os.startfile(model_vars['tts_audio_path'])
            except Exception as e:
                messagebox.showerror("错误", f"无法打开音频: {e}")

    def _reset_to_defaults_for_model(self, model_name):
        """为指定模型恢复默认设置"""
        model_vars = self.tts_vars.get(model_name)
        if not model_vars:
            return
        
        # 只恢复高级设置默认值
        model_vars['randomize_seed_var'].set(True)
        model_vars['seed_var'].set(random.randint(1000000000, 9999999999))
        model_vars['remove_silences_var'].set(False)
        model_vars['speed_var'].set(1.0)
        model_vars['nfe_steps_var'].set(32)
        model_vars['crossfade_var'].set(0.15)
        
        self.log(f"[{model_name.upper()}] 已恢复高级设置为默认值")
        if not self._loading_config:
            self.save_config()

    def save_audio(self):
        """向后兼容的方法，使用当前选中的模型"""
        self._save_audio_for_model(self.current_tts_model)

    def open_audio(self):
        """向后兼容的方法，使用当前选中的模型"""
        self._open_audio_for_model(self.current_tts_model)
    
    def load_config(self):
        """从配置文件加载上次的设置"""
        try:
            # 设置标志，避免在加载时触发保存
            self._loading_config = True
            
            if os.path.isfile(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 支持旧版配置格式（单个模型）和新版格式（多个模型）
                # 如果存在 'f5tts' 或 'e2tts' 键，说明是新版格式
                if 'f5tts' in config or 'e2tts' in config:
                    # 新版格式：每个模型独立配置
                    for model_name in ['f5tts', 'e2tts']:
                        if model_name not in self.tts_vars:
                            continue
                        model_vars = self.tts_vars[model_name]
                        model_config = config.get(model_name, {})
                        
                        # 恢复服务器地址
                        if 'server' in model_config:
                            model_vars['server_var'].set(model_config['server'])
                        
                        # 恢复参考音频路径
                        if 'ref_audio' in model_config and model_config['ref_audio']:
                            if os.path.isfile(model_config['ref_audio']) or model_config['ref_audio'].startswith('http'):
                                model_vars['ref_audio_var'].set(model_config['ref_audio'])
                        
                        # 恢复参考文本
                        if 'ref_text' in model_config:
                            model_vars['ref_text_var'].set(model_config['ref_text'])
                        
                        # 恢复生成文本
                        if 'gen_text' in model_config:
                            model_vars['gen_text'].delete('1.0', tk.END)
                            model_vars['gen_text'].insert('1.0', model_config['gen_text'])
                        
                        # 恢复高级设置
                        if 'remove_silences' in model_config:
                            model_vars['remove_silences_var'].set(model_config['remove_silences'])
                        if 'randomize_seed' in model_config:
                            model_vars['randomize_seed_var'].set(model_config['randomize_seed'])
                        if 'seed' in model_config:
                            model_vars['seed_var'].set(model_config['seed'])
                        if 'speed' in model_config:
                            model_vars['speed_var'].set(model_config['speed'])
                        if 'nfe_steps' in model_config:
                            model_vars['nfe_steps_var'].set(model_config['nfe_steps'])
                        if 'crossfade' in model_config:
                            model_vars['crossfade_var'].set(model_config['crossfade'])
                        if 'auto_save_dir' in model_config:
                            model_vars['auto_save_dir_var'].set(model_config['auto_save_dir'])
                else:
                    # 旧版格式：只有一个模型（F5-TTS）的配置，需要迁移
                    # 恢复服务器地址（只恢复到F5-TTS，如果有的话）
                    if 'server' in config and 'f5tts' in self.tts_vars:
                        self.tts_vars['f5tts']['server_var'].set(config['server'])
                    
                    # 恢复参考音频路径
                    if 'ref_audio' in config and config['ref_audio'] and 'f5tts' in self.tts_vars:
                        if os.path.isfile(config['ref_audio']) or config['ref_audio'].startswith('http'):
                            self.tts_vars['f5tts']['ref_audio_var'].set(config['ref_audio'])
                    
                    # 恢复参考文本
                    if 'ref_text' in config and 'f5tts' in self.tts_vars:
                        self.tts_vars['f5tts']['ref_text_var'].set(config['ref_text'])
                    
                    # 恢复生成文本
                    if 'gen_text' in config and 'f5tts' in self.tts_vars:
                        self.tts_vars['f5tts']['gen_text'].delete('1.0', tk.END)
                        self.tts_vars['f5tts']['gen_text'].insert('1.0', config['gen_text'])
                    
                    # 恢复高级设置
                    if 'f5tts' in self.tts_vars:
                        f5tts_vars = self.tts_vars['f5tts']
                        if 'remove_silences' in config:
                            f5tts_vars['remove_silences_var'].set(config['remove_silences'])
                        if 'randomize_seed' in config:
                            f5tts_vars['randomize_seed_var'].set(config['randomize_seed'])
                        if 'seed' in config:
                            f5tts_vars['seed_var'].set(config['seed'])
                        if 'speed' in config:
                            f5tts_vars['speed_var'].set(config['speed'])
                        if 'nfe_steps' in config:
                            f5tts_vars['nfe_steps_var'].set(config['nfe_steps'])
                        if 'crossfade' in config:
                            f5tts_vars['crossfade_var'].set(config['crossfade'])
                        if 'auto_save_dir' in config:
                            f5tts_vars['auto_save_dir_var'].set(config['auto_save_dir'])
                    
            # 清除标志
            self._loading_config = False
        except Exception as e:
            self._loading_config = False
            self.log(f"[CONFIG] 加载配置失败: {e}")
    
    def save_config(self):
        """保存当前设置到配置文件"""
        try:
            config = {}
            
            # 保存每个模型的独立配置
            for model_name in ['f5tts', 'e2tts']:
                if model_name not in self.tts_vars:
                    continue
                
                model_vars = self.tts_vars[model_name]
                config[model_name] = {
                    'server': model_vars['server_var'].get(),
                    'ref_audio': model_vars['ref_audio_var'].get(),
                    'ref_text': model_vars['ref_text_var'].get(),
                    'gen_text': model_vars['gen_text'].get('1.0', tk.END).strip(),
                    'remove_silences': model_vars['remove_silences_var'].get(),
                    'randomize_seed': model_vars['randomize_seed_var'].get(),
                    'seed': model_vars['seed_var'].get(),
                    'speed': model_vars['speed_var'].get(),
                    'nfe_steps': model_vars['nfe_steps_var'].get(),
                    'crossfade': model_vars['crossfade_var'].get(),
                    'auto_save_dir': model_vars['auto_save_dir_var'].get()
                }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"[CONFIG] 保存配置失败: {e}")
    
    def setup_auto_save(self):
        """设置自动保存配置（在变量改变时保存）"""
        # 确保标志已初始化（如果在load_config中已设置，这里会覆盖）
        if not hasattr(self, '_loading_config'):
            self._loading_config = False
        
        def save_wrapper(var_name, *args):
            if not self._loading_config:
                self.save_config()
        
        # 绑定所有变量的变化事件
        # 使用 trace('w', ...) 在变量写入时触发保存
        # 注意：滑块变量（speed_var, nfe_steps_var, crossfade_var）的保存已经在各自的显示更新函数中处理，避免重复绑定
        self.server_var.trace('w', lambda *args: save_wrapper('server', *args))
        self.ref_audio_var.trace('w', lambda *args: save_wrapper('ref_audio', *args))
        self.ref_text_var.trace('w', lambda *args: save_wrapper('ref_text', *args))
        self.remove_silences_var.trace('w', lambda *args: save_wrapper('remove_silences', *args))
        self.randomize_seed_var.trace('w', lambda *args: save_wrapper('randomize_seed', *args))
        self.seed_var.trace('w', lambda *args: save_wrapper('seed', *args))
        
        # 绑定生成文本的变化事件
        def on_gen_text_change(event=None):
            if not self._loading_config:
                self.save_config()
        self.gen_text.bind('<KeyRelease>', on_gen_text_change)
        self.gen_text.bind('<Button-1>', on_gen_text_change)
    
    def reset_to_defaults(self):
        """恢复高级设置为默认值"""
        try:
            # 设置标志，避免在恢复时触发保存
            self._loading_config = True
            
            # 只恢复高级设置默认值
            self.remove_silences_var.set(False)
            self.randomize_seed_var.set(True)
            default_seed = random.randint(1000000000, 9999999999)  # 10位数字
            self.seed_var.set(default_seed)
            self.speed_var.set(1.0)
            self.nfe_steps_var.set(32)
            self.crossfade_var.set(0.15)
            
            # 清除标志并手动保存配置（因为变量已经设置完，trace不会触发）
            self._loading_config = False
            self.save_config()
            
            self.log("[CONFIG] 已恢复高级设置为默认值")
        except Exception as e:
            self._loading_config = False
            self.log(f"[CONFIG] 恢复默认设置失败: {e}")

def main():
    root = tk.Tk()
    app = TextFormatter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
