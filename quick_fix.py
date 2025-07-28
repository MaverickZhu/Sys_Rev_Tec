#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复剩余的缩进错误
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


def fix_file_indentation(file_path):
    """修复文件的缩进问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        for i, line in enumerate(lines):
            # 移除行尾空白
            line = line.rstrip() + "\n" if line.strip() else "\n"

            if line.strip():
                # 计算当前行的缩进
                indent = len(line) - len(line.lstrip())

                # 修复import语句 - 应该在顶层
                if re.match(r"^\s*(import|from)\s+", line):
                    line = line.lstrip() + "\n"

                # 修复类和函数定义的缩进
                elif re.match(r"^\s*(class|def|async def)\s+", line):
                    # 检查是否在类内部
                    in_class = False
                    for j in range(i - 1, -1, -1):
                        prev_line = lines[j].strip()
                        if prev_line.startswith("class "):
                            in_class = True
                            break
                        elif prev_line.startswith("def ") or prev_line.startswith(
                            "async def "
                        ):
                            break

                    if in_class and line.strip().startswith("def "):
                        # 类内方法应该缩进4个空格
                        line = "    " + line.lstrip()
                    elif not in_class:
                        # 顶级定义不应该缩进
                        line = line.lstrip() + "\n"

                # 修复装饰器的缩进
                elif re.match(r"^\s*@", line):
                    # 装饰器应该与其装饰的函数/类有相同的缩进
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if re.match(r"^\s*(def|class|async def)", next_line):
                            next_indent = len(next_line) - len(next_line.lstrip())
                            line = " " * next_indent + line.lstrip()

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


def main():
    """主函数"""
    print("开始快速修复缩进错误...")

    # 获取有E999错误的文件列表
    flake8_output = run_flake8()
    error_files = set()

    for line in flake8_output.strip().split("\n"):
        if "E999" in line and line.strip():
            file_path = line.split(":")[0]
            error_files.add(file_path)

    print(f"发现 {len(error_files)} 个有E999错误的文件")

    # 修复每个文件
    fixed_count = 0
    for file_path in error_files:
        print(f"修复文件: {file_path}")
        if fix_file_indentation(file_path):
            fixed_count += 1

    print(f"\n修复完成！处理了 {fixed_count} 个文件")

    # 再次检查
    print("\n重新检查...")
    final_output = run_flake8()

    if final_output:
        lines = final_output.strip().split("\n")
        error_count = len([line for line in lines if line.strip()])
        print(f"剩余问题数量: {error_count}")

        if error_count > 0:
            print("\n前15个剩余问题:")
            for line in lines[:15]:
                if line.strip():
                    print(f"  {line}")
    else:
        print("🎉 所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
