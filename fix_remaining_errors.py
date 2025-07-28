#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复剩余的语法错误
"""

import os
import re
import subprocess
from pathlib import Path


def run_flake8():
    """运行flake8检查"""
    try:
        result = subprocess.run(
            ["flake8", "app/", "--max-line-length=79"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout
    except UnicodeDecodeError:
        # 如果有编码问题，尝试使用gbk
        try:
            result = subprocess.run(
                ["flake8", "app/", "--max-line-length=79"],
                capture_output=True,
                text=True,
                encoding="gbk",
            )
            return result.stdout
        except Exception as e:
            print(f"Error running flake8: {e}")
            return ""


def fix_file_encoding_and_syntax(file_path):
    """修复文件编码和语法错误"""
    try:
        # 尝试不同的编码读取文件
        content = None
        for encoding in ["utf-8", "gbk", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            print(f"Cannot read file {file_path}")
            return False

        original_content = content

        # 修复中文括号
        content = content.replace("（", "(")
        content = content.replace("）", ")")
        content = content.replace("，", ",")
        content = content.replace("：", ":")
        content = content.replace("；", ";")

        # 修复未终止的字符串字面量
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # 检查是否有未闭合的字符串
            if '"""' in line:
                # 处理三引号字符串
                quote_count = line.count('"""')
                if quote_count % 2 == 1:  # 奇数个三引号
                    # 查找下一个三引号或添加一个
                    found_closing = False
                    for j in range(i + 1, len(lines)):
                        if '"""' in lines[j]:
                            found_closing = True
                            break
                    if not found_closing:
                        line += '"""'

            # 修复单引号和双引号
            if line.strip() and not line.strip().startswith("#"):
                # 简单的引号修复
                if line.count('"') % 2 == 1 and not line.strip().endswith("\\"):
                    if not any(x in line for x in ['"""', "'''"]):
                        line += '"'

                if line.count("'") % 2 == 1 and not line.strip().endswith("\\"):
                    if not any(x in line for x in ['"""', "'''"]):
                        line += "'"

            fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        # 修复缩进问题
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # 移除行尾空白
            line = line.rstrip()

            # 修复缩进
            if line.strip():
                # 将tab转换为4个空格
                line = line.expandtabs(4)

                # 检查是否是续行
                if i > 0 and lines[i - 1].strip().endswith(("(", "[", "{", "\\", ",")):
                    # 续行应该有适当的缩进
                    if line.strip() and not line.startswith(" "):
                        # 添加适当的缩进
                        prev_indent = len(lines[i - 1]) - len(lines[i - 1].lstrip())
                        line = " " * (prev_indent + 4) + line.strip()

            fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def fix_cache_service():
    """修复cache_service.py的特定问题"""
    file_path = "app/services/cache_service.py"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 修复空白行包含空格的问题
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            # 移除只包含空格的行
            if line.strip() == "":
                fixed_lines.append("")
            else:
                fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        # 修复续行缩进问题
        content = content.replace(
            '                    logger.error(f"Failed to deserialize pickle cache "\n                                f"{key}: {e}")',
            '                    logger.error(f"Failed to deserialize pickle cache "\n                                 f"{key}: {e}")',
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Fixed cache_service.py")

    except Exception as e:
        print(f"Error fixing cache_service.py: {e}")


def main():
    """主函数"""
    print("开始修复剩余的语法错误...")

    # 获取所有需要修复的文件
    error_files = [
        "app/services/document_service.py",
        "app/services/ocr_service.py",
        "app/utils/ai_integration.py",
        "app/utils/cache.py",
        "app/utils/cache_decorator.py",
        "app/utils/knowledge_graph.py",
        "app/utils/text_processing.py",
        "app/utils/vector_service.py",
        "app/schemas/vector.py",
    ]

    # 修复每个文件
    for file_path in error_files:
        if os.path.exists(file_path):
            fix_file_encoding_and_syntax(file_path)

    # 特别修复cache_service.py
    fix_cache_service()

    print("\n修复完成，重新运行flake8检查...")

    # 重新运行flake8
    output = run_flake8()
    if output:
        print("剩余错误:")
        print(output)
    else:
        print("所有语法错误已修复！")


if __name__ == "__main__":
    main()
