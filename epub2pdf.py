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
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from functools import partial

# 全局变量用于缓存字体注册状态
_font_registered = False
_registered_font_path = None

# 注册中文字体
def register_chinese_font():
    global _font_registered, _registered_font_path
    
    # 如果字体已注册，直接返回
    if _font_registered and _registered_font_path:
        try:
            # 验证字体是否可用
            pdfmetrics.getFont('chinese')
            return True
        except Exception:
            # 如果字体不可用，重置状态并继续注册
            _font_registered = False
            _registered_font_path = None
    
    try:
        # 尝试使用系统自带的中文字体
        font_paths = []
        if sys.platform.startswith('darwin'):  # macOS
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/Hiragino Sans GB.ttc',
                '/System/Library/Fonts/STSong.ttc',
                '/System/Library/Fonts/Songti.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
                '/Library/Fonts/Microsoft/SimSong.ttf',
                '/Library/Fonts/Noto Sans CJK SC Regular.otf',
                '/Library/Fonts/Noto Sans CJK TC Regular.otf',
                '/Library/Fonts/Noto Sans CJK JP Regular.otf',
                '/Library/Fonts/Noto Sans CJK KR Regular.otf'
            ]
        elif sys.platform.startswith('win'):   # Windows
            font_paths = [
                'C:\\Windows\\Fonts\\msyh.ttc',
                'C:\\Windows\\Fonts\\simsun.ttc',
                'C:\\Windows\\Fonts\\simhei.ttf',
                'C:\\Windows\\Fonts\\simkai.ttf',
                'C:\\Windows\\Fonts\\simfang.ttf',
                'C:\\Windows\\Fonts\\msyhl.ttc',
                'C:\\Windows\\Fonts\\mingliub.ttc',
                'C:\\Windows\\Fonts\\malgun.ttf',  # 韩文
                'C:\\Windows\\Fonts\\msgothic.ttc',  # 日文
                'C:\\Windows\\Fonts\\batang.ttc'  # 韩文
            ]
        else:  # Linux
            font_paths = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/arphic/uming.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
                '/usr/share/fonts/truetype/arphic/ukai.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
                '/usr/share/fonts/truetype/takao/TakaoPGothic.ttf'
            ]
            
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    # 先检查字体是否已注册
                    try:
                        pdfmetrics.getFont('chinese')
                        _font_registered = True
                        _registered_font_path = font_path
                        return True
                    except Exception:
                        # 字体未注册，进行注册
                        pdfmetrics.registerFont(TTFont('chinese', font_path))
                        print(f"成功注册中文字体: {font_path}")
                        _font_registered = True
                        _registered_font_path = font_path
                        return True
                except Exception as font_error:
                    print(f"注册字体 {font_path} 失败: {str(font_error)}")
                    continue
        
        if not _font_registered:
            # 尝试使用系统默认字体
            try:
                from matplotlib.font_manager import findSystemFonts
                system_fonts = findSystemFonts()
                for font in system_fonts:
                    if any(keyword in font.lower() for keyword in ['song', 'ming', 'hei', 'kai', 'gothic', 'yuan', 'noto', 'cjk']):
                        try:
                            pdfmetrics.registerFont(TTFont('chinese', font))
                            print(f"成功注册系统字体: {font}")
                            _font_registered = True
                            _registered_font_path = font
                            return True
                        except:
                            continue
            except ImportError:
                pass
        
        if not _font_registered:
            print("警告：未找到合适的中文字体，文档可能无法正确显示中文")
            return False
        
        return True
    except Exception as e:
        print(f"注册中文字体失败: {str(e)}")
        return False

