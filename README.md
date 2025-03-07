# Mistral PDF OCR 工具

这是一个使用 Mistral AI 的 OCR API 处理 PDF 文档的工具，可以从文档中提取文本和结构信息。

## 功能特点

- 支持处理单个或多个 PDF、PNG、JPG、JPEG 文档
- 支持多种输出格式：Markdown、纯文本和 JSON
- 生成文字版 PDF 文件，支持中文显示
- 自动检测系统中的中文字体，确保 PDF 文件正确显示中文
- 自动管理 API 密钥，首次使用时提示输入并安全保存
- 简化的用户交互流程，自动检测文件或目录
- 自动检查必要的依赖包并提供清晰的安装指导
- 完善的错误处理机制
- 使用 Mistral 官方 Python 客户端库进行 API 调用

## 安装指南

### 1. 安装依赖

运行以下命令安装所需的依赖包：

```bash
pip install mistralai python-dotenv tqdm reportlab
```

脚本会在启动时自动检查依赖包是否已安装，如果缺少任何必要的依赖，会提供清晰的安装指导。

### 2. 获取 Mistral API 密钥

1. 访问 [Mistral AI 平台](https://console.mistral.ai/)
2. 注册并登录您的账户
3. 在控制台中创建 API 密钥

首次运行脚本时，系统会提示您输入 API 密钥，该密钥将被保存到 `.env` 文件中，以便后续使用。

## 使用方法

### 基本用法

直接运行脚本，脚本会自动检查依赖并提示您输入文件路径：

```bash
python mistral_pdf_ocr.py
```

脚本会自动检测您输入的是文件还是目录，无需手动选择模式。支持的文件格式包括：PDF、PNG、JPG、JPEG。

### 命令行选项

```bash
# 处理单个文件
python mistral_pdf_ocr.py --file "文档路径.pdf"

# 处理目录中的所有文档
python mistral_pdf_ocr.py --directory "文档目录路径"

# 指定输出格式（markdown、text 或 json）
python mistral_pdf_ocr.py --file "文档路径.pdf" --format markdown

# 生成文字版 PDF
python mistral_pdf_ocr.py --file "文档路径.pdf" --pdf

# 指定输出目录
python mistral_pdf_ocr.py --directory "文档目录路径" --output "输出目录路径"

# 指定 API 密钥
python mistral_pdf_ocr.py --file "文档路径.pdf" --api-key "YOUR_API_KEY"
```

脚本会自动处理文件路径中的引号，无需手动去除。

## 输出文件

脚本会生成以下类型的输出文件：

- `文档名_OCR.md`：Markdown 格式的 OCR 结果，包含原始文档的图像和提取的文本
- `文档名_OCR文本版本.pdf`：文字版 PDF 文件（如果使用 `--pdf` 选项），包含提取的文本内容，并支持中文显示

## 常见问题解决

### PDF 中文字符显示问题

脚本现在会自动检测并使用系统中的中文字体，确保生成的 PDF 文件能正确显示中文字符。脚本会自动尝试以下字体：

- `/System/Library/Fonts/PingFang.ttc`
- `/Library/Fonts/Arial Unicode.ttf`
- `/Library/Fonts/STHeiti Light.ttc`
- `/System/Library/Fonts/STHeiti Light.ttc`
- `/System/Library/Fonts/Hiragino Sans GB.ttc`

如果仍然出现中文显示问题，请确保您的系统中安装了上述字体之一。脚本会在控制台输出字体检测和注册信息，便于诊断问题。

### 依赖安装问题

如果遇到依赖安装问题，请确保您使用的是最新版本的 pip：

```bash
pip install --upgrade pip
```

然后再尝试安装依赖包。

## 注意事项

- 脚本使用 Mistral AI 的 OCR API，需要互联网连接
- 处理大型文档可能需要较长时间
- API 使用可能会产生费用，请参考 Mistral AI 的定价政策
- 脚本会自动保存 Markdown 和 PDF 输出文件
- 如果您遇到任何问题，脚本会提供详细的错误信息和解决建议
