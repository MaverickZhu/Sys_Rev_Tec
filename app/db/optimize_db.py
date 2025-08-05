#!/usr/bin/env python3

import argparse
import sys
import traceback
from pathlib import Path

from app.core.config import settings
from app.db.database_optimization import (
    analyze_query_performance,
    create_database_indexes,
    optimize_database_settings,
)

"""
数据库优化管理命令

使用方法:
    python -m app.db.optimize_db --create-indexes
    python -m app.db.optimize_db --analyze
    python -m app.db.optimize_db --optimize-settings
    python -m app.db.optimize_db --all
"""

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据库性能优化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
%(prog)s --create-indexes     # 创建数据库索引
%(prog)s --analyze           # 分析查询性能
%(prog)s --optimize-settings # 优化数据库设置
%(prog)s --all               # 执行所有优化操作
""",
    )

    parser.add_argument(
        "--create-indexes", action="store_true", help="创建数据库索引以优化查询性能"
    )

    parser.add_argument(
        "--analyze", action="store_true", help="分析查询性能并提供优化建议"
    )

    parser.add_argument(
        "--optimize-settings", action="store_true", help="优化数据库配置设置"
    )

    parser.add_argument("--all", action="store_true", help="执行所有优化操作")

    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细输出")

    args = parser.parse_args()

    # 如果没有指定任何操作，显示帮助
    if not any([args.create_indexes, args.analyze, args.optimize_settings, args.all]):
        parser.print_help()
        return

    print(f"连接数据库: {settings.DATABASE_URL}")
    print("=" * 60)

    try:
        if args.all or args.create_indexes:
            print("\n🔧 创建数据库索引...")
            create_database_indexes()
            print("✅ 索引创建完成")

        if args.all or args.analyze:
            print("\n📊 分析查询性能...")
            analyze_query_performance()
            print("✅ 性能分析完成")

        if args.all or args.optimize_settings:
            print("\n⚙️ 优化数据库设置...")
            optimize_database_settings()
            print("✅ 设置优化完成")

        print("\n🎉 数据库优化操作完成！")

    except Exception as e:
        print(f"\n❌ 优化过程中发生错误: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
