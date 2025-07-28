#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确修复代码质量问题
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


def fix_specific_issues(file_path, issues):
    """修复特定文件的问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 按行号排序，从后往前处理避免行号变化
        file_issues = [issue for issue in issues if issue["file"] == file_path]
        file_issues.sort(key=lambda x: x["line"], reverse=True)

        for issue in file_issues:
            line_idx = issue["line"] - 1
            if line_idx >= len(lines):
                continue

            error_code = issue["code"]

            # 修复W391: 文件末尾空行
            if error_code == "W391":
                # 移除文件末尾的空行
                while lines and lines[-1].strip() == "":
                    lines.pop()
                # 确保文件以一个换行符结尾
                if lines and not lines[-1].endswith("\n"):
                    lines[-1] += "\n"

            # 修复E303: 过多空行
            elif error_code == "E303":
                # 移除多余的空行，保留最多2个
                blank_count = 0
                i = line_idx
                while i >= 0 and lines[i].strip() == "":
                    blank_count += 1
                    i -= 1

                if blank_count > 2:
                    # 移除多余的空行
                    for _ in range(blank_count - 2):
                        if line_idx < len(lines):
                            lines.pop(line_idx)

            # 修复E302: 缺少空行
            elif error_code == "E302":
                # 在函数/类定义前添加空行
                if line_idx > 0:
                    # 检查前面是否已有足够空行
                    blank_count = 0
                    i = line_idx - 1
                    while i >= 0 and lines[i].strip() == "":
                        blank_count += 1
                        i -= 1

                    if blank_count < 2:
                        # 添加所需的空行
                        for _ in range(2 - blank_count):
                            lines.insert(line_idx, "\n")

            # 修复E304: 装饰器后的空行
            elif error_code == "E304":
                # 移除装饰器后的空行
                if line_idx < len(lines) and lines[line_idx].strip() == "":
                    lines.pop(line_idx)

            # 修复E999缩进错误
            elif error_code == "E999":
                line = lines[line_idx]
                if "unexpected indent" in issue["message"]:
                    # 移除意外的缩进
                    lines[line_idx] = line.lstrip() + "\n"
                elif "expected an indented block" in issue["message"]:
                    # 添加缩进
                    if not line.startswith("    "):
                        lines[line_idx] = "    " + line.lstrip()

        # 修复错位的import语句
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查是否是错位的import语句
            if re.match(
                r"^\s*from\s+app\.(models|schemas)\.[\w.]+\s+import", line.strip()
            ):
                # 这是一个import语句，应该在文件顶部
                # 暂时跳过，稍后处理
                i += 1
                continue

            fixed_lines.append(line)
            i += 1

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False


def fix_import_placement(file_path):
    """修复import语句位置"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # 分离不同类型的内容
        imports = []
        other_lines = []
        in_function = False

        for line in lines:
            # 检查是否在函数内部
            if re.match(r"^\s*(def|class|async def)\s+", line):
                in_function = True
            elif line.strip() == "" or line.startswith("#"):
                pass  # 空行和注释不改变状态
            elif not line.startswith(" ") and not line.startswith("\t"):
                in_function = False

            # 如果是顶级import语句
            if re.match(r"^\s*(import|from)\s+", line) and not in_function:
                imports.append(line)
            else:
                other_lines.append(line)

        # 重新组织文件
        if imports:
            # 找到第一个非import、非注释、非空行的位置
            insert_pos = 0
            for i, line in enumerate(other_lines):
                if (
                    line.strip()
                    and not line.strip().startswith("#")
                    and not re.match(r"^\s*(import|from)\s+", line)
                ):
                    insert_pos = i
                    break

            # 插入import语句
            for imp in reversed(imports):
                other_lines.insert(insert_pos, imp)

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(other_lines))

        return True
    except Exception as e:
        print(f"修复import位置 {file_path} 时出错: {e}")
        return False


def main():
    """主函数"""
    print("开始精确修复...")

    # 运行flake8获取问题列表
    output = run_flake8()
    if not output:
        print("没有发现问题或flake8运行失败")
        return

    issues = parse_flake8_output(output)
    print(f"发现 {len(issues)} 个问题")

    # 按文件分组
    files_with_issues = {}
    for issue in issues:
        file_path = issue["file"]
        if file_path not in files_with_issues:
            files_with_issues[file_path] = []
        files_with_issues[file_path].append(issue)

    # 修复每个文件
    fixed_count = 0
    for file_path, file_issues in files_with_issues.items():
        print(f"修复文件: {file_path} ({len(file_issues)} 个问题)")

        # 先修复import位置
        fix_import_placement(file_path)

        # 再修复其他问题
        if fix_specific_issues(file_path, file_issues):
            fixed_count += 1

    print(f"\n修复完成！处理了 {fixed_count} 个文件")

    # 最终检查
    print("\n最终检查...")
    final_output = run_flake8()

    if final_output:
        final_issues = parse_flake8_output(final_output)
        print(f"剩余问题数量: {len(final_issues)}")

        if final_issues:
            print("\n前20个剩余问题:")
            for issue in final_issues[:20]:
                print(
                    f"  {issue['file']}:{issue['line']}:{issue['col']}: {issue['code']} {issue['message']}"
                )
        else:
            print("🎉 所有代码质量问题已修复！")
    else:
        print("🎉 所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
