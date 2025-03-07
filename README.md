# Mistral PDF OCR 工具

这是一个使用 Mistral AI 的 OCR API 处理 PDF 文档的工具，可以从文档中提取文本和结构信息。

## 功能特点

- 支持处理单个或多个 PDF 文档
- 支持多种输出格式：Markdown、纯文本和 JSON
- 可生成文字版 PDF 文件
- 自动管理 API 密钥
- 用户友好的交互界面
- 自动检查依赖并提供安装指导

## 安装指南

### 1. 安装依赖

运行以下命令安装所需的依赖包：

```bash
pip install mistralai python-dotenv tqdm reportlab
```

### 2. 获取 Mistral API 密钥

1. 访问 [Mistral AI 平台](https://console.mistral.ai/)
2. 注册并登录您的账户
3. 在控制台中创建 API 密钥

首次运行脚本时，系统会提示您输入 API 密钥，该密钥将被保存到 `.env` 文件中，以便后续使用。

## 使用方法

### 基本用法

直接运行脚本，按照提示输入文件路径：

```bash
python mistral_pdf_ocr.py
```

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
```

## 输出文件

脚本会生成以下类型的输出文件：

- `文档名_OCR.md`：Markdown 格式的 OCR 结果
- `文档名_OCR文本版本.pdf`：文字版 PDF 文件（如果使用 `--pdf` 选项）

## 常见问题解决

### PDF 中文字符显示为乱码

如果生成的 PDF 文件中的中文字符显示为乱码，这可能是因为系统中缺少合适的中文字体。脚本会尝试使用系统中的中文字体，如果找不到合适的字体，会使用默认字体。

您可以尝试安装以下中文字体之一：
- Arial Unicode
- PingFang
- STHeiti
- Hiragino Sans GB

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
