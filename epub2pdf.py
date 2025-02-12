#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from tqdm import tqdm
import ebooklib
from ebooklib import epub
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog

# 注册中文字体
def register_chinese_font():
    try:
        # 尝试使用系统自带的中文字体
        font_paths = []
        if sys.platform.startswith('darwin'):  # macOS
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/Hiragino Sans GB.ttc'
            ]
        elif sys.platform.startswith('win'):   # Windows
            font_paths = [
                'C:\\Windows\\Fonts\\msyh.ttc',
                'C:\\Windows\\Fonts\\simsun.ttc',
                'C:\\Windows\\Fonts\\simhei.ttf'
            ]
        else:  # Linux
            font_paths = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/arphic/uming.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
            ]
            
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('chinese', font_path))
                print(f"成功注册中文字体: {font_path}")
                return True
                
        print("警告：未找到合适的中文字体，文档可能无法正确显示中文")
    except Exception as e:
        print(f"注册中文字体失败: {str(e)}")
    return False

def convert_epub_to_pdf(epub_path, output_dir=None):
    """将单个epub文件转换为pdf
    
    Args:
        epub_path: epub文件路径
        output_dir: 输出目录，如果为None则使用epub所在目录
    
    Returns:
        转换后的pdf文件路径
    """
    try:
        # 确保中文字体已注册
        has_chinese_font = register_chinese_font()
        
        # 读取epub文件
        book = epub.read_epub(epub_path)
        
        # 准备输出路径
        epub_path = Path(epub_path)
        if output_dir is None:
            output_dir = epub_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
        pdf_path = output_dir / f"{epub_path.stem}.pdf"
        
        # 创建PDF文档
        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        width, height = A4
        
        # 如果成功注册了中文字体，设置字体
        if has_chinese_font:
            c.setFont('chinese', 12)  # 增大字号以提高可读性
        
        # 提取epub内容并转换为文本
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            html_content = item.get_content().decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            # 分页处理文本，按照中文标点符号分割
            text = text.replace('\n', '').replace('\r', '')
            sentences = []
            current_sentence = ''
            
            for char in text:
                current_sentence += char
                if char in '。！？，；：' or len(current_sentence) >= 40:  # 按照标点符号或固定长度分割
                    sentences.append(current_sentence)
                    current_sentence = ''
            
            if current_sentence:  # 添加最后一个句子
                sentences.append(current_sentence)
            
            # 写入PDF
            y = height - 50
            for sentence in sentences:
                if y < 50:  # 如果页面空间不足，创建新页面
                    c.showPage()
                    if has_chinese_font:  # 新页面也需要设置字体
                        c.setFont('chinese', 12)
                    y = height - 50
                
                # 使用UTF-8编码确保中文正确显示
                c.drawString(50, y, sentence)
                y -= 20  # 增加行间距
            
            c.showPage()
        
        c.save()
        
        return str(pdf_path)
    except Exception as e:
        print(f"转换文件 {epub_path} 时出错: {str(e)}")
        return None

def batch_convert(input_path, output_dir=None):
    """批量转换epub文件为pdf
    
    Args:
        input_path: 输入路径（文件或目录）
        output_dir: 输出目录
    """
    input_path = Path(input_path)
    
    # 收集所有epub文件
    epub_files = []
    if input_path.is_file() and input_path.suffix.lower() == '.epub':
        epub_files.append(input_path)
    elif input_path.is_dir():
        epub_files.extend(input_path.glob('**/*.epub'))
    
    if not epub_files:
        print("未找到epub文件")
        return
    
    # 批量转换
    print(f"找到 {len(epub_files)} 个epub文件")
    for epub_file in tqdm(epub_files, desc="转换进度"):
        pdf_path = convert_epub_to_pdf(epub_file, output_dir)
        if pdf_path:
            tqdm.write(f"已转换: {epub_file.name} -> {Path(pdf_path).name}")

def select_folder(title):
    """打开文件夹选择对话框
    
    Args:
        title: 对话框标题
    
    Returns:
        选择的文件夹路径，如果用户取消则返回None
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory(title=title)
    return folder_path if folder_path else None

def main():
    # 选择输入文件夹
    input_path = select_folder("选择包含EPUB文件的文件夹")
    if not input_path:
        print("未选择输入文件夹，程序退出")
        sys.exit(0)
    
    # 选择输出文件夹
    output_dir = select_folder("选择PDF文件保存位置")
    if not output_dir:
        print("未选择输出文件夹，程序退出")
        sys.exit(0)
    
    if not os.path.exists(input_path):
        print(f"错误：输入路径 {input_path} 不存在")
        sys.exit(1)
    
    batch_convert(input_path, output_dir)

if __name__ == '__main__':
    main()