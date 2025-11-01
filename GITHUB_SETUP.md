# GitHub 上传指南

## 步骤 1: 在GitHub上创建新仓库

1. 访问 [GitHub.com](https://github.com)
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 填写仓库信息：
   - Repository name: `text-formatter`
   - Description: `A Python GUI tool to convert numbers to English words for voice-over purposes`
   - 选择 Public 或 Private
   - **不要**勾选 "Initialize this repository with a README"
4. 点击 "Create repository"

## 步骤 2: 连接本地仓库到GitHub

在命令行中运行以下命令（替换 YOUR_USERNAME 为你的GitHub用户名）：

```bash
git remote add origin https://github.com/YOUR_USERNAME/text-formatter.git
git branch -M main
git push -u origin main
```

## 步骤 3: 验证上传

1. 刷新GitHub页面
2. 你应该能看到以下文件：
   - `text_formatter.py` - 主程序文件
   - `README.md` - 项目说明
   - `requirements.txt` - 依赖文件
   - `.gitignore` - Git忽略文件

## 项目特点

- **功能**: 将文本中的数字转换为英文单词
- **界面**: 左右对比布局，实时预览
- **用途**: 配音友好，避免中文读音
- **支持**: 年份识别、带后缀数字处理

## 使用方法

```bash
python text_formatter.py
```

## 示例转换

- 1991s → nineteen ninety-ones
- 64 → sixty-four
- 4th → fourth
- 123 → one hundred twenty-three
