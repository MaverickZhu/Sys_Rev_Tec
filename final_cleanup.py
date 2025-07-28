#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终清理脚本 - 处理剩余的格式问题
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


def parse_flake8_output(output):
    """解析flake8输出"""
    issues = []
    for line in output.strip().split("\n"):
        if line.strip():
            parts = line.split(":")
            if len(parts) >= 4:
                file_path = parts[0]
                line_num = int(parts[1])
                col_num = int(parts[2])
                error_code = parts[3].strip().split()[0]
                message = ":".join(parts[3:]).strip()
                issues.append(
                    {
                        "file": file_path,
                        "line": line_num,
                        "col": col_num,
                        "code": error_code,
                        "message": message,
                    }
                )
    return issues


def fix_blank_lines(file_path):
    """修复空行问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查是否是函数或类定义
            if re.match(r"^\s*(def|class|async def)\s+", line):
                # 确保前面有2个空行（除非是文件开头）
                if i > 0:
                    # 移除多余的空行
                    while fixed_lines and fixed_lines[-1].strip() == "":
                        fixed_lines.pop()
                    # 添加2个空行
                    fixed_lines.extend(["\n", "\n"])
                fixed_lines.append(line)

            # 检查装饰器后的空行
            elif re.match(r"^\s*@", line):
                fixed_lines.append(line)
                # 查找装饰器后的函数定义
                j = i + 1
                while j < len(lines) and (
                    lines[j].strip() == "" or re.match(r"^\s*@", lines[j])
                ):
                    if lines[j].strip() == "":
                        # 跳过装饰器后的空行
                        j += 1
                        continue
                    fixed_lines.append(lines[j])
                    j += 1

                if j < len(lines) and re.match(
                    r"^\s*(def|class|async def)\s+", lines[j]
                ):
                    # 装饰器后直接跟函数定义，不需要空行
                    fixed_lines.append(lines[j])
                    i = j
                else:
                    fixed_lines.append(line)

            else:
                fixed_lines.append(line)

            i += 1

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True
    except Exception as e:
        print(f"修复空行 {file_path} 时出错: {e}")
        return False


def fix_continuation_lines(file_path):
    """修复续行缩进问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        for i, line in enumerate(lines):
            # 检查是否是续行
            if i > 0 and (
                lines[i - 1].rstrip().endswith("(")
                or lines[i - 1].rstrip().endswith(",")
                or lines[i - 1].rstrip().endswith("=")
            ):

                # 计算前一行的缩进
                prev_indent = len(lines[i - 1]) - len(lines[i - 1].lstrip())
                current_indent = len(line) - len(line.lstrip())

                # 续行应该比前一行多缩进4个空格
                if line.strip() and current_indent <= prev_indent:
                    correct_indent = prev_indent + 4
                    line = " " * correct_indent + line.lstrip()

            # 修复ResponseModel等特殊情况
            if "ResponseModel" in line and "(" in line:
                # 确保参数正确对齐
                if i + 1 < len(lines) and lines[i + 1].strip().startswith(
                    ("data=", "message=")
                ):
                    next_line = lines[i + 1]
                    base_indent = len(line) - len(line.lstrip())
                    param_indent = base_indent + 4
                    lines[i + 1] = " " * param_indent + next_line.lstrip()

            fixed_lines.append(line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True
    except Exception as e:
        print(f"修复续行 {file_path} 时出错: {e}")
        return False


def main():
    """主函数"""
    print("开始最终清理...")

    # 获取当前问题
    flake8_output = run_flake8()
    issues = parse_flake8_output(flake8_output)

    print(f"发现 {len(issues)} 个问题")

    # 按文件分组问题
    files_to_fix = {}
    for issue in issues:
        file_path = issue["file"]
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append(issue)

    # 修复每个文件
    for file_path, file_issues in files_to_fix.items():
        print(f"修复文件: {file_path}")

        # 检查问题类型并应用相应修复
        has_blank_line_issues = any(
            issue["code"] in ["E302", "E304", "E305"] for issue in file_issues
        )
        has_continuation_issues = any(
            issue["code"] in ["E122", "E124", "E125", "E128"] for issue in file_issues
        )

        if has_blank_line_issues:
            fix_blank_lines(file_path)

        if has_continuation_issues:
            fix_continuation_lines(file_path)

    print("\n最终清理完成！")

    # 最终检查
    print("\n最终检查...")
    final_output = run_flake8()
    final_issues = parse_flake8_output(final_output)

    print(f"剩余问题数量: {len(final_issues)}")

    if final_issues:
        print("\n剩余问题:")
        for issue in final_issues[:20]:  # 显示前20个
            print(
                f"  {issue['file']}:{issue['line']}:{issue['col']}: {issue['code']} {issue['message']}"
            )
    else:
        print("🎉 所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
