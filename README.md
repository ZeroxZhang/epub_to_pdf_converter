# EPUB to PDF Converter

A user-friendly tool for converting EPUB e-books to PDF format, supporting batch conversion, Chinese character display, and graphical interface operation.

## Background

With the popularity of e-books, EPUB format has become one of the mainstream e-book formats due to its flexibility and openness. However, in certain scenarios (such as printing, archiving, and knowledge base indexing), PDF format might be more suitable. This tool aims to provide a simple solution to help users convert EPUB format e-books to PDF format while maintaining good Chinese language support.

## Features

- Graphical interface operation, easy to use
- Support batch conversion of multiple EPUB files
- Automatic recognition of system Chinese fonts
- Support for Windows, macOS and Linux systems
- Automatic pagination, maintaining reading experience
- Conversion progress display

## Requirements

- Python 3.6 or higher version
- Chinese fonts installed in the system

## Installation

1. Clone or download this project locally

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the program:
   ```bash
   python epub2pdf.py
   ```

2. In the folder selection dialog that pops up:
   - First select the folder containing EPUB files
   - Then select the destination folder for saving PDF files

3. The program will automatically start conversion and display the conversion progress

## Notes

- Make sure Chinese fonts are installed in the system, otherwise Chinese content may not display correctly
- Converting large files may take some time
- It is recommended to backup original EPUB files before conversion

## Dependencies

- ebooklib: EPUB file parsing
- reportlab: PDF file generation
- beautifulsoup4: HTML content parsing
- tqdm: Progress bar display
- tkinter: Graphical interface support (Python standard library)

## Changelog

### 2025-02-12
- Fix: Resolved the issue of incomplete display of some Chinese characters
- Optimization: Improved PDF document layout format for better reading experience
- New: Support for selecting single EPUB file or entire folder for conversion

### 2025-02-11
- Launch: Launched the first version of the project

---

# EPUB转PDF工具

一个简单易用的EPUB电子书转PDF工具，支持批量转换、中文显示和图形界面操作。

## 项目背景

随着电子书的普及，EPUB格式因其灵活性和开放性成为了主流的电子书格式之一。然而，在某些场景下（如打印、存档、以及知识库索引等场景下），PDF格式可能更为适合。本工具旨在提供一个简单的解决方案，帮助用户将EPUB格式的电子书转换为PDF格式，同时保持良好的中文支持。

## 功能特点

- 图形界面操作，简单易用
- 支持批量转换多个EPUB文件
- 自动识别系统中文字体，确保中文正确显示
- 支持Windows、macOS和Linux系统
- 自动分页，保持阅读体验
- 转换进度显示

## 环境要求

- Python 3.6 或更高版本
- 系统安装有中文字体

## 安装步骤

1. 克隆或下载本项目到本地

2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. 运行程序：
   ```bash
   python epub2pdf.py
   ```

2. 在弹出的文件夹选择对话框中：
   - 首先选择包含EPUB文件的文件夹
   - 然后选择要保存PDF文件的目标文件夹

3. 程序会自动开始转换，并显示转换进度

## 注意事项

- 确保系统已安装中文字体，否则可能无法正确显示中文内容
- 转换大文件时可能需要等待一段时间
- 建议在转换前备份原始EPUB文件

## 依赖说明

- ebooklib: EPUB文件解析
- reportlab: PDF文件生成
- beautifulsoup4: HTML内容解析
- tqdm: 进度条显示
- tkinter: 图形界面支持（Python标准库）

## 更新日志

### 2025-02-12
- 修复：解决了部分中文字符显示不完整的问题
- 优化：改进了PDF文档的排版格式，提升阅读体验
- 新增：支持选择单个EPUB文件或整个文件夹进行转换

### 2025-02-11
- 上线：上线项目第一个版本