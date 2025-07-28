#!/usr/bin/env python3
"""
修复剩余的代码质量问题，专门针对E131和E501等问题
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


def fix_hanging_indent(lines: List[str], line_num: int) -> bool:
    """修复悬挂缩进问题 (E131)"""
    if line_num <= 0 or line_num > len(lines):
        return False

    line_idx = line_num - 1
    line = lines[line_idx]

    # 如果这行是空的或者只有空白字符，跳过
    if not line.strip():
        return False

    # 查找前一行来确定正确的缩进
    prev_line_idx = line_idx - 1
    while prev_line_idx >= 0 and not lines[prev_line_idx].strip():
        prev_line_idx -= 1

    if prev_line_idx < 0:
        return False

    prev_line = lines[prev_line_idx]

    # 如果前一行以 (, [, { 结尾，或者包含 = 且以逗号结尾
    if prev_line.rstrip().endswith(("(", "[", "{", ",")) or (
        "=" in prev_line and prev_line.rstrip().endswith(",")
    ):

        # 计算前一行的基础缩进
        prev_indent = len(prev_line) - len(prev_line.lstrip())

        # 悬挂缩进应该是基础缩进 + 4
        correct_indent = prev_indent + 4

        # 获取当前行的内容（去掉前导空白）
        content = line.lstrip()

        # 应用正确的缩进
        new_line = " " * correct_indent + content

        if new_line != line:
            lines[line_idx] = new_line
            return True

    # 处理函数调用的参数对齐
    elif "(" in prev_line and not prev_line.rstrip().endswith(")"):
        # 找到开括号的位置
        paren_pos = prev_line.rfind("(")
        if paren_pos != -1:
            # 对齐到开括号后的位置
            correct_indent = paren_pos + 1
            content = line.lstrip()
            new_line = " " * correct_indent + content

            if new_line != line and correct_indent > 0:
                lines[line_idx] = new_line
                return True

    return False


def fix_line_length_advanced(line: str, max_length: int = 79) -> str:
    """高级行长度修复"""
    if len(line) <= max_length:
        return line

    # 获取缩进
    indent = len(line) - len(line.lstrip())
    indent_str = " " * indent
    content = line.strip()

    # 策略1: 修复字符串连接
    if " + " in content and ('"' in content or "'" in content):
        # 分割字符串连接
        parts = content.split(" + ")
        if len(parts) > 1:
            new_line = indent_str + parts[0] + " + \\\n"
            for i, part in enumerate(parts[1:], 1):
                new_line += indent_str + "    " + part
                if i < len(parts) - 1:
                    new_line += " + \\\n"
            return new_line

    # 策略2: 修复长的条件语句
    if content.startswith(("if ", "elif ", "while ")) and (
        " and " in content or " or " in content
    ):
        # 分割条件
        for operator in [" and ", " or "]:
            if operator in content:
                keyword_part = content.split(operator)[0]
                remaining = content[len(keyword_part) :]
                conditions = remaining.split(operator)

                new_line = indent_str + keyword_part + operator.strip() + " \\\n"
                for i, condition in enumerate(conditions[1:], 1):
                    new_line += indent_str + "    " + condition.strip()
                    if i < len(conditions) - 1:
                        new_line += operator + "\\\n"
                return new_line

    # 策略3: 修复长的赋值语句
    if "=" in content and not content.startswith(("if", "elif", "while", "for")):
        eq_pos = content.find("=")
        var_part = content[:eq_pos].strip()
        value_part = content[eq_pos + 1 :].strip()

        if len(value_part) > 40:
            # 如果值部分很长，换行
            return f"{indent_str}{var_part} = (\n{indent_str}    {value_part}\n{indent_str})"

    # 策略4: 修复长的函数调用
    if "(" in content and ")" in content and "," in content:
        # 查找函数调用
        paren_start = content.find("(")
        paren_end = content.rfind(")")

        if paren_start != -1 and paren_end != -1 and paren_end > paren_start:
            func_part = content[:paren_start]
            params_part = content[paren_start + 1 : paren_end]
            after_part = content[paren_end + 1 :]

            if "," in params_part:
                params = [p.strip() for p in params_part.split(",")]
                if len(params) > 1:
                    new_line = f"{indent_str}{func_part}(\n"
                    for i, param in enumerate(params):
                        new_line += f"{indent_str}    {param}"
                        if i < len(params) - 1:
                            new_line += ",\n"
                        else:
                            new_line += f"\n{indent_str}){after_part}"
                    return new_line

    # 策略5: 修复长的导入语句
    if content.startswith("from ") and "import" in content and "," in content:
        import_pos = content.find("import")
        from_part = content[: import_pos + 6]  # 包含 'import'
        imports_part = content[import_pos + 6 :].strip()

        if "," in imports_part:
            imports = [imp.strip() for imp in imports_part.split(",")]
            if len(imports) > 2:
                new_line = f"{indent_str}{from_part} (\n"
                for i, imp in enumerate(imports):
                    new_line += f"{indent_str}    {imp}"
                    if i < len(imports) - 1:
                        new_line += ",\n"
                    else:
                        new_line += f"\n{indent_str})"
                return new_line

    # 策略6: 简单的在合适位置断行
    if len(line) > max_length:
        # 寻找合适的断行点
        break_points = []
        for i, char in enumerate(line):
            if char in " .,;" and i > max_length // 2:
                break_points.append(i)

        if break_points:
            # 选择最接近理想长度的断行点
            ideal_pos = max_length - 10
            best_pos = min(break_points, key=lambda x: abs(x - ideal_pos))

            if best_pos < len(line) - 10:  # 确保第二行不会太短
                part1 = line[: best_pos + 1].rstrip()
                part2 = line[best_pos + 1 :].lstrip()
                return f"{part1} \\\n{indent_str}    {part2}"

    return line


def fix_file_remaining_issues(
    file_path: str, issues: List[Tuple[int, str, str]]
) -> int:
    """修复文件中的剩余问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        fixed_count = 0

        # 按行号排序问题，从后往前处理避免行号偏移
        issues_by_line = {}
        for line_num, code, message in issues:
            if line_num not in issues_by_line:
                issues_by_line[line_num] = []
            issues_by_line[line_num].append((code, message))

        # 从后往前处理
        for line_num in sorted(issues_by_line.keys(), reverse=True):
            line_issues = issues_by_line[line_num]

            for code, message in line_issues:
                if code == "E131":  # 悬挂缩进问题
                    if fix_hanging_indent(lines, line_num):
                        fixed_count += 1

                elif code == "E501":  # 行过长问题
                    if line_num <= len(lines):
                        original_line = lines[line_num - 1]
                        new_line = fix_line_length_advanced(original_line)
                        if new_line != original_line:
                            lines[line_num - 1] = new_line
                            fixed_count += 1

                elif code in ["E122", "E124", "E128"]:  # 缩进问题
                    if line_num <= len(lines):
                        line = lines[line_num - 1]
                        if line.strip():  # 非空行
                            # 查找前一个非空行
                            prev_idx = line_num - 2
                            while prev_idx >= 0 and not lines[prev_idx].strip():
                                prev_idx -= 1

                            if prev_idx >= 0:
                                prev_line = lines[prev_idx]
                                prev_indent = len(prev_line) - len(prev_line.lstrip())

                                # 根据前一行调整缩进
                                if prev_line.rstrip().endswith((":")):
                                    correct_indent = prev_indent + 4
                                elif prev_line.rstrip().endswith(("(", "[", "{")):
                                    correct_indent = prev_indent + 4
                                else:
                                    correct_indent = prev_indent

                                content = line.lstrip()
                                new_line = " " * correct_indent + content

                                if new_line != line:
                                    lines[line_num - 1] = new_line
                                    fixed_count += 1

        # 写入修复后的内容
        new_content = "\n".join(lines)
        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

        return fixed_count

    except Exception as e:
        print(f"修复文件 {file_path} 失败: {e}")
        return 0


