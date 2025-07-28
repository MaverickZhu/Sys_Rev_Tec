#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复语法错误脚本
"""

import os
import re
import subprocess


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


def fix_syntax_errors(file_path):
    """修复语法错误"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # 修复未终止的字符串字面量
            if '"""' in line:
                # 检查三引号是否成对
                count = line.count('"""')
                if count == 1 and not line.strip().endswith('"""'):
                    # 添加结束的三引号
                    line = line.rstrip() + '"""'

            # 修复单引号字符串
            if line.count('"') % 2 == 1 and not line.strip().startswith("#"):
                # 未终止的字符串
                if not line.strip().endswith('"'):
                    line = line.rstrip() + '"'

            # 修复中文括号
            line = line.replace("（", "(")
            line = line.replace("）", ")")

            # 修复意外缩进
            if line.strip() and i > 0:
                prev_line = lines[i - 1].strip() if i > 0 else ""

                # 如果前一行不是以冒号结尾，当前行不应该有额外缩进
                if (
                    not prev_line.endswith(":")
                    and line.startswith("    ")
                    and not line.strip().startswith(("@", "#"))
                ):
                    # 检查是否应该在顶级
                    if line.strip().startswith(
                        ("import ", "from ", "class ", "def ", "async def ")
                    ):
                        line = line.lstrip()

            fixed_lines.append(line)

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fixed_lines))
            if fixed_lines and fixed_lines[-1].strip():
                f.write("\n")

        return True
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False


def fix_vector_schema():
    """专门修复vector.py的重复定义问题"""
    file_path = "app/schemas/vector.py"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        fixed_lines = []
        config_count = 0
        status_count = 0

        for line in lines:
            # 跳过重复的Config类定义
            if line.strip() == "class Config:":
                config_count += 1
                if config_count > 1:
                    continue

            # 跳过重复的status定义
            if "status =" in line and "status" in line:
                status_count += 1
                if status_count > 1:
                    continue

            # 修复过度缩进
            if line.startswith("        ") and not line.strip().startswith("#"):
                # 减少缩进
                line = "    " + line.lstrip()

            fixed_lines.append(line)

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fixed_lines))
            if fixed_lines and fixed_lines[-1].strip():
                f.write("\n")

        return True
    except Exception as e:
        print(f"修复vector.py时出错: {e}")
        return False


def main():
    """主函数"""
    print("开始修复语法错误...")

    # 获取有E999错误的文件
    flake8_output = run_flake8()
    error_files = set()

    if flake8_output:
        for line in flake8_output.split("\n"):
            if "E999" in line:
                parts = line.split(":")
                if len(parts) >= 1:
                    file_path = parts[0].strip()
                    error_files.add(file_path)

    print(f"找到 {len(error_files)} 个有语法错误的文件")

    # 修复每个文件
    for file_path in error_files:
        print(f"修复文件: {file_path}")
        fix_syntax_errors(file_path)

    # 专门修复vector.py
    print("修复vector.py的重复定义问题...")
    fix_vector_schema()

    # 最终检查
    print("\n最终检查...")
    final_output = run_flake8()

    if final_output:
        lines = final_output.strip().split("\n")
        error_count = len([line for line in lines if line.strip()])
        print(f"剩余问题数量: {error_count}")

        if error_count > 0:
            print("\n前10个剩余问题:")
            for line in lines[:10]:
                if line.strip():
                    print(f"  {line}")
        else:
            print("🎉 所有语法错误已修复！")
    else:
        print("🎉 所有语法错误已修复！")


if __name__ == "__main__":
    main()
