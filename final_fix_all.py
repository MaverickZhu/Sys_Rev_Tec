#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复所有代码质量问题
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


def fix_blank_lines_and_indentation(file_path):
    """修复空行和缩进问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 移除行尾空白
            line = line.rstrip() + "\n" if line.strip() else "\n"

            # 处理import语句
            if re.match(r"^\s*(import|from)\s+", line):
                line = line.lstrip() + "\n"
                fixed_lines.append(line)

            # 处理装饰器
            elif re.match(r"^\s*@", line):
                # 装饰器前确保有适当的空行
                if fixed_lines and fixed_lines[-1].strip() != "":
                    # 如果前面不是空行，添加空行
                    if not re.match(r"^\s*(class|def|async def)", fixed_lines[-1]):
                        fixed_lines.append("\n")
                        fixed_lines.append("\n")

                # 添加装饰器
                fixed_lines.append(line.lstrip() + "\n")

                # 处理装饰器后的内容
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if re.match(r"^\s*@", next_line):
                        # 另一个装饰器
                        fixed_lines.append(next_line.lstrip() + "\n")
                        j += 1
                    elif next_line.strip() == "":
                        # 跳过装饰器后的空行
                        j += 1
                    elif re.match(r"^\s*(def|class|async def)", next_line):
                        # 函数或类定义
                        fixed_lines.append(next_line.lstrip() + "\n")
                        i = j
                        break
                    else:
                        break

            # 处理函数和类定义
            elif re.match(r"^\s*(def|class|async def)\s+", line):
                # 确保前面有2个空行（除非是文件开头或在类内部）
                if fixed_lines:
                    # 移除多余的空行
                    while fixed_lines and fixed_lines[-1].strip() == "":
                        fixed_lines.pop()

                    # 检查是否在类内部
                    in_class = False
                    for prev_line in reversed(fixed_lines):
                        if prev_line.strip().startswith("class "):
                            in_class = True
                            break
                        elif prev_line.strip().startswith(("def ", "async def ")):
                            break

                    if not in_class:
                        # 顶级定义前添加2个空行
                        fixed_lines.extend(["\n", "\n"])
                    else:
                        # 类内方法前添加1个空行
                        fixed_lines.append("\n")

                # 添加函数/类定义
                if line.strip().startswith("def ") and any(
                    "class " in prev_line
                    for prev_line in fixed_lines[-10:]
                    if prev_line.strip()
                ):
                    # 类内方法缩进4个空格
                    fixed_lines.append("    " + line.lstrip())
                else:
                    # 顶级定义不缩进
                    fixed_lines.append(line.lstrip() + "\n")

            # 处理其他行
            else:
                # 修复意外的缩进
                if (
                    line.strip()
                    and not line.startswith("    ")
                    and not line.startswith("\t")
                ):
                    # 检查是否应该缩进
                    should_indent = False
                    for j in range(len(fixed_lines) - 1, -1, -1):
                        prev_line = fixed_lines[j].strip()
                        if prev_line:
                            if prev_line.startswith(
                                (
                                    "def ",
                                    "class ",
                                    "if ",
                                    "for ",
                                    "while ",
                                    "try:",
                                    "except",
                                    "with ",
                                )
                            ):
                                should_indent = True
                            break

                    if should_indent and not line.strip().startswith(
                        ("def ", "class ", "import ", "from ")
                    ):
                        line = "    " + line.lstrip()
                    else:
                        line = line.lstrip() + "\n"

                fixed_lines.append(line)

            i += 1

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
    print("开始最终修复...")

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
        if fix_blank_lines_and_indentation(file_path):
            fixed_count += 1

    print(f"\n修复完成！处理了 {fixed_count} 个文件")

    # 最终检查
    print("\n最终检查...")
    final_output = run_flake8()

    if final_output:
        lines = final_output.strip().split("\n")
        error_count = len([line for line in lines if line.strip()])
        print(f"剩余问题数量: {error_count}")

        if error_count > 0:
            print("\n剩余问题:")
            for line in lines[:20]:
                if line.strip():
                    print(f"  {line}")
        else:
            print("🎉 所有代码质量问题已修复！")
    else:
        print("🎉 所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
