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
            
        registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('chinese', font_path))
                    print(f"成功注册中文字体: {font_path}")
                    registered = True
                    break
                except Exception as font_error:
                    print(f"注册字体 {font_path} 失败: {str(font_error)}")
                    continue
        
        if not registered:
            # 尝试使用系统默认字体
            try:
                from matplotlib.font_manager import findSystemFonts
                system_fonts = findSystemFonts()
                for font in system_fonts:
                    if any(keyword in font.lower() for keyword in ['song', 'ming', 'hei', 'kai', 'gothic', 'yuan', 'noto', 'cjk']):
                        try:
                            pdfmetrics.registerFont(TTFont('chinese', font))
                            print(f"成功注册系统字体: {font}")
                            registered = True
                            break
                        except:
                            continue
            except ImportError:
                pass
        
        if not registered:
            print("警告：未找到合适的中文字体，文档可能无法正确显示中文")
            return False
        
        return True
    except Exception as e:
        print(f"注册中文字体失败: {str(e)}")
        return False

def convert_epub_to_pdf(epub_path, output_dir=None):
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
        margin_left = 50
        margin_right = 50
        margin_top = 50
        margin_bottom = 50
        text_width = width - margin_left - margin_right
        
        # 设置基本字体和样式
        if has_chinese_font:
            c.setFont('chinese', 12)  # 正文字体
        
        # 提取epub内容并转换为文本
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                # 尝试多种编码方式
                content = item.get_content()
                encodings = ['utf-8', 'utf-16', 'gbk', 'gb2312', 'big5', 'shift-jis', 'euc-jp', 'euc-kr', 'iso-2022-jp', 'euc-kr']
                html_content = None
                
                for encoding in encodings:
                    try:
                        html_content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if html_content is None:
                    html_content = content.decode('utf-8', errors='replace')
                
                soup = BeautifulSoup(html_content, 'html.parser')
                # 移除script和style标签
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # 处理标题和段落
                y = height - margin_top
                for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span']):
                    # 获取文本内容和样式
                    text = element.get_text(strip=True)
                    if not text:
                        continue
                    
                    # 解析样式
                    style = element.get('style', '')
                    text_align = 'left'  # 默认左对齐
                    if 'text-align: center' in style:
                        text_align = 'center'
                    elif 'text-align: right' in style:
                        text_align = 'right'
                    
                    # 根据标签类型设置样式
                    if element.name.startswith('h'):
                        level = int(element.name[1])
                        font_size = 24 - (level * 2)  # h1=22, h2=20, h3=18, ...
                        if has_chinese_font:
                            c.setFont('chinese', font_size)
                        y -= font_size + 10  # 标题前增加额外空间
                        
                        # 处理标题对齐
                        if text_align == 'center':
                            c.drawCentredString(width/2, y, text)
                        elif text_align == 'right':
                            c.drawRightString(width - margin_right, y, text)
                        else:
                            c.drawString(margin_left, y, text)
                            
                        y -= font_size  # 标题后增加额外空间
                    else:  # 段落文本
                        if has_chinese_font:
                            c.setFont('chinese', 12)
                        
                        # 处理段落缩进
                        indent = 24  # 默认缩进两个中文字符
                        current_x = margin_left + indent
                        
                        # 分段处理长文本
                        words = []
                        # 对中文和非中文字符分别处理
                        current_word = ''
                        for char in text:
                            if ord(char) > 127:  # 中文字符
                                if current_word:
                                    words.append(current_word)
                                    current_word = ''
                                words.append(char)
                            else:  # 非中文字符
                                current_word += char
                        if current_word:
                            words.append(current_word)
                            
                        line = ''
                        first_line = True
                        
                        for word in words:
                            test_line = line + word
                            if line and not word.isspace():  # 如果不是第一个词且不是空格，添加空格
                                test_line = line + ' ' + word
                            
                            line_width = c.stringWidth(test_line, 'chinese' if has_chinese_font else None, 12)
                            
                            if line_width < text_width - (indent if first_line else 0):
                                line = test_line
                            else:
                                if y < margin_bottom + 20:  # 页面空间不足，创建新页面
                                    c.showPage()
                                    if has_chinese_font:
                                        c.setFont('chinese', 12)
                                    y = height - margin_top
                                
                                # 绘制当前行
                                x = current_x if first_line else margin_left
                                if text_align == 'center':
                                    c.drawCentredString(width/2, y, line)
                                elif text_align == 'right':
                                    c.drawRightString(width - margin_right, y, line)
                                else:
                                    c.drawString(x, y, line)
                                
                                y -= 20
                                line = word
                                first_line = False
                        
                        # 输出最后一行
                        if line:
                            if y < margin_bottom + 20:
                                c.showPage()
                                if has_chinese_font:
                                    c.setFont('chinese', 12)
                                y = height - margin_top
                            
                            x = current_x if first_line else margin_left
                            if text_align == 'center':
                                c.drawCentredString(width/2, y, line)
                            elif text_align == 'right':
                                c.drawRightString(width - margin_right, y, line)
                            else:
                                c.drawString(x, y, line)
                            y -= 20
                        
                        y -= 10  # 段落间额外间距
                    
                    # 检查是否需要新页面
                    if y < margin_bottom:
                        c.showPage()
                        if has_chinese_font:
                            c.setFont('chinese', 12)
                        y = height - margin_top
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