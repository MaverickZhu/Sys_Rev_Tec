#!/usr/bin/env python3
"""
代码质量检查脚本

这个脚本运行所有的代码质量检查工具，包括：
- 代码格式化检查 (Black, isort)
- 代码风格检查 (Flake8, Ruff)
- 类型检查 (MyPy)
- 安全检查 (Bandit)
- 测试覆盖率 (pytest-cov)

使用方法:
    python scripts/quality_check.py [--fix] [--fast] [--verbose]

参数:
    --fix: 自动修复可以修复的问题
    --fast: 使用 Ruff 替代 Flake8 (更快)
    --verbose: 显示详细输出
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
APP_DIR = ROOT_DIR / "app"
TESTS_DIR = ROOT_DIR / "tests"


# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str) -> None:
    """打印带颜色的标题"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_success(text: str) -> None:
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str) -> None:
    """打印错误消息"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str) -> None:
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def run_command(
    cmd: List[str], description: str, fix_mode: bool = False, verbose: bool = False
) -> Tuple[bool, str]:
    """运行命令并返回结果"""
    try:
        if verbose:
            print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd, cwd=ROOT_DIR, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            print_success(f"{description} passed")
            if verbose and result.stdout:
                print(result.stdout)
            return True, result.stdout
        else:
            print_error(f"{description} failed")
            if result.stderr:
                print(f"{Colors.RED}{result.stderr}{Colors.END}")
            if result.stdout:
                print(f"{Colors.YELLOW}{result.stdout}{Colors.END}")
            return False, result.stderr

    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0]}")
        print_warning(f"Please install {cmd[0]} or check your PATH")
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        print_error(f"Error running {description}: {e}")
        return False, str(e)


def check_black(fix_mode: bool = False, verbose: bool = False) -> bool:
    """检查代码格式 (Black)"""
    print_header("Code Formatting Check (Black)")

    if fix_mode:
        cmd = ["black", "app/", "--line-length", "88"]
        description = "Black formatting (fixing)"
    else:
        cmd = ["black", "app/", "--check", "--diff", "--line-length", "88"]
        description = "Black formatting check"

    success, output = run_command(cmd, description, fix_mode, verbose)
    return success


def check_isort(fix_mode: bool = False, verbose: bool = False) -> bool:
    """检查导入排序 (isort)"""
    print_header("Import Sorting Check (isort)")

    if fix_mode:
        cmd = ["isort", "app/", "--profile", "black"]
        description = "isort import sorting (fixing)"
    else:
        cmd = [
            "isort",
            "app/",
            "--check-only",
            "--diff",
            "--profile",
            "black",
        ]
        description = "isort import sorting check"

    success, output = run_command(cmd, description, fix_mode, verbose)
    return success


def check_flake8(verbose: bool = False) -> bool:
    """检查代码风格 (Flake8)"""
    print_header("Code Style Check (Flake8)")

    cmd = [
        "flake8",
        "app/",
        "--max-line-length=88",
        "--extend-ignore=E203,W503,F401,C901",
        "--max-complexity=15",
    ]

    success, output = run_command(cmd, "Flake8 style check", False, verbose)
    return success


def check_ruff(fix_mode: bool = False, verbose: bool = False) -> bool:
    """检查代码风格 (Ruff) - 更快的替代方案"""
    print_header("Code Style Check (Ruff)")

    # 检查
    cmd_check = ["ruff", "check", "app/"]
    if fix_mode:
        cmd_check.append("--fix")

    success1, output1 = run_command(cmd_check, "Ruff style check", fix_mode, verbose)

    # 格式化
    if fix_mode:
        cmd_format = ["ruff", "format", "app/"]
        success2, output2 = run_command(
            cmd_format, "Ruff formatting", fix_mode, verbose
        )
        return success1 and success2

    return success1


def check_mypy(verbose: bool = False) -> bool:
    """检查类型注解 (MyPy)"""
    print_header("Type Checking (MyPy)")

    cmd = [
        "mypy",
        "app/",
        "--ignore-missing-imports",
        "--no-strict-optional",
        "--show-error-codes",
    ]

    success, output = run_command(cmd, "MyPy type check", False, verbose)
    return success


def check_bandit(verbose: bool = False) -> bool:
    """检查安全问题 (Bandit)"""
    print_header("Security Check (Bandit)")

    cmd = [
        "bandit",
        "-r",
        "app/",
        "-f",
        "json",
        "-o",
        "bandit-report.json",
    ]

    # 先生成JSON报告
    success1, output1 = run_command(
        cmd, "Bandit security scan (JSON report)", False, verbose
    )

    # 再显示终端输出
    cmd_terminal = ["bandit", "-r", "app/"]
    success2, output2 = run_command(
        cmd_terminal, "Bandit security scan (terminal)", False, verbose
    )

    return success1 or success2  # JSON报告可能失败，但终端输出成功就算通过


def run_tests(with_coverage: bool = True, verbose: bool = False) -> bool:
    """运行测试"""
    # 检查tests目录是否存在
    if not TESTS_DIR.exists():
        print_warning("Tests directory not found, skipping tests")
        return True  # 没有测试目录不算失败
        
    if with_coverage:
        print_header("Running Tests with Coverage")
        cmd = [
            "pytest",
            "tests/",
            "-v",
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml",
        ]
        description = "Tests with coverage"
    else:
        print_header("Running Tests")
        cmd = ["pytest", "tests/", "-v"]
        description = "Tests"

    success, output = run_command(cmd, description, False, verbose)

    if success and with_coverage:
        print_success("Coverage report generated in htmlcov/")

    return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Run code quality checks")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues where possible"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Use Ruff instead of Flake8 (faster)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests")
    parser.add_argument(
        "--no-coverage", action="store_true", help="Run tests without coverage"
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}🔍 Starting Code Quality Checks{Colors.END}")
    print(f"Fix mode: {'ON' if args.fix else 'OFF'}")
    print(f"Fast mode: {'ON' if args.fast else 'OFF'}")
    print(f"Verbose: {'ON' if args.verbose else 'OFF'}")

    results = []

    # 代码格式化检查
    results.append(("Black", check_black(args.fix, args.verbose)))
    results.append(("isort", check_isort(args.fix, args.verbose)))

    # 代码风格检查
    if args.fast:
        results.append(("Ruff", check_ruff(args.fix, args.verbose)))
    else:
        results.append(("Flake8", check_flake8(args.verbose)))

    # 类型检查
    results.append(("MyPy", check_mypy(args.verbose)))

    # 安全检查
    results.append(("Bandit", check_bandit(args.verbose)))

    # 测试
    if not args.no_tests:
        with_coverage = not args.no_coverage
        results.append(("Tests", run_tests(with_coverage, args.verbose)))

    # 总结
    print_header("Quality Check Summary")

    passed = 0
    failed = 0

    for name, success in results:
        if success:
            print_success(f"{name}: PASSED")
            passed += 1
        else:
            print_error(f"{name}: FAILED")
            failed += 1

    print(f"\n{Colors.BOLD}Results: {passed} passed, {failed} failed{Colors.END}")

    if failed == 0:
        print_success("🎉 All quality checks passed!")
        sys.exit(0)
    else:
        print_error(f"💥 {failed} quality check(s) failed!")
        if not args.fix:
            print_warning("Try running with --fix to auto-fix some issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
