#!/usr/bin/env python3
"""
Mistral PDF OCR 处理器

此脚本使用 Mistral AI 的 OCR API 处理 PDF 文档，从文档中提取文本
和结构信息。它支持处理单个或多个 PDF 文件，并以各种格式输出结果。

依赖项:
    - mistralai
    - python-dotenv
    - tqdm
    - argparse

使用方法:
    python mistral_pdf_ocr.py --file 文档路径/文档.pdf
    python mistral_pdf_ocr.py --directory 文档目录路径/ --output 结果目录/
"""

import os
import json
import argparse
import base64
from pathlib import Path
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
from tqdm import tqdm

# 导入 ReportLab 用于生成 PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 导入 Mistral 官方客户端库
from mistralai import Mistral
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
from mistralai.models import OCRResponse
from mistralai.models.sdkerror import SDKError

# 加载环境变量
load_dotenv()

# 检查必要的依赖并提供安装指导
def check_dependencies():
    """
    检查必要的依赖是否已安装，如果缺少依赖则提供安装指导
    """
    missing_packages = []
    
    # 检查必要的包
    try:
        import mistralai
    except ImportError:
        missing_packages.append("mistralai")
    
    try:
        import dotenv
    except ImportError:
        missing_packages.append("python-dotenv")
    
    try:
        import tqdm
    except ImportError:
        missing_packages.append("tqdm")
    
    try:
        import reportlab
    except ImportError:
        missing_packages.append("reportlab")
    
    # 如果有缺少的包，提供安装指导
    if missing_packages:
        print("\n" + "=" * 80)
        print("\u7f3a少必要的依赖包！\n")
        print("请使用以下命令安装缺少的依赖包：\n")
        print(f"pip install {' '.join(missing_packages)}")
        print("\n或者使用以下命令安装所有必要的依赖包：\n")
        print("pip install mistralai python-dotenv tqdm reportlab")
        print("\n安装完成后，请重新运行此脚本。")
        print("=" * 80 + "\n")
        return False
    
    return True

# 常量定义
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")  # 从环境变量获取 API 密钥
DEFAULT_MODEL = "mistral-ocr-latest"  # 默认使用的 OCR 模型


def check_and_setup_api_key():
    """
    检查是否存在 API 密钥，如果不存在，提示用户输入并保存到 .env 文件
    """
    global MISTRAL_API_KEY
    
    if not MISTRAL_API_KEY:
        print("未找到 Mistral API 密钥。")
        print("请访问 https://console.mistral.ai/ 获取您的 API 密钥。")
        MISTRAL_API_KEY = input("请输入您的 Mistral API 密钥: ").strip()
        
        if MISTRAL_API_KEY:
            # 将 API 密钥保存到 .env 文件
            env_path = Path(".env")
            
            if env_path.exists():
                # 读取现有的 .env 文件内容
                with open(env_path, "r") as f:
                    lines = f.readlines()
                
                # 检查是否已存在 MISTRAL_API_KEY 行
                key_exists = False
                for i, line in enumerate(lines):
                    if line.startswith("MISTRAL_API_KEY="):
                        lines[i] = f"MISTRAL_API_KEY={MISTRAL_API_KEY}\n"
                        key_exists = True
                        break
                
                # 如果不存在，添加新行
                if not key_exists:
                    lines.append(f"MISTRAL_API_KEY={MISTRAL_API_KEY}\n")
                
                # 写回文件
                with open(env_path, "w") as f:
                    f.writelines(lines)
            else:
                # 创建新的 .env 文件
                with open(env_path, "w") as f:
                    f.write(f"MISTRAL_API_KEY={MISTRAL_API_KEY}\n")
            
            print(".env 文件已更新，您的 API 密钥已保存。")
            return True
        else:
            print("未提供 API 密钥，无法继续。")
            return False
    
    return True


