#!/usr/bin/env python3
"""
语法错误修复脚本 - 专门处理E999语法错误
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple


def run_flake8() -> List[str]:
    """运行flake8并返回问题列表"""
    try:
        result = subprocess.run(
            ["flake8", "app/", "--max-line-length=79"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except Exception as e:
        print(f"运行flake8失败: {e}")
        return []


def parse_flake8_output(lines: List[str]) -> List[Tuple[str, int, str, str]]:
    """解析flake8输出"""
    issues = []
    for line in lines:
        if not line.strip():
            continue

        match = re.match(r"^([^:]+):(\d+):(\d+): ([A-Z]\d+) (.+)$", line)
        if match:
            file_path, line_num, col, code, message = match.groups()
            issues.append((file_path, int(line_num), code, message))

    return issues


def fix_syntax_errors_comprehensive(content: str) -> str:
    """全面修复语法错误"""
    lines = content.split("\n")
    fixed_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # 修复错误的缩进（类定义前的意外缩进）
        if line.lstrip().startswith("class ") and line.startswith("    "):
            # 类定义不应该有缩进（除非在函数内部）
            fixed_lines.append(line.lstrip())
            i += 1
            continue

        # 修复错误的元组语法
        if re.search(r"code\s*=\s*\(\s*\d+,\s*message\s*=", line):
            # 这是错误的语法: code = (200, message="...", data=...)
            # 应该改为字典或分开赋值
            indent = " " * (len(line) - len(line.lstrip()))

            # 提取参数
            match = re.search(
                r'code\s*=\s*\(\s*(\d+),\s*message\s*=\s*"([^"]*)",\s*data\s*=\s*(.+)\)',
                line,
            )
            if match:
                code_val, message_val, data_val = match.groups()
                # 重构为正确的语法
                fixed_lines.append(f"{indent}code={code_val},")
                fixed_lines.append(f'{indent}message="{message_val}",')
                fixed_lines.append(f"{indent}data={data_val}")
                i += 1
                continue

        # 修复错误的data赋值语法
        if re.search(r"data\s*=\s*\(\s*\{", line):
            # data = ({...}, ) 这种语法是错误的
            match = re.search(r"data\s*=\s*\(\s*(\{.+\}),?\s*\)", line)
            if match:
                data_content = match.group(1)
                indent = " " * (len(line) - len(line.lstrip()))
                fixed_lines.append(f"{indent}data={data_content}")
                i += 1
                continue

        # 修复未终止的字符串字面量
        if "\\" in line and not line.rstrip().endswith("\\"):
            # 检查是否是错误的字符串连接
            if re.search(r'f".*\\\s*$', line):
                # f"string\ 这种格式是错误的
                # 应该是 f"string" \
                fixed_line = line.replace("\\", '" \\')
                fixed_lines.append(fixed_line)
                i += 1
                continue

        # 修复错误的缩进（函数定义等）
        if line.strip() and not line.startswith(" ") and i > 0:
            prev_line = fixed_lines[-1] if fixed_lines else ""
            # 如果前一行是装饰器或函数定义的一部分，当前行可能需要缩进
            if (
                prev_line.strip().endswith(",")
                or prev_line.strip().endswith("(")
                or (
                    prev_line.strip().startswith("@")
                    and not line.strip().startswith(("def ", "async def ", "class "))
                )
            ):

                # 计算正确的缩进
                if prev_line.strip().startswith("@"):
                    # 装饰器后应该是函数定义，不需要额外缩进
                    if line.strip().startswith(("def ", "async def ", "class ")):
                        fixed_lines.append(line)
                    else:
                        # 可能是多行装饰器
                        base_indent = len(prev_line) - len(prev_line.lstrip())
                        fixed_lines.append(" " * base_indent + line.lstrip())
                else:
                    # 多行结构的续行
                    base_indent = len(prev_line) - len(prev_line.lstrip())
                    fixed_lines.append(" " * (base_indent + 4) + line.lstrip())
                i += 1
                continue

        # 修复错误的health赋值
        if "health = cache_service.health_check()" in line and line.startswith("    "):
            # 检查缩进是否正确
            # 找到正确的缩进级别
            correct_indent = 8  # 在try块内部
            content = line.lstrip()
            fixed_lines.append(" " * correct_indent + content)
            i += 1
            continue

        fixed_lines.append(line)
        i += 1

    return "\n".join(fixed_lines)


def fix_specific_syntax_issues(content: str) -> str:
    """修复特定的语法问题"""
    # 修复错误的ResponseModel调用
    content = re.sub(
        r'return ResponseModel\(\s*code\s*=\s*\(\s*(\d+),\s*message\s*=\s*"([^"]*)",\s*data\s*=\s*([^)]+)\)\s*\)',
        r'return ResponseModel(\n            code=\1,\n            message="\2",\n            data=\3\n        )',
        content,
        flags=re.MULTILINE | re.DOTALL,
    )

    # 修复错误的data赋值
    content = re.sub(r"data\s*=\s*\(\s*(\{[^}]+\}),?\s*\)", r"data=\1", content)

    # 修复错误的字符串连接
    content = re.sub(
        r'f"([^"]*)\\\\\s*\n\s*([^"]*)"', r'f"\1\2"', content, flags=re.MULTILINE
    )

    return content


def fix_file_syntax(file_path: str) -> int:
    """修复文件的语法错误"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 应用修复
        content = fix_syntax_errors_comprehensive(content)
        content = fix_specific_syntax_issues(content)

        # 最终清理
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            # 移除行尾空白
            line = line.rstrip()
            fixed_lines.append(line)

        # 移除文件末尾多余的空行
        while fixed_lines and not fixed_lines[-1].strip():
            fixed_lines.pop()

        # 确保文件以换行符结尾
        if fixed_lines:
            fixed_lines.append("")

        new_content = "\n".join(fixed_lines)

        if new_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return 1

        return 0

    except Exception as e:
        print(f"修复文件 {file_path} 失败: {e}")
        return 0


