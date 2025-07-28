#!/usr/bin/env python3
"""
自动修复代码质量问题的脚本
"""

import os
import re
import subprocess
import ast
from pathlib import Path
from typing import List, Tuple, Dict, Set


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

        # 解析格式: file:line:col: code message
        match = re.match(r"^([^:]+):(\d+):(\d+): ([A-Z]\d+) (.+)$", line)
        if match:
            file_path, line_num, col, code, message = match.groups()
            issues.append((file_path, int(line_num), code, message))

    return issues


def get_used_names_in_file(file_path: str) -> Set[str]:
    """获取文件中实际使用的名称"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 查找所有可能的名称使用
        names = set()
        for match in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", content):
            names.add(match.group(1))

        return names
    except:
        return set()


def fix_indentation_errors(lines: List[str]) -> Tuple[List[str], int]:
    """修复缩进错误"""
    fixed_count = 0
    new_lines = []

    for i, line in enumerate(lines):
        original_line = line

        # 检查是否有混合的制表符和空格
        if "\t" in line and " " in line:
            # 将制表符转换为4个空格
            line = line.expandtabs(4)
            fixed_count += 1

        # 检查缩进是否是4的倍数
        if line.strip() and line.startswith(" "):
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 4 != 0:
                # 调整为最近的4的倍数
                correct_indent = (leading_spaces // 4 + 1) * 4
                line = " " * correct_indent + line.lstrip()
                fixed_count += 1

        new_lines.append(line)

    return new_lines, fixed_count


def fix_line_too_long_aggressive(line: str, indent_str: str) -> str:
    """更激进的行长度修复"""
    if len(line.strip()) <= 79:
        return line

    original_line = line

    # 策略1: 分割长字符串
    if ('"' in line or "'" in line) and len(line) > 79:
        # 查找字符串并分割
        for quote in ['"', "'"]:
            pattern = f"{quote}([^{quote}]{{30,}}){quote}"
            matches = list(re.finditer(pattern, line))
            for match in reversed(matches):  # 从后往前处理避免位置偏移
                content = match.group(1)
                if len(content) > 30:
                    # 分割字符串
                    mid = len(content) // 2
                    # 寻找合适的分割点（空格、标点符号等）
                    for offset in range(-5, 6):
                        split_pos = mid + offset
                        if (
                            0 < split_pos < len(content)
                            and content[split_pos] in " .,;:-"
                        ):
                            mid = split_pos + 1
                            break

                    part1 = content[:mid].rstrip()
                    part2 = content[mid:].lstrip()

                    if part1 and part2:
                        new_string = f"{quote}{part1}{quote} + \\\n{indent_str}    {quote}{part2}{quote}"
                        line = line[: match.start()] + new_string + line[match.end() :]
                        break

    # 策略2: 分割函数参数
    if "(" in line and ")" in line and "," in line and len(line) > 79:
        # 查找函数调用
        func_pattern = r"(\w+)\(([^)]+)\)"
        matches = list(re.finditer(func_pattern, line))
        for match in reversed(matches):
            func_name = match.group(1)
            params = match.group(2)
            if "," in params and len(match.group(0)) > 50:
                param_list = [p.strip() for p in params.split(",")]
                if len(param_list) > 1:
                    formatted_params = (
                        f"\n{indent_str}    "
                        + f",\n{indent_str}    ".join(param_list)
                        + f"\n{indent_str}"
                    )
                    new_call = f"{func_name}({formatted_params})"
                    line = line[: match.start()] + new_call + line[match.end() :]
                    break

    # 策略3: 分割长赋值
    if "=" in line and len(line) > 79:
        parts = line.split("=", 1)
        if len(parts) == 2:
            var_part = parts[0].strip()
            value_part = parts[1].strip()
            if len(value_part) > 40 and not value_part.startswith("("):
                line = f"{var_part} = (\n{indent_str}    {value_part}\n{indent_str})"

    # 策略4: 分割链式调用
    if "." in line and len(line) > 79:
        # 查找链式调用
        chain_pattern = r"(\w+(?:\.\w+)+)\(([^)]*)\)"
        match = re.search(chain_pattern, line)
        if match:
            chain = match.group(1)
            if "." in chain:
                parts = chain.split(".")
                if len(parts) > 2:
                    # 分割链式调用
                    new_chain = parts[0]
                    for part in parts[1:]:
                        new_chain += f" \\\n{indent_str}    .{part}"
                    line = line.replace(chain, new_chain)

    # 策略5: 分割导入语句
    if line.strip().startswith("from ") and "import" in line and "," in line:
        parts = line.split("import", 1)
        if len(parts) == 2:
            from_part = parts[0] + "import"
            import_part = parts[1].strip()
            if "," in import_part:
                imports = [imp.strip() for imp in import_part.split(",")]
                if len(imports) > 2:
                    # 分割导入
                    line = from_part + " (\n"
                    for i, imp in enumerate(imports):
                        line += f"{indent_str}    {imp}"
                        if i < len(imports) - 1:
                            line += ",\n"
                        else:
                            line += f"\n{indent_str})"

    return line


def fix_file_comprehensive(file_path: str, issues: List[Tuple[int, str, str]]) -> int:
    """综合修复文件中的所有问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        lines = content.split("\n")
        fixed_count = 0

        # 获取文件中实际使用的名称
        used_names = get_used_names_in_file(file_path)

        # 1. 修复缩进错误 (E999)
        lines, indent_fixes = fix_indentation_errors(lines)
        fixed_count += indent_fixes

        # 2. 修复空白字符问题
        for i, line in enumerate(lines):
            stripped = line.rstrip()
            if stripped != line:
                lines[i] = stripped
                fixed_count += 1

        # 确保文件以换行符结尾
        if lines and lines[-1]:
            lines.append("")
            fixed_count += 1

        # 3. 修复导入问题 (F401, F403)
        import_lines = []
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                import_lines.append((i, line))

        for i, line in import_lines:
            original_line = line

            # 处理 from ... import * (F403)
            if "import *" in line:
                if "from fastapi import *" in line:
                    common_fastapi = [
                        "FastAPI",
                        "HTTPException",
                        "Depends",
                        "status",
                        "Query",
                        "Path",
                    ]
                    used_fastapi = [
                        name for name in common_fastapi if name in used_names
                    ]
                    if used_fastapi:
                        lines[i] = f"from fastapi import {', '.join(used_fastapi)}"
                        fixed_count += 1
                elif "from sqlalchemy import *" in line:
                    common_sqlalchemy = [
                        "Column",
                        "Integer",
                        "String",
                        "DateTime",
                        "Boolean",
                        "Text",
                        "ForeignKey",
                    ]
                    used_sqlalchemy = [
                        name for name in common_sqlalchemy if name in used_names
                    ]
                    if used_sqlalchemy:
                        lines[i] = (
                            f"from sqlalchemy import {', '.join(used_sqlalchemy)}"
                        )
                        fixed_count += 1

            # 处理未使用的导入 (F401)
            elif "import " in line and not line.strip().startswith("#"):
                if line.strip().startswith("from "):
                    match = re.match(r"from\s+[\w.]+\s+import\s+(.+)", line.strip())
                    if match:
                        imports = [name.strip() for name in match.group(1).split(",")]
                        used_imports = []
                        for name in imports:
                            # 检查是否在文件中使用
                            if (
                                name in used_names
                                or name in ["Depends", "HTTPException", "FastAPI"]
                                or re.search(rf"\b{re.escape(name)}\b", content)
                            ):
                                used_imports.append(name)

                        if not used_imports:
                            lines[i] = ""
                            fixed_count += 1
                        elif len(used_imports) < len(imports):
                            module_part = line.split(" import ")[0]
                            lines[i] = f"{module_part} import {', '.join(used_imports)}"
                            fixed_count += 1

                elif line.strip().startswith("import "):
                    match = re.match(r"import\s+([\w.]+)", line.strip())
                    if match:
                        module_name = match.group(1).split(".")[0]
                        if module_name not in used_names and not re.search(
                            rf"\b{re.escape(module_name)}\b", content
                        ):
                            lines[i] = ""
                            fixed_count += 1

        # 4. 修复行过长问题 (E501)
        for line_num, code, message in issues:
            if code == "E501" and line_num <= len(lines):
                line = lines[line_num - 1]
                if len(line.strip()) > 79:
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * indent

                    new_line = fix_line_too_long_aggressive(line, indent_str)
                    if new_line != line:
                        lines[line_num - 1] = new_line
                        fixed_count += 1

        # 5. 修复空行问题 (E302, E303, E304)
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # 处理装饰器后的空行 (E304)
            if line.strip().startswith("@"):
                new_lines.append(line)
                i += 1
                # 跳过装饰器后的空行
                while i < len(lines) and not lines[i].strip():
                    i += 1
                # 确保装饰器后直接跟函数定义
                if i < len(lines):
                    new_lines.append(lines[i])
                    i += 1
                continue

            # 处理函数/类定义前的空行 (E302)
            if line.strip().startswith(("def ", "class ")):
                if new_lines and new_lines[-1].strip():
                    if not new_lines[-1].strip().startswith("@"):
                        new_lines.append("")
                        fixed_count += 1

            # 移除多余的连续空行 (E303)
            if not line.strip():
                empty_count = 0
                j = i
                while j < len(lines) and not lines[j].strip():
                    empty_count += 1
                    j += 1

                keep_count = min(empty_count, 2)
                for _ in range(keep_count):
                    new_lines.append("")

                if empty_count > keep_count:
                    fixed_count += empty_count - keep_count

                i = j
            else:
                new_lines.append(line)
                i += 1

        lines = new_lines

        # 6. 修复括号缩进问题 (E124, E128)
        for i, line in enumerate(lines):
            if line.strip().endswith((",", "(")):
                # 检查下一行的缩进
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip():
                        current_indent = len(line) - len(line.lstrip())
                        next_indent = len(next_line) - len(next_line.lstrip())
                        expected_indent = current_indent + 4

                        if next_indent != expected_indent:
                            lines[i + 1] = " " * expected_indent + next_line.lstrip()
                            fixed_count += 1

        # 7. 修复bare except (E722)
        for i, line in enumerate(lines):
            if "except:" in line:
                lines[i] = line.replace("except:", "except Exception:")
                fixed_count += 1

        # 写入修复后的内容
        new_content = "\n".join(lines)
        if new_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

        return fixed_count

    except Exception as e:
        print(f"修复文件 {file_path} 失败: {e}")
        return 0


def main():
    """主函数"""
    print("开始自动修复代码质量问题...")

    # 获取所有问题
    flake8_output = run_flake8()
    if not flake8_output:
        print("没有发现代码质量问题或flake8运行失败")
        return

    issues = parse_flake8_output(flake8_output)
    print(f"发现 {len(issues)} 个代码质量问题")

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
        fixed_count = fix_file_comprehensive(file_path, file_issues)
        if fixed_count > 0:
            print(f"  ✓ 修复了 {fixed_count} 个问题")
            total_fixed += fixed_count

    print(f"\n修复完成！共修复了 {total_fixed} 个问题")

    # 再次运行flake8检查剩余问题
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
        for i, (file_path, line_num, code, message) in enumerate(remaining_parsed[:10]):
            print(f"  {file_path}:{line_num}: {code} {message}")
        if len(remaining_parsed) > 10:
            print(f"  ... 还有 {len(remaining_parsed) - 10} 个问题")
    else:
        print("所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