def process_chunk(chunk, font_info, pdf_canvas, width, height, margins):
    """处理文本块"""
    margin_left, margin_right, margin_top, margin_bottom = margins
    text_width = width - margin_left - margin_right
    y = height - margin_top
    
    has_chinese_font, font_name = font_info
    try:
        if has_chinese_font:
            pdf_canvas.setFont(font_name, 12)
        else:
            # 如果没有中文字体，使用默认字体
            pdf_canvas.setFont('Helvetica', 12)
    except Exception as e:
        print(f"设置字体失败: {str(e)}，使用默认字体")
        pdf_canvas.setFont('Helvetica', 12)
    
    soup = BeautifulSoup(chunk, 'html.parser')
    for script in soup(['script', 'style']):
        script.decompose()
    
    # 提取并处理文本内容，保持章节结构
    text_blocks = []
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
        tag_name = element.name
        text = element.get_text(strip=True)
        if text:
            text_blocks.append((tag_name, text))
    
    # 渲染文本内容
    base_line_height = 15  # 基础行高
    paragraph_spacing = 20  # 段落间距
    heading_spacing = 30   # 标题间距
    indent_size = 24       # 段落缩进
    
    for tag_name, text in text_blocks:
        try:
            # 根据标签类型设置不同的样式
            if tag_name.startswith('h'):
                heading_level = int(tag_name[1])
                font_size = max(12, 24 - (heading_level * 2))  # h1=24, h2=22, h3=20...
                pdf_canvas.setFont(font_name if has_chinese_font else 'Helvetica-Bold', font_size)
                y -= heading_spacing
            else:
                pdf_canvas.setFont(font_name if has_chinese_font else 'Helvetica', 12)
            
            # 处理长文本自动换行，针对中英文混合文本
            current_line = []
            current_width = indent_size if tag_name == 'p' else 0  # 段落首行缩进
            
            # 将文本按照中英文和标点符号分割
            text_parts = []
            temp = ''
            for char in text:
                # 判断字符类型（中文、英文、标点符号）
                is_cjk = ord(char) > 127
                is_punctuation = not char.isalnum() and not char.isspace()
                
                # 处理分割逻辑
                if is_cjk:
                    if temp:
                        text_parts.append(temp)
                        temp = ''
                    text_parts.append(char)
                elif is_punctuation:
                    if temp:
                        text_parts.append(temp)
                        temp = ''
                    text_parts.append(char)
                else:  # 英文和数字
                    if not temp or char.isspace() or (temp[-1].isspace()):
                        temp += char
                    elif (temp[-1].isalnum() and char.isalnum()):
                        temp += char
                    else:
                        text_parts.append(temp)
                        temp = char
            if temp:
                text_parts.append(temp)
            
            # 优化行宽计算和换行处理
            first_line = True
            for part in text_parts:
                try:
                    # 计算当前部分的宽度
                    part_width = pdf_canvas.stringWidth(part, pdf_canvas._fontname, pdf_canvas._fontsize)
                    
                    # 计算是否需要添加空格
                    need_space = False
                    if current_line and not part.isspace():
                        last_part = current_line[-1]
                        if (ord(last_part[-1]) <= 127 and ord(part[0]) <= 127) and \
                           (last_part[-1].isalnum() or part[0].isalnum()):
                            need_space = True
                    
                    space_width = pdf_canvas.stringWidth(' ', pdf_canvas._fontname, pdf_canvas._fontsize) if need_space else 0
                    total_width = current_width + part_width + space_width
                    
                    # 判断是否需要换行
                    if total_width <= text_width:
                        if need_space:
                            current_line.append(' ')
                        current_line.append(part)
                        current_width = total_width
                    else:
                        # 绘制当前行
                        if current_line:
                            line_text = ''.join(current_line)
                            x_pos = margin_left + (indent_size if first_line and tag_name == 'p' else 0)
                            pdf_canvas.drawString(x_pos, y, line_text)
                            y -= base_line_height * (1.5 if tag_name.startswith('h') else 1.2)
                            first_line = False
                        # 开始新行
                        current_line = [part]
                        current_width = part_width
                except Exception as e:
                    print(f"处理单词宽度时出错: {str(e)}")
                    continue
            
            # 绘制最后一行
            if current_line:
                try:
                    line_text = ''.join(current_line)
                    x_pos = margin_left + (indent_size if first_line and tag_name == 'p' else 0)
                    pdf_canvas.drawString(x_pos, y, line_text)
                    # 根据标签类型添加不同的间距
                    if tag_name.startswith('h'):
                        y -= heading_spacing
                    else:
                        y -= paragraph_spacing
                except Exception as e:
                    print(f"绘制文本行时出错: {str(e)}")
            
            # 检查是否需要新页面
            if y < margin_bottom:
                pdf_canvas.showPage()
                y = height - margin_top
                try:
                    if tag_name.startswith('h'):
                        pdf_canvas.setFont(font_name if has_chinese_font else 'Helvetica-Bold', font_size)
                    else:
                        pdf_canvas.setFont(font_name if has_chinese_font else 'Helvetica', 12)
                except Exception as e:
                    print(f"设置新页面字体失败: {str(e)}，使用默认字体")
                    pdf_canvas.setFont('Helvetica', 12)
        except Exception as e:
            print(f"处理文本块时出错: {str(e)}")
            continue
    
    return y