def main():
    """主函数"""
    print("开始语法错误修复...")

    # 获取所有E999问题
    flake8_output = run_flake8()
    if not flake8_output:
        print("没有发现代码质量问题")
        return

    issues = parse_flake8_output(flake8_output)
    e999_issues = [(f, l, c, m) for f, l, c, m in issues if c == "E999"]

    if not e999_issues:
        print("没有发现E999语法错误")
        return

    print(f"发现 {len(e999_issues)} 个E999语法错误")

    # 获取需要修复的文件列表
    files_to_fix = set()
    for file_path, line_num, code, message in e999_issues:
        files_to_fix.add(file_path)

    total_fixed = 0

    # 修复每个文件
    for file_path in sorted(files_to_fix):
        print(f"修复文件: {file_path}")
        fixed_count = fix_file_syntax(file_path)
        if fixed_count > 0:
            print(f"  ✓ 文件已修复")
            total_fixed += fixed_count
        else:
            print(f"  - 无需修复")

    print(f"\n修复完成！共修复了 {total_fixed} 个文件")

    # 再次检查剩余问题
    print("\n检查剩余E999问题...")
    remaining_issues = run_flake8()
    if remaining_issues:
        remaining_parsed = parse_flake8_output(remaining_issues)
        remaining_e999 = [
            (f, l, c, m) for f, l, c, m in remaining_parsed if c == "E999"
        ]

        if remaining_e999:
            print(f"还有 {len(remaining_e999)} 个E999问题")
            print("\n剩余E999问题:")
            for file_path, line_num, code, message in remaining_e999[:10]:
                print(f"  {file_path}:{line_num}: {code} {message}")
        else:
            print("🎉 所有E999语法错误已修复！")

            # 显示总体剩余问题统计
            total_remaining = len(remaining_parsed)
            if total_remaining > 0:
                issue_types = {}
                for _, _, code, _ in remaining_parsed:
                    issue_types[code] = issue_types.get(code, 0) + 1

                print(f"\n总共还有 {total_remaining} 个其他问题:")
                for code, count in sorted(issue_types.items()):
                    print(f"  {code}: {count} 个")
    else:
        print("🎉 所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