class MistralOCR:
    """
    用于使用 Mistral OCR API 处理文档的类。
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """
        初始化 MistralOCR 处理器。
        
        参数:
            api_key: Mistral API 密钥。如果未提供，将查找环境中的 MISTRAL_API_KEY。
            model: 要使用的 OCR 模型。默认为 'mistral-ocr-latest'。
        """
        self.api_key = api_key or MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("需要 Mistral API 密钥。设置 MISTRAL_API_KEY 环境变量或作为参数提供。")
        
        self.model = model
        
        # 初始化 Mistral 客户端
        try:
            print(f"正在初始化 Mistral 客户端...")
            self.client = Mistral(api_key=self.api_key)
            print(f"Mistral 客户端初始化成功")
        except Exception as e:
            print(f"初始化 Mistral 客户端时出错: {str(e)}")
            raise
    
    def process_document(self, file_path: str, output_format: str = "markdown", generate_pdf: bool = False) -> Dict:
        """
        使用 Mistral OCR API 处理文档。
        
        参数:
            file_path: 要处理的文档路径。
            output_format: OCR 输出的格式。选项：'markdown'、'text'、'json'。
                           默认为 'markdown'。
        
        返回:
            包含 OCR 结果的字典。
        """
        print(f"正在使用 Mistral OCR 模型 {self.model} 处理 {file_path}")
        
        # 验证文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"未找到文件：{file_path}")
        
        # 验证文件扩展名
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in ['.pdf', '.png', '.jpg', '.jpeg']:
            raise ValueError(f"不支持的文件格式：{file_ext}。支持的格式：PDF、PNG、JPG、JPEG")
        
        # 读取文件内容
        print(f"正在读取文件内容...")
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # 使用 Mistral 客户端发送 OCR 请求
        print(f"正在使用 Mistral 客户端发送 OCR 请求...")
        try:
            # 首先上传文件
            print(f"正在上传文件 {Path(file_path).name}...")
            pdf_file = Path(file_path)
            
            try:
                # 上传文件到 Mistral
                uploaded_file = self.client.files.upload(
                    file={
                        "file_name": pdf_file.stem,
                        "content": pdf_file.read_bytes(),
                    },
                    purpose="ocr",
                )
                
                # 获取签名 URL
                print("获取文件的签名 URL...")
                signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
                
                # 使用签名 URL 调用 OCR API
                print(f"使用签名 URL 调用 OCR API，模型: {self.model}")
                
                # 始终包含图像，以便在 Markdown 和 PDF 中显示
                response = self.client.ocr.process(
                    document=DocumentURLChunk(document_url=signed_url.url),
                    model=self.model,
                    include_image_base64=True,  # 始终包含图像
                )
                
                # 清理上传的文件
                try:
                    self.client.files.delete(file_id=uploaded_file.id)
                    print("临时文件已删除")
                except Exception as e:
                    print(f"警告: 无法删除临时文件: {str(e)}")
            except Exception as e:
                print(f"OCR 处理失败: {str(e)}")
                raise
            print("OCR 请求成功处理")
            
            # 将响应转换为字典
            import json
            # 使用正确的方法将响应转换为 JSON
            response_dict = json.loads(response.json())
            
            # 根据输出格式处理结果
            if output_format == "json":
                result = response_dict
            elif output_format == "markdown":
                # 处理 Markdown 中的图像
                result = {"content": self._get_combined_markdown(response)}
            else:  # text
                # 连接所有页面的文本内容
                text_contents = [
                    page.get("text", "") for page in response_dict.get("pages", [])
                ]
                result = {"content": "\n\n".join(text_contents)}
                
            # 保存 Markdown 文件
            if output_format == "markdown":
                md_output_path = self._save_markdown_file(file_path, result["content"])
                result["markdown_path"] = md_output_path
                print(f"已生成 Markdown 文件: {md_output_path}")
                
            # 如果需要生成 PDF，则创建文字 PDF 版本
            if generate_pdf:
                pdf_output_path = self._generate_text_pdf(file_path, result["content"])
                result["pdf_path"] = pdf_output_path
                print(f"已生成文字 PDF 版本: {pdf_output_path}")
            
            return result
            
        except SDKError as e:
            error_msg = f"Mistral API 错误: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"处理文档时出错: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
    
    def _replace_images_in_markdown(self, markdown_str: str, images_dict: dict) -> str:
        """
        将 Markdown 中的图像引用替换为 base64 编码的图像
        
        参数:
            markdown_str: Markdown 字符串
            images_dict: 图像 ID 到 base64 字符串的映射
            
        返回:
            替换后的 Markdown 字符串
        """
        for img_name, base64_str in images_dict.items():
            markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})")
        return markdown_str
    
    def _get_combined_markdown(self, ocr_response: OCRResponse) -> str:
        """
        将 OCR 响应中的所有页面的 Markdown 内容组合起来，并处理图像
        
        参数:
            ocr_response: OCR 响应对象
            
        返回:
            组合后的 Markdown 字符串
        """
        markdowns = []
        for page in ocr_response.pages:
            image_data = {}
            for img in page.images:
                image_data[img.id] = img.image_base64
            markdowns.append(self._replace_images_in_markdown(page.markdown, image_data))
        
        return "\n\n".join(markdowns)
    
    def _save_markdown_file(self, original_file_path: str, content: str) -> str:
        """
        将 OCR 结果保存为 Markdown 文件
        
        参数:
            original_file_path: 原始文件路径，用于生成输出文件名
            content: 要写入文件的 Markdown 内容
            
        返回:
            生成的 Markdown 文件路径
        """
        # 创建输出文件路径
        original_path = Path(original_file_path)
        output_md_path = original_path.with_stem(f"{original_path.stem}_OCR").with_suffix(".md")
        
        # 写入文件
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return str(output_md_path)
    
    def _generate_text_pdf(self, original_file_path: str, content: str) -> str:
        """
        将 OCR 文本内容生成为 PDF 文件
        
        参数:
            original_file_path: 原始文件路径，用于生成输出文件名
            content: 要写入 PDF 的文本内容
            
        返回:
            生成的 PDF 文件路径
        """
        # 创建输出文件路径
        original_path = Path(original_file_path)
        output_pdf_path = original_path.with_stem(f"{original_path.stem}_OCR文本版本").with_suffix(".pdf")
        
        # 创建 PDF 文档
        doc = SimpleDocTemplate(
            str(output_pdf_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # 注册中文字体
        try:
            # 尝试使用系统自带的中文字体
            # macOS 上的常见中文字体
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",  # PingFang
                "/Library/Fonts/Arial Unicode.ttf",  # Arial Unicode
                "/Library/Fonts/STHeiti Light.ttc",  # Heiti
                "/System/Library/Fonts/STHeiti Light.ttc",  # Heiti
                "/System/Library/Fonts/Hiragino Sans GB.ttc"  # Hiragino
            ]
            
            font_registered = False
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        font_registered = True
                        print(f"已注册中文字体: {font_path}")
                        break
                except Exception as e:
                    print(f"注册字体 {font_path} 失败: {str(e)}")
                    continue
            
            if not font_registered:
                # 如果没有找到中文字体，使用默认字体
                print("警告: 未找到中文字体，将使用默认字体。PDF 中的中文可能显示为乱码。")
                chinese_font_name = 'Helvetica'
            else:
                chinese_font_name = 'ChineseFont'
                
        except Exception as e:
            print(f"警告: 注册中文字体时出错: {str(e)}")
            chinese_font_name = 'Helvetica'
        
        # 创建样式
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Normal_CH',
            fontName=chinese_font_name,
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
        ))
        
        # 准备内容
        story = []
        
        # 添加标题
        title = f"OCR 文本版本 - {original_path.name}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 0.25 * inch))
        
        # 添加正文内容
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.replace('\n', '<br/>'), styles['Normal_CH']))
                story.append(Spacer(1, 0.1 * inch))
        
        # 构建 PDF
        doc.build(story)
        
        return str(output_pdf_path)
    
    def process_directory(self, directory_path: str, output_dir: Optional[str] = None, 
                         output_format: str = "markdown", generate_pdf: bool = False) -> List[Dict]:
        """
        处理目录中的所有 PDF 文档。
        
        参数:
            directory_path: 包含文档的目录路径。
            output_dir: 保存结果的目录。如果为 None，结果不会保存到文件中。
            output_format: OCR 输出的格式。选项：'markdown'、'text'、'json'。
                          默认为 'markdown'。
        
        返回:
            包含每个文档 OCR 结果的字典列表。
        """
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"未找到目录：{directory_path}")
        
        # 如果指定了输出目录，则创建它
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        results = []
        # 获取所有支持的文档文件
        pdf_files = [f for f in os.listdir(directory_path) 
                    if os.path.isfile(os.path.join(directory_path, f)) 
                    and Path(f).suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']]
        
        if not pdf_files:
            print(f"在 {directory_path} 中未找到支持的文档")
            return results
        
        # 处理每个文件并显示进度条
        for file_name in tqdm(pdf_files, desc="正在处理文档"):
            file_path = os.path.join(directory_path, file_name)
            result = self.process_document(file_path, output_format)
            results.append({"file": file_name, "result": result})
            
            # 如果指定了输出目录，则将结果保存到文件
            if output_dir and 'error' not in result:
                output_file_base = os.path.join(output_dir, Path(file_name).stem)
                
                if output_format == 'markdown':
                    output_file = f"{output_file_base}.md"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result.get('content', ''))
                elif output_format == 'text':
                    output_file = f"{output_file_base}.txt"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result.get('content', ''))
                elif output_format == 'json':
                    output_file = f"{output_file_base}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"已将结果保存到 {output_file}")
        
        return results


def main():
    """
    从命令行运行脚本的主函数。
    """
    # 检查必要的依赖
    if not check_dependencies():
        return
    
    # 添加调试信息
    print("开始执行 Mistral OCR 脚本...")
    
    # 检查并设置 API 密钥
    if not check_and_setup_api_key():
        return
    
    parser = argparse.ArgumentParser(description="使用 Mistral OCR API 处理文档")
    
    # 输入选项
    input_group = parser.add_mutually_exclusive_group(required=False)  # 修改为非必需
    input_group.add_argument('--file', type=str, help='要处理的单个文档的路径')
    input_group.add_argument('--directory', type=str, help='包含要处理的文档的目录路径')
    
    # 输出选项
    parser.add_argument('--output', type=str, help='保存结果的目录')
    parser.add_argument('--format', type=str, choices=['markdown', 'text', 'json'], 
                        default='markdown', help='输出格式（默认：markdown）')
    parser.add_argument('--pdf', action='store_true', help='生成文字 PDF 版本')
    
    # API 选项
    parser.add_argument('--api-key', type=str, help='Mistral API 密钥（覆盖环境变量）')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL, 
                        help=f'要使用的 OCR 模型（默认：{DEFAULT_MODEL}）')
    
    args = parser.parse_args()
    
    # 如果没有提供文件或目录参数，直接提示用户输入文件路径
    if not args.file and not args.directory:
        file_path = input("请输入 PDF 文件的完整路径: ").strip()
        # 去除路径中的引号
        file_path = file_path.strip('\'"')
        
        if not file_path:
            print("错误：未提供文件路径。")
            return
            
        # 检查是否是文件或目录
        if os.path.isfile(file_path):
            args.file = file_path
        elif os.path.isdir(file_path):
            args.directory = file_path
            # 询问输出目录
            output_dir = input("请输入输出目录路径 (可选，直接回车跳过): ").strip()
            # 去除路径中的引号
            output_dir = output_dir.strip('\'"')
            if output_dir:
                args.output = output_dir
        else:
            print(f"错误：{file_path} 不存在或不是有效的文件/目录。")
            return
        
        # 询问输出格式
        print("请选择输出格式：")
        print("1. Markdown (默认)")
        print("2. 纯文本")
        print("3. JSON")
        format_choice = input("请输入您的选择 (1/2/3): ").strip()
        
        if format_choice == "2":
            args.format = "text"
        elif format_choice == "3":
            args.format = "json"
        else:
            args.format = "markdown"  # 默认为 markdown
        
        # 询问是否生成 PDF
        pdf_choice = input("是否生成 PDF 文件版本的 OCR 结果? (y/n): ").strip().lower()
        args.pdf = pdf_choice in ["y", "yes", "是", "1", "true"]
    
    # 打印参数信息
    print(f"参数信息: 文件={args.file}, 目录={args.directory}, 输出目录={args.output}, 格式={args.format}, 生成PDF={args.pdf}")
    
    try:
        # 初始化 OCR 处理器
        print("正在初始化 OCR 处理器...")
        api_key = args.api_key or MISTRAL_API_KEY  # 使用全局变量
        
        ocr = MistralOCR(api_key=api_key, model=args.model)
        print(f"OCR 处理器初始化完成，使用模型: {args.model}")
        
        # 处理单个文件或目录
        if args.file:
            # 处理单个文件
            result = ocr.process_document(args.file, args.format, generate_pdf=args.pdf)
            
            if 'error' not in result:
                if args.output:
                    # 如果指定了输出目录，将结果保存到文件
                    os.makedirs(args.output, exist_ok=True)
                    output_file_base = os.path.join(args.output, Path(args.file).stem)
                    
                    if args.format == 'markdown':
                        output_file = f"{output_file_base}.md"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(result.get('content', ''))
                    elif args.format == 'text':
                        output_file = f"{output_file_base}.txt"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(result.get('content', ''))
                    elif args.format == 'json':
                        output_file = f"{output_file_base}.json"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    print(f"已将结果保存到 {output_file}")
                else:
                    # 将结果打印到控制台
                    if args.format == 'json':
                        print(json.dumps(result, ensure_ascii=False, indent=2))
                    else:
                        print(result.get('content', ''))
            else:
                print(f"错误：{result.get('error')}")
        
        elif args.directory:
            # 处理整个目录
            results = ocr.process_directory(args.directory, args.output, args.format, generate_pdf=args.pdf)
            
            # 如果未指定输出目录，则打印摘要
            if not args.output:
                print(f"已处理 {len(results)} 个文档：")
                for item in results:
                    status = "成功" if 'error' not in item['result'] else f"错误：{item['result']['error']}"
                    print(f"  {item['file']}：{status}")
    
    except Exception as e:
        print(f"错误：{str(e)}")
        # 打印详细的错误信息
        import traceback
        print("详细错误信息:")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
    except Exception as e:
        print(f"\n程序出错: {str(e)}")
        print("\n如果这是依赖包相关的错误，请尝试运行以下命令安装必要的依赖包：")
        print("pip install mistralai python-dotenv tqdm reportlab")
    