def convert_epub_to_pdf(epub_path, output_dir=None):
    try:
        # 确保在子进程中重新注册字体
        if not _font_registered:
            register_chinese_font()
        
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
        margins = (50, 50, 50, 50)  # left, right, top, bottom
        
        # 获取字体信息并确保字体已注册
        font_info = (_font_registered, 'chinese' if _font_registered else 'Helvetica')
        
        # 提取epub内容并分块处理
        chunk_size = 1024 * 1024  # 1MB per chunk
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                content = item.get_content()
                # 尝试多种编码
                encodings = ['utf-8', 'utf-16', 'gbk', 'gb2312', 'big5', 'shift-jis', 'euc-jp', 'euc-kr']
                html_content = None
                
                for encoding in encodings:
                    try:
                        html_content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if html_content is None:
                    html_content = content.decode('utf-8', errors='replace')
                
                # 分块处理内容
                chunks = [html_content[i:i+chunk_size] 
                         for i in range(0, len(html_content), chunk_size)]
                
                y = height - margins[2]  # 初始y坐标
                for chunk in chunks:
                    y = process_chunk(chunk, font_info, c, width, height, margins)
                    if y < margins[3]:
                        c.showPage()
                        y = height - margins[2]
                
            except Exception as e:
                print(f"处理文档内容时出错: {str(e)}")
                continue
            
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
    # 在主进程中注册字体
    register_chinese_font()
    
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
    
    # 使用进程池并行处理文件
    max_workers = max(1, multiprocessing.cpu_count() - 1)  # 保留一个CPU核心
    print(f"找到 {len(epub_files)} 个epub文件，使用 {max_workers} 个进程并行处理")
    
    # 确保每个子进程都能访问到字体信息
    multiprocessing.set_start_method('spawn', force=True)
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 创建带有固定output_dir参数的转换函数
        convert_func = partial(convert_epub_to_pdf, output_dir=output_dir)
        
        # 使用tqdm显示总体进度
        results = list(tqdm(
            executor.map(convert_func, epub_files),
            total=len(epub_files),
            desc="转换进度"
        ))
        
        # 输出转换结果
        for epub_file, pdf_path in zip(epub_files, results):
            if pdf_path:
                print(f"已转换: {epub_file.name} -> {Path(pdf_path).name}")
            else:
                print(f"转换失败: {epub_file.name}")

def select_input_path():
    """打开文件选择对话框，支持选择单个epub文件或文件夹
    
    Returns:
        选择的文件或文件夹路径，如果用户取消则返回None
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 创建选择窗口
    dialog = tk.Toplevel(root)
    dialog.title("选择EPUB文件或文件夹")
    dialog.geometry("300x150")
    dialog.resizable(False, False)
    
    selected_path = [None]  # 使用列表存储选择的路径，方便在回调函数中修改
    
    def select_file():
        file_path = filedialog.askopenfilename(
            title="选择EPUB文件",
            filetypes=[("EPUB文件", "*.epub")]
        )
        if file_path:
            selected_path[0] = file_path
            dialog.destroy()
    
    def select_folder():
        folder_path = filedialog.askdirectory(title="选择包含EPUB文件的文件夹")
        if folder_path:
            selected_path[0] = folder_path
            dialog.destroy()
    
    def on_cancel():
        dialog.destroy()
    
    # 创建按钮
    tk.Button(dialog, text="选择单个EPUB文件", command=select_file).pack(pady=10)
    tk.Button(dialog, text="选择文件夹", command=select_folder).pack(pady=10)
    tk.Button(dialog, text="取消", command=on_cancel).pack(pady=10)
    
    # 设置窗口位置居中
    dialog.transient(root)
    dialog.grab_set()
    root.eval(f'tk::PlaceWindow {dialog} center')
    
    # 等待窗口关闭
    dialog.wait_window()
    return selected_path[0]

def select_output_folder():
    """打开文件夹选择对话框选择输出目录
    
    Returns:
        选择的文件夹路径，如果用户取消则返回None
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory(title="选择PDF文件保存位置")
    return folder_path if folder_path else None

def main():
    # 在程序启动时注册字体
    register_chinese_font()
    
    # 选择输入文件或文件夹
    input_path = select_input_path()
    if not input_path:
        print("未选择输入文件或文件夹，程序退出")
        sys.exit(0)
    
    # 选择输出文件夹
    output_dir = select_output_folder()
    if not output_dir:
        print("未选择输出文件夹，程序退出")
        sys.exit(0)
    
    if not os.path.exists(input_path):
        print(f"错误：输入路径 {input_path} 不存在")
        sys.exit(1)
    
    batch_convert(input_path, output_dir)

if __name__ == '__main__':
    main()