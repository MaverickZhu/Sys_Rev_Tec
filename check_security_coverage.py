#!/usr/bin/env python3
"""
独立的security中间件覆盖率检查脚本
"""

import subprocess
import sys
import os

def run_security_coverage():
    """运行security中间件的覆盖率测试"""
    
    # 设置环境变量避免配置问题
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    # 运行覆盖率测试
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/test_middleware_security.py',
        '--cov=app.middleware.security',
        '--cov-report=term-missing',
        '--cov-report=html:htmlcov_security',
        '-v',
        '--tb=short'
    ]
    
    print("运行security中间件覆盖率测试...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"\n退出码: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

if __name__ == "__main__":
    success = run_security_coverage()
    if success:
        print("\n✅ Security中间件覆盖率测试完成")
    else:
        print("\n❌ Security中间件覆盖率测试失败")
        sys.exit(1)