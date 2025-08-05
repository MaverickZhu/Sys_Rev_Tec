#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统性能检测脚本
"""

import psutil
import time
import platform
from datetime import datetime

def check_system_performance():
    """检查系统性能指标"""
    print("=" * 50)
    print("系统性能基准测试")
    print("=" * 50)
    print(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    print()
    
    # CPU信息
    print("📊 CPU性能:")
    print(f"  CPU核心数: {psutil.cpu_count(logical=False)} 物理核心")
    print(f"  CPU线程数: {psutil.cpu_count(logical=True)} 逻辑核心")
    
    # 获取CPU使用率（1秒间隔）
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"  CPU使用率: {cpu_percent:.2f}%")
    
    # 内存信息
    print("\n💾 内存性能:")
    memory = psutil.virtual_memory()
    print(f"  总内存: {memory.total / (1024**3):.2f} GB")
    print(f"  已用内存: {memory.used / (1024**3):.2f} GB")
    print(f"  可用内存: {memory.available / (1024**3):.2f} GB")
    print(f"  内存使用率: {memory.percent:.2f}%")
    
    # 磁盘信息
    print("\n💿 磁盘性能:")
    disk = psutil.disk_usage('C:\\')
    print(f"  总磁盘空间: {disk.total / (1024**3):.2f} GB")
    print(f"  已用磁盘空间: {disk.used / (1024**3):.2f} GB")
    print(f"  可用磁盘空间: {disk.free / (1024**3):.2f} GB")
    print(f"  磁盘使用率: {disk.percent:.2f}%")
    
    # 网络信息
    print("\n🌐 网络性能:")
    net_io = psutil.net_io_counters()
    print(f"  发送字节数: {net_io.bytes_sent / (1024**2):.2f} MB")
    print(f"  接收字节数: {net_io.bytes_recv / (1024**2):.2f} MB")
    
    # 进程信息
    print("\n🔄 进程信息:")
    processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))
    processes.sort(key=lambda x: x.info['cpu_percent'] or 0, reverse=True)
    
    print("  CPU使用率最高的5个进程:")
    for i, proc in enumerate(processes[:5]):
        if proc.info['cpu_percent'] and proc.info['cpu_percent'] > 0:
            print(f"    {i+1}. {proc.info['name']} (PID: {proc.info['pid']}) - CPU: {proc.info['cpu_percent']:.2f}%")
    
    print("\n  内存使用率最高的5个进程:")
    processes.sort(key=lambda x: x.info['memory_percent'] or 0, reverse=True)
    for i, proc in enumerate(processes[:5]):
        if proc.info['memory_percent'] and proc.info['memory_percent'] > 0:
            print(f"    {i+1}. {proc.info['name']} (PID: {proc.info['pid']}) - 内存: {proc.info['memory_percent']:.2f}%")
    
    print("\n=" * 50)
    print("性能检测完成")
    print("=" * 50)

if __name__ == "__main__":
    check_system_performance()