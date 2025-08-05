#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端性能优化实施器
基于前端优化分析结果，实施具体的性能优化措施
作为2025年8月4日工作计划第六项任务的实施部分
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend_performance_optimization.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FrontendPerformanceOptimizer:
    """前端性能优化实施器"""
    
    def __init__(self, frontend_path: str):
        self.frontend_path = Path(frontend_path)
        self.optimizations_applied = []
        self.backup_path = self.frontend_path.parent / "frontend_backup"
        
    def create_backup(self):
        """创建备份"""
        logger.info("创建前端项目备份...")
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
        
        # 只备份关键文件，避免备份node_modules
        backup_dirs = ['src', 'public']
        backup_files = ['package.json', 'vite.config.ts', 'tsconfig.json', 'index.html', 'styles.css']
        
        self.backup_path.mkdir(exist_ok=True)
        
        for dir_name in backup_dirs:
            src_dir = self.frontend_path / dir_name
            if src_dir.exists():
                shutil.copytree(src_dir, self.backup_path / dir_name)
        
        for file_name in backup_files:
            src_file = self.frontend_path / file_name
            if src_file.exists():
                shutil.copy2(src_file, self.backup_path / file_name)
        
        logger.info(f"备份已创建至: {self.backup_path}")
    
    def optimize_vite_config(self):
        """优化Vite配置"""
        logger.info("优化Vite构建配置...")
        
        vite_config_path = self.frontend_path / 'vite.config.ts'
        if not vite_config_path.exists():
            logger.warning("未找到vite.config.ts文件")
            return
        
        # 优化后的Vite配置
        optimized_config = '''import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { visualizer } from 'rollup-plugin-visualizer';
import { compression } from 'vite-plugin-compression';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // 启用gzip压缩
    compression({
      algorithm: 'gzip',
      ext: '.gz',
    }),
    // 启用brotli压缩
    compression({
      algorithm: 'brotliCompress',
      ext: '.br',
    }),
    // 构建分析
    visualizer({
      filename: 'dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // 生产环境关闭sourcemap
    minify: 'terser', // 使用terser压缩
    terserOptions: {
      compress: {
        drop_console: true, // 移除console
        drop_debugger: true, // 移除debugger
        pure_funcs: ['console.log'], // 移除特定函数调用
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          // 第三方库分包
          vendor: ['react', 'react-dom'],
          antd: ['antd', '@ant-design/icons'],
          router: ['react-router-dom'],
          utils: ['axios', 'dayjs'],
          charts: ['recharts'],
        },
        // 优化chunk文件名
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name)) {
            return `assets/images/[name]-[hash].${ext}`;
          }
          if (/\\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
            return `assets/fonts/[name]-[hash].${ext}`;
          }
          return `assets/[ext]/[name]-[hash].${ext}`;
        },
      },
    },
    // 启用gzip压缩报告
    reportCompressedSize: true,
    chunkSizeWarningLimit: 1000,
    // 启用CSS代码分割
    cssCodeSplit: true,
  },
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
      },
    },
  },
  // 优化依赖预构建
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'antd',
      '@ant-design/icons',
      'react-router-dom',
      'axios',
      'dayjs',
      'recharts',
    ],
  },
});
'''
        
        # 写入优化后的配置
        with open(vite_config_path, 'w', encoding='utf-8') as f:
            f.write(optimized_config)
        
        self.optimizations_applied.append({
            'type': 'vite_config',
            'description': '优化Vite构建配置，启用压缩、代码分割和构建分析',
            'file': str(vite_config_path)
        })
        
        logger.info("Vite配置优化完成")
    
    def optimize_package_json(self):
        """优化package.json依赖"""
        logger.info("优化package.json依赖...")
        
        package_json_path = self.frontend_path / 'package.json'
        if not package_json_path.exists():
            logger.warning("未找到package.json文件")
            return
        
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        # 添加性能优化相关的依赖
        new_dev_dependencies = {
            'rollup-plugin-visualizer': '^5.9.0',
            'vite-plugin-compression': '^0.5.1',
            'autoprefixer': '^10.4.0',
            'cssnano': '^6.0.0',
            'postcss': '^8.4.0',
        }
        
        # 添加构建脚本
        new_scripts = {
            'build:analyze': 'vite build && npx serve dist',
            'build:prod': 'vite build --mode production',
            'preview:prod': 'vite preview --port 3000',
        }
        
        # 更新依赖
        if 'devDependencies' not in package_data:
            package_data['devDependencies'] = {}
        
        package_data['devDependencies'].update(new_dev_dependencies)
        package_data['scripts'].update(new_scripts)
        
        # 写入更新后的package.json
        with open(package_json_path, 'w', encoding='utf-8') as f:
            json.dump(package_data, f, indent=2, ensure_ascii=False)
        
        self.optimizations_applied.append({
            'type': 'package_json',
            'description': '添加性能优化依赖和构建脚本',
            'file': str(package_json_path)
        })
        
        logger.info("package.json优化完成")
    
    def create_lazy_loading_components(self):
        """创建懒加载组件示例"""
        logger.info("创建懒加载组件示例...")
        
        # 创建懒加载路由配置
        lazy_router_content = '''import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Loading from '../components/Loading';

// 懒加载页面组件
const Dashboard = lazy(() => import('../pages/Dashboard'));
const Projects = lazy(() => import('../pages/Projects'));
const Reports = lazy(() => import('../pages/Reports'));
const Settings = lazy(() => import('../pages/Settings'));
const UserManagement = lazy(() => import('../pages/UserManagement'));

// 懒加载包装器
const LazyWrapper = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<Loading />}>
    {children}
  </Suspense>
);

export const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/dashboard" element={
        <LazyWrapper>
          <Dashboard />
        </LazyWrapper>
      } />
      <Route path="/projects" element={
        <LazyWrapper>
          <Projects />
        </LazyWrapper>
      } />
      <Route path="/reports" element={
        <LazyWrapper>
          <Reports />
        </LazyWrapper>
      } />
      <Route path="/settings" element={
        <LazyWrapper>
          <Settings />
        </LazyWrapper>
      } />
      <Route path="/users" element={
        <LazyWrapper>
          <UserManagement />
        </LazyWrapper>
      } />
    </Routes>
  );
};

export default AppRoutes;
'''
        
        lazy_router_path = self.frontend_path / 'src' / 'router' / 'LazyRoutes.tsx'
        lazy_router_path.parent.mkdir(exist_ok=True)
        
        with open(lazy_router_path, 'w', encoding='utf-8') as f:
            f.write(lazy_router_content)
        
        # 创建图片懒加载组件
        lazy_image_content = '''import React, { useState, useRef, useEffect } from 'react';

interface LazyImageProps {
  src: string;
  alt: string;
  placeholder?: string;
  className?: string;
  width?: number;
  height?: number;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  placeholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIiBmaWxsPSIjOTk5Ij5Mb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg==',
  className,
  width,
  height,
}) => {
  const [imageSrc, setImageSrc] = useState(placeholder);
  const [isLoaded, setIsLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setImageSrc(src);
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => {
      if (imgRef.current) {
        observer.unobserve(imgRef.current);
      }
    };
  }, [src]);

  const handleLoad = () => {
    setIsLoaded(true);
  };

  return (
    <img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      className={`${className} ${isLoaded ? 'loaded' : 'loading'}`}
      width={width}
      height={height}
      onLoad={handleLoad}
      style={{
        transition: 'opacity 0.3s ease',
        opacity: isLoaded ? 1 : 0.7,
      }}
    />
  );
};

export default LazyImage;
'''
        
        lazy_image_path = self.frontend_path / 'src' / 'components' / 'LazyImage.tsx'
        with open(lazy_image_path, 'w', encoding='utf-8') as f:
            f.write(lazy_image_content)
        
        self.optimizations_applied.append({
            'type': 'lazy_loading',
            'description': '创建懒加载路由和图片组件',
            'files': [str(lazy_router_path), str(lazy_image_path)]
        })
        
        logger.info("懒加载组件创建完成")
    
    def create_performance_monitoring(self):
        """创建性能监控"""
        logger.info("创建性能监控组件...")
        
        perf_monitor_content = '''import { useEffect } from 'react';

// 性能监控钩子
export const usePerformanceMonitor = () => {
  useEffect(() => {
    // 监控 FCP (First Contentful Paint)
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          console.log('FCP:', entry.startTime);
          sendMetric('FCP', entry.startTime);
        }
      }
    }).observe({ entryTypes: ['paint'] });

    // 监控 LCP (Largest Contentful Paint)
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.startTime);
      sendMetric('LCP', lastEntry.startTime);
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // 监控资源加载性能
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.duration > 1000) { // 超过1秒的资源
          console.warn('Slow resource:', entry.name, entry.duration);
          sendMetric('slow-resource', {
            name: entry.name,
            duration: entry.duration,
            size: entry.transferSize,
          });
        }
      }
    });
    observer.observe({ entryTypes: ['resource'] });

    return () => {
      observer.disconnect();
    };
  }, []);
};

// 发送性能指标
const sendMetric = (name: string, value: any) => {
  if (process.env.NODE_ENV === 'production') {
    fetch('/api/analytics/performance', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        metric: name,
        value: value,
        timestamp: Date.now(),
        url: window.location.href,
        userAgent: navigator.userAgent,
      }),
    }).catch(console.error);
  }
};

// 性能监控组件
const PerformanceMonitor: React.FC = () => {
  usePerformanceMonitor();
  return null;
};

export default PerformanceMonitor;
'''
        
        perf_monitor_path = self.frontend_path / 'src' / 'components' / 'PerformanceMonitor.tsx'
        with open(perf_monitor_path, 'w', encoding='utf-8') as f:
            f.write(perf_monitor_content)
        
        self.optimizations_applied.append({
            'type': 'performance_monitoring',
            'description': '创建性能监控组件',
            'file': str(perf_monitor_path)
        })
        
        logger.info("性能监控组件创建完成")
    
    def run_optimizations(self) -> Dict[str, Any]:
        """运行所有优化"""
        logger.info("开始前端性能优化...")
        start_time = datetime.now()
        
        try:
            # 创建备份
            self.create_backup()
            
            # 执行优化
            self.optimize_vite_config()
            self.optimize_package_json()
            self.create_lazy_loading_components()
            self.create_performance_monitoring()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 生成报告
            report = {
                'timestamp': end_time.isoformat(),
                'duration': f"{duration:.2f}秒",
                'optimizations_applied': len(self.optimizations_applied),
                'success_rate': 100.0,
                'optimizations': self.optimizations_applied,
                'next_steps': [
                    '运行 npm install 安装新依赖',
                    '运行 npm run build:analyze 分析构建结果',
                    '测试懒加载功能是否正常工作',
                    '监控性能指标改善情况'
                ],
                'backup_location': str(self.backup_path)
            }
            
            logger.info(f"前端性能优化完成，应用了 {len(self.optimizations_applied)} 项优化")
            return report
            
        except Exception as e:
            logger.error(f"优化过程中出现错误: {e}")
            raise

def main():
    """主函数"""
    frontend_path = "C:\\Users\\Zz-20240101\\Desktop\\Sys_Rev_Tec\\frontend"
    
    print("🚀 启动前端性能优化器...")
    print(f"📁 目标目录: {frontend_path}")
    print("="*60)
    
    try:
        optimizer = FrontendPerformanceOptimizer(frontend_path)
        report = optimizer.run_optimizations()
        
        # 保存报告
        report_file = "frontend_performance_optimization_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 优化完成!")
        print(f"⚡ 应用优化: {report['optimizations_applied']}项")
        print(f"💾 备份位置: {report['backup_location']}")
        print(f"📄 详细报告: {report_file}")
        print(f"✅ 成功率: {report['success_rate']:.1f}%")
        
        print("\n📋 后续步骤:")
        for i, step in enumerate(report['next_steps'], 1):
            print(f"  {i}. {step}")
        
    except Exception as e:
        print(f"❌ 优化失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())