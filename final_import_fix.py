#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复所有import问题和格式问题
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


def fix_imports_and_formatting(file_path):
    """修复import和格式问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # 常见的缺失import映射
        import_fixes = {
            "ResponseModel": "from app.schemas.response import ResponseModel",
            "User": "from app.models.user import User",
            "Document": "from app.models.document import Document",
            "Project": "from app.models.project import Project",
            "ReviewStage": "from app.models.review_stage import ReviewStage",
            "Vector": "from app.models.vector import Vector",
            "HTTPException": "from fastapi import HTTPException",
            "status": "from fastapi import status",
            "Depends": "from fastapi import Depends",
            "APIRouter": "from fastapi import APIRouter",
            "Request": "from fastapi import Request",
            "UploadFile": "from fastapi import UploadFile",
            "File": "from fastapi import File",
            "Form": "from fastapi import Form",
            "Session": "from sqlalchemy.orm import Session",
            "BaseModel": "from pydantic import BaseModel",
            "List": "from typing import List",
            "Optional": "from typing import Optional",
            "Any": "from typing import Any",
            "Dict": "from typing import Dict",
        }

        # 检查需要的import
        needed_imports = set()
        for line in lines:
            for symbol, import_stmt in import_fixes.items():
                if symbol in line and not line.strip().startswith("#"):
                    # 检查是否已经有这个import
                    if not any(
                        import_stmt.split("import")[1].strip() in existing_line
                        for existing_line in lines
                        if existing_line.strip().startswith(("import", "from"))
                    ):
                        needed_imports.add(import_stmt)

        # 找到import区域
        import_end_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(("import", "from")):
                import_end_idx = i + 1
            elif line.strip() and not line.strip().startswith("#"):
                break

        # 添加缺失的import
        for import_stmt in sorted(needed_imports):
            lines.insert(import_end_idx, import_stmt)
            import_end_idx += 1

        # 修复格式问题
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # 移除文件开头的多余空行
            if i == 0:
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
                if i < len(lines):
                    fixed_lines.append(lines[i])
                i += 1
                continue

            # 处理多余的空行
            if line.strip() == "":
                # 计算连续空行数
                blank_count = 0
                j = i
                while j < len(lines) and lines[j].strip() == "":
                    blank_count += 1
                    j += 1

                # 限制连续空行数量
                if blank_count > 2:
                    # 只保留2个空行
                    for _ in range(2):
                        fixed_lines.append("")
                    i = j
                else:
                    fixed_lines.append(line)
                    i += 1
            else:
                fixed_lines.append(line)
                i += 1

        # 确保文件不以空行结尾
        while fixed_lines and fixed_lines[-1].strip() == "":
            fixed_lines.pop()

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fixed_lines))
            if fixed_lines:  # 只有在文件不为空时才添加最后的换行符
                f.write("\n")

        return True
    except Exception as e:
        print(f"修复文件 {file_path} 时出错: {e}")
        return False


def fix_specific_syntax_errors(file_path):
    """修复特定的语法错误"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        for i, line in enumerate(lines):
            # 修复装饰器后的空行
            if line.strip().startswith("@") and i + 1 < len(lines):
                fixed_lines.append(line)
                # 跳过装饰器后的空行
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                # 添加函数定义
                if j < len(lines):
                    fixed_lines.append(lines[j])
                    i = j
                continue

            # 修复缩进错误
            if line.strip() and not line.startswith((" ", "\t")):
                # 检查是否应该缩进
                if i > 0:
                    prev_line = lines[i - 1].strip()
                    if prev_line.endswith(":") and not prev_line.startswith(
                        ("@", "def ", "class ")
                    ):
                        # 应该缩进
                        line = "    " + line.lstrip()

            fixed_lines.append(line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True
    except Exception as e:
        print(f"修复语法错误 {file_path} 时出错: {e}")
        return False


def main():
    """主函数"""
    print("开始修复import和格式问题...")

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
        if fix_imports_and_formatting(file_path):
            fix_specific_syntax_errors(file_path)
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
            print("\n前20个剩余问题:")
            for line in lines[:20]:
                if line.strip():
                    print(f"  {line}")
        else:
            print("🎉 所有代码质量问题已修复！")
    else:
        print("🎉 所有代码质量问题已修复！")


if __name__ == "__main__":
    main()
