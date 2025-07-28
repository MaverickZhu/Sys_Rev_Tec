#!/usr/bin/env python3
"""
最终修复脚本 - 处理所有剩余的代码质量问题
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict


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


def fix_syntax_errors(content: str) -> str:
    """修复常见的语法错误"""
    lines = content.split("\n")
    fixed_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 修复错误的赋值语句格式
        # 例如: code = (200, message="...", data={...})
        if re.search(r"code\s*=\s*\(\s*\d+,\s*message=", line):
            # 这种格式是错误的，应该分开
            match = re.search(
                r'code\s*=\s*\(\s*(\d+),\s*message="([^"]*)",\s*data=(.+)\)', line
            )
            if match:
                code_val, message_val, data_val = match.groups()
                indent = " " * (len(line) - len(line.lstrip()))
                fixed_lines.append(f"{indent}code={code_val},")
                fixed_lines.append(f'{indent}message="{message_val}",')
                fixed_lines.append(f"{indent}data={data_val}")
                continue

        # 修复多行参数的格式问题
        if line.strip().endswith(",") and i + 1 < len(lines):
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            # 检查下一行的缩进是否正确
            if next_line.strip() and not next_line.startswith(" "):
                # 下一行缩进不正确
                current_indent = len(line) - len(line.lstrip())
                next_content = next_line.lstrip()
                lines[i + 1] = " " * (current_indent + 4) + next_content

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def fix_hanging_indent_comprehensive(lines: List[str]) -> List[str]:
    """全面修复悬挂缩进问题"""
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 检查是否是函数定义或装饰器
        if (
            line.strip().startswith("@")
            or line.strip().startswith("def ")
            or line.strip().startswith("async def ")
        ):
            fixed_lines.append(line)
            i += 1
            continue

        # 检查是否是多行函数调用或参数列表的开始
        if (
            "(" in line and line.count("(") > line.count(")")
        ) or line.rstrip().endswith((",", "(")):
            # 这是一个多行结构的开始
            base_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1

            # 处理后续的行，直到找到匹配的结束
            paren_count = line.count("(") - line.count(")")
            bracket_count = line.count("[") - line.count("]")
            brace_count = line.count("{") - line.count("}")

            while i < len(lines) and (
                paren_count > 0
                or bracket_count > 0
                or brace_count > 0
                or lines[i - 1].rstrip().endswith(",")
            ):
                current_line = lines[i]

                if current_line.strip():
                    # 计算正确的缩进
                    if current_line.strip().startswith((")", "]", "}")):
                        # 结束符号，使用基础缩进
                        correct_indent = base_indent
                    else:
                        # 参数或内容，使用基础缩进 + 4
                        correct_indent = base_indent + 4

                    content = current_line.lstrip()
                    fixed_line = " " * correct_indent + content
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(current_line)

                # 更新括号计数
                paren_count += current_line.count("(") - current_line.count(")")
                bracket_count += current_line.count("[") - current_line.count("]")
                brace_count += current_line.count("{") - current_line.count("}")

                i += 1

                # 如果所有括号都匹配了，检查是否还有逗号
                if paren_count <= 0 and bracket_count <= 0 and brace_count <= 0:
                    if not current_line.rstrip().endswith(","):
                        break
        else:
            fixed_lines.append(line)
            i += 1

    return fixed_lines


def fix_decorator_spacing(lines: List[str]) -> List[str]:
    """修复装饰器后的空行问题"""
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("@"):
            # 这是一个装饰器
            fixed_lines.append(line)
            i += 1

            # 跳过装饰器后的空行
            while i < len(lines) and not lines[i].strip():
                i += 1

            # 确保装饰器后直接跟函数定义
            if i < len(lines):
                fixed_lines.append(lines[i])
                i += 1
        else:
            fixed_lines.append(line)
            i += 1

    return fixed_lines


def fix_file_final(file_path: str) -> int:
    """最终修复文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 1. 修复语法错误
        content = fix_syntax_errors(content)

        lines = content.split("\n")

        # 2. 修复悬挂缩进
        lines = fix_hanging_indent_comprehensive(lines)

        # 3. 修复装饰器空行
        lines = fix_decorator_spacing(lines)

        # 4. 修复其他格式问题
        fixed_lines = []
        for i, line in enumerate(lines):
            # 移除行尾空白
            line = line.rstrip()

            # 修复连续的空行
            if not line.strip():
                # 检查前面是否已经有空行
                if fixed_lines and not fixed_lines[-1].strip():
                    continue  # 跳过多余的空行

            fixed_lines.append(line)

        # 5. 确保文件以换行符结尾
        if fixed_lines and fixed_lines[-1]:
            fixed_lines.append("")

        # 写入修复后的内容
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
    print("开始最终修复...")

    # 获取所有问题
    flake8_output = run_flake8()
    if not flake8_output:
        print("没有发现代码质量问题")
        return

    issues = parse_flake8_output(flake8_output)
    print(f"发现 {len(issues)} 个问题")

    # 获取需要修复的文件列表
    files_to_fix = set()
    for file_path, line_num, code, message in issues:
        files_to_fix.add(file_path)

    total_fixed = 0

    # 修复每个文件
    for file_path in files_to_fix:
        print(f"修复文件: {file_path}")
        fixed_count = fix_file_final(file_path)
        if fixed_count > 0:
            print(f"  ✓ 文件已修复")
            total_fixed += fixed_count
        else:
            print(f"  - 无需修复")

    print(f"\n修复完成！共修复了 {total_fixed} 个文件")

    # 再次检查剩余问题
    print("\n检查剩余问题...")
    remaining_issues = run_flake8()
    if remaining_issues:
        remaining_parsed = parse_flake8_output(remaining_issues)
        remaining_count = len(remaining_parsed)
        print(f"还有 {remaining_count} 个问题")

        # 显示剩余问题的类型统计
        issue_types = {}
        for _, _, code, _ in remaining_parsed:
            issue_types[code] = issue_types.get(code, 0) + 1

        print("剩余问题类型统计:")
        for code, count in sorted(issue_types.items()):
            print(f"  {code}: {count} 个")

        if remaining_count <= 50:
            print("\n剩余问题详情:")
            for file_path, line_num, code, message in remaining_parsed:
                print(f"  {file_path}:{line_num}: {code} {message}")
    else:
        print("🎉 所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
