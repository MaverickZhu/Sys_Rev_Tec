#!/usr/bin/env python3
"""
最终语法修复脚本 - 批量修复所有E999语法错误
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
            ['flake8', 'app/', '--max-line-length=79'],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except Exception as e:
        print(f"运行flake8失败: {e}")
        return []


def parse_flake8_output(lines: List[str]) -> List[Tuple[str, int, str, str]]:
    """解析flake8输出"""
    issues = []
    for line in lines:
        if not line.strip():
            continue
        
        match = re.match(r'^([^:]+):(\d+):(\d+): ([A-Z]\d+) (.+)$', line)
        if match:
            file_path, line_num, col, code, message = match.groups()
            issues.append((file_path, int(line_num), code, message))
    
    return issues


def fix_indentation_errors(content: str) -> str:
    """修复缩进错误"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # 修复意外的缩进
        if line.strip():
            # 检查是否是顶级定义（class, def, import等）
            if line.lstrip().startswith(('class ', 'def ', 'async def ', 'import ', 'from ')):
                # 这些应该在顶级或适当的缩进级别
                if line.startswith('    ') and not any(fixed_lines[j].strip().startswith(('class ', 'def ', 'async def ')) 
                                                      for j in range(max(0, i-5), i) if j < len(fixed_lines)):
                    # 移除不必要的缩进
                    fixed_lines.append(line.lstrip())
                    continue
            
            # 修复错误的缩进级别
            if i > 0:
                prev_line = fixed_lines[-1] if fixed_lines else ''
                
                # 如果前一行是装饰器，当前行应该是函数定义
                if prev_line.strip().startswith('@') and line.lstrip().startswith(('def ', 'async def ')):
                    # 保持与装饰器相同的缩进
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    fixed_lines.append(' ' * prev_indent + line.lstrip())
                    continue
                
                # 如果前一行以冒号结尾，当前行应该有更多缩进
                if prev_line.rstrip().endswith(':') and line.strip() and not line.startswith(' '):
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    fixed_lines.append(' ' * (prev_indent + 4) + line.lstrip())
                    continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def fix_string_literals(content: str) -> str:
    """修复字符串字面量问题"""
    # 修复未终止的字符串
    content = re.sub(r'f"([^"]*)\\
\s*([^"]*)', r'f"\1\2', content, flags=re.MULTILINE)
    
    # 修复错误的字符串连接
    content = re.sub(r'"([^"]*)\\
\s*([^"]*)', r'"\1" \\
    "\2', content, flags=re.MULTILINE)
    
    return content


def fix_syntax_patterns(content: str) -> str:
    """修复常见的语法模式错误"""
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 修复错误的函数调用格式
        if 'ResponseModel(' in line and '=' in line and '(' in line:
            # 检查是否是错误的参数格式
            if re.search(r'code\s*=\s*\(', line):
                # 重构整个ResponseModel调用
                indent = ' ' * (len(line) - len(line.lstrip()))
                
                # 提取参数
                if 'code=' in line:
                    code_match = re.search(r'code\s*=\s*(\d+)', line)
                    message_match = re.search(r'message\s*=\s*"([^"]*)', line)
                    data_match = re.search(r'data\s*=\s*([^)]+)', line)
                    
                    if code_match:
                        fixed_lines.append(f"{indent}return ResponseModel(")
                        fixed_lines.append(f"{indent}    code={code_match.group(1)},")
                        
                        if message_match:
                            fixed_lines.append(f"{indent}    message=\"{message_match.group(1)}\",")
                        
                        if data_match:
                            data_content = data_match.group(1).strip()
                            if data_content.startswith('{') and data_content.endswith('}'):
                                fixed_lines.append(f"{indent}    data={data_content}")
                            else:
                                fixed_lines.append(f"{indent}    data={data_content}")
                        
                        fixed_lines.append(f"{indent})")
                        i += 1
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)


def fix_file_comprehensive(file_path: str) -> int:
    """全面修复文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用所有修复
        content = fix_indentation_errors(content)
        content = fix_string_literals(content)
        content = fix_syntax_patterns(content)
        
        # 最终清理
        lines = content.split('\n')
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
            fixed_lines.append('')
        
        new_content = '\n'.join(fixed_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return 1
        
        return 0
    
    except Exception as e:
        print(f"修复文件 {file_path} 失败: {e}")
        return 0


def main():
    """主函数"""
    print("开始最终语法修复...")
    
    # 获取所有E999问题
    flake8_output = run_flake8()
    if not flake8_output:
        print("没有发现代码质量问题")
        return
    
    issues = parse_flake8_output(flake8_output)
    e999_issues = [(f, l, c, m) for f, l, c, m in issues if c == 'E999']
    
    if not e999_issues:
        print("没有发现E999语法错误")
        # 显示其他问题统计
        if issues:
            issue_types = {}
            for _, _, code, _ in issues:
                issue_types[code] = issue_types.get(code, 0) + 1
            
            print(f"发现 {len(issues)} 个其他问题:")
            for code, count in sorted(issue_types.items()):
                print(f"  {code}: {count} 个")
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
        fixed_count = fix_file_comprehensive(file_path)
        if fixed_count > 0:
            print(f"  ✓ 文件已修复")
            total_fixed += fixed_count
        else:
            print(f"  - 无需修复")
    
    print(f"\n修复完成！共修复了 {total_fixed} 个文件")
    
    # 最终检查
    print("\n最终检查...")
    final_issues = run_flake8()
    if final_issues:
        final_parsed = parse_flake8_output(final_issues)
        final_e999 = [(f, l, c, m) for f, l, c, m in final_parsed if c == 'E999']
        
        if final_e999:
            print(f"还有 {len(final_e999)} 个E999问题需要手动修复")
        else:
            print("🎉 所有E999语法错误已修复！")
        
        # 显示总体统计
        total_remaining = len(final_parsed)
        if total_remaining > 0:
            issue_types = {}
            for _, _, code, _ in final_parsed:
                issue_types[code] = issue_types.get(code, 0) + 1
            
            print(f"\n总共还有 {total_remaining} 个问题:")
            for code, count in sorted(issue_types.items()):
                print(f"  {code}: {count} 个")
    else:
        print("🎉 所有代码质量问题已修复！")


if __name__ == '__main__':
    main()