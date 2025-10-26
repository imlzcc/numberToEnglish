import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import re

class TextFormatter:
    def __init__(self, root):
        self.root = root
        self.root.title("文本格式化工具")
        self.root.geometry("1200x700")
        
        # 数字转英文的映射
        self.number_words = {
            0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
            6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
            11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
            16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
            20: "twenty", 30: "thirty", 40: "forty", 50: "fifty",
            60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety"
        }
        
        self.setup_ui()
        
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

def main():
    root = tk.Tk()
    app = TextFormatter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
