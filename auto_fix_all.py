#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复代码质量问题的脚本
"""

import os
import re
import subprocess
from pathlib import Path


def run_flake8():
    """运行flake8并返回结果"""
    try:
        result = subprocess.run(
            ["flake8", "app/", "--max-line-length=79"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        return result.stdout
    except Exception as e:
        print(f"运行flake8时出错: {e}")
        return ""


def fix_indentation_errors(file_path):
    """修复缩进错误"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        for i, line in enumerate(lines):
            # 移除行尾空白
            line = line.rstrip() + "\n" if line.strip() else "\n"

            # 修复常见的缩进问题
            if line.strip():
                # 计算当前行的缩进
                indent = len(line) - len(line.lstrip())

                # 如果是类或函数定义，确保正确缩进
                if re.match(r"^\s*(class|def|async def)\s+", line):
                    # 顶级定义应该没有缩进或4的倍数缩进
                    if indent % 4 != 0:
                        correct_indent = (indent // 4) * 4
                        line = " " * correct_indent + line.lstrip()

                # 修复import语句的缩进
                elif re.match(r"^\s*(import|from)\s+", line):
                    if indent > 0 and indent % 4 != 0:
                        line = line.lstrip() + "\n"

                # 修复装饰器的缩进
                elif re.match(r"^\s*@", line):
                    if indent % 4 != 0:
                        correct_indent = (indent // 4) * 4
                        line = " " * correct_indent + line.lstrip()

            fixed_lines.append(line)

        # 确保文件以换行符结尾
        if fixed_lines and not fixed_lines[-1].endswith("\n"):
            fixed_lines[-1] += "\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False


def fix_string_literals(file_path):
    """修复字符串字面量问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 修复未终止的字符串（简单情况）
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            # 检查是否有未终止的字符串
            if '"' in line:
                # 计算引号数量
                quote_count = line.count('"') - line.count('\\"')
                if quote_count % 2 != 0:
                    # 如果引号数量是奇数，可能有未终止的字符串
                    # 简单修复：在行尾添加引号
                    if not line.rstrip().endswith('"'):
                        line = line.rstrip() + '"'

            fixed_lines.append(line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fixed_lines))

        return True
    except Exception as e:
        print(f"修复字符串字面量 {file_path} 时出错: {e}")
        return False


def main():
    """主函数"""
    print("开始自动修复代码质量问题...")

    # 获取所有Python文件
    python_files = []
    for root, dirs, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    print(f"找到 {len(python_files)} 个Python文件")

    # 修复每个文件
    fixed_count = 0
    for file_path in python_files:
        print(f"修复文件: {file_path}")

        # 修复缩进错误
        if fix_indentation_errors(file_path):
            fixed_count += 1

        # 修复字符串字面量问题
        fix_string_literals(file_path)

    print(f"\n修复完成！处理了 {fixed_count} 个文件")

    # 再次运行flake8检查结果
    print("\n重新检查代码质量...")
    flake8_output = run_flake8()

    if flake8_output:
        lines = flake8_output.strip().split("\n")
        error_count = len([line for line in lines if line.strip()])
        print(f"剩余问题数量: {error_count}")

        if error_count > 0:
            print("\n前10个剩余问题:")
            for line in lines[:10]:
                if line.strip():
                    print(f"  {line}")
    else:
        print("没有发现代码质量问题！")


if __name__ == "__main__":
    main()