def main():
    """主函数"""
    print("开始修复剩余的代码质量问题...")

    # 获取所有问题
    flake8_output = run_flake8()
    if not flake8_output:
        print("没有发现代码质量问题")
        return

    issues = parse_flake8_output(flake8_output)
    print(f"发现 {len(issues)} 个剩余问题")

    # 按文件分组问题
    files_to_fix = {}
    for file_path, line_num, code, message in issues:
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append((line_num, code, message))

    total_fixed = 0

    # 修复每个文件
    for file_path, file_issues in files_to_fix.items():
        print(f"修复文件: {file_path}")
        fixed_count = fix_file_remaining_issues(file_path, file_issues)
        if fixed_count > 0:
            print(f"  ✓ 修复了 {fixed_count} 个问题")
            total_fixed += fixed_count
        else:
            print(f"  - 没有修复任何问题")

    print(f"\n修复完成！共修复了 {total_fixed} 个问题")

    # 再次检查剩余问题
    print("\n检查剩余问题...")
    remaining_issues = run_flake8()
    if remaining_issues:
        remaining_parsed = parse_flake8_output(remaining_issues)
        remaining_count = len(remaining_parsed)
        print(f"还有 {remaining_count} 个问题需要手动修复")

        # 显示剩余问题的类型统计
        issue_types = {}
        for _, _, code, _ in remaining_parsed:
            issue_types[code] = issue_types.get(code, 0) + 1

        print("剩余问题类型统计:")
        for code, count in sorted(issue_types.items()):
            print(f"  {code}: {count} 个")

        # 显示一些具体的剩余问题示例
        print("\n剩余问题示例:")
        for i, (file_path, line_num, code, message) in enumerate(remaining_parsed[:15]):
            print(f"  {file_path}:{line_num}: {code} {message}")
        if len(remaining_parsed) > 15:
            print(f"  ... 还有 {len(remaining_parsed) - 15} 个问题")
    else:
        print("所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
