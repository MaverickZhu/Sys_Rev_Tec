import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';
import duration from 'dayjs/plugin/duration';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import App from './App';
import './index.css';

// 配置 dayjs
dayjs.locale('zh-cn');
dayjs.extend(relativeTime);
dayjs.extend(duration);
dayjs.extend(utc);
dayjs.extend(timezone);

// 设置默认时区
dayjs.tz.setDefault('Asia/Shanghai');

// 全局错误处理
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  // 可以在这里添加错误上报逻辑
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  // 可以在这里添加错误上报逻辑
});

// 性能监控
if ('performance' in window && 'measure' in window.performance) {
  window.addEventListener('load', () => {
    setTimeout(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      
      console.log('Performance metrics:', {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: paint.find(entry => entry.name === 'first-paint')?.startTime,
        firstContentfulPaint: paint.find(entry => entry.name === 'first-contentful-paint')?.startTime,
      });
    }, 0);
  });
}

// 创建根元素
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// 渲染应用
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <ConfigProvider
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
            wireframe: false,
          },
          components: {
            Layout: {
              bodyBg: '#f0f2f5',
              headerBg: '#fff',
              siderBg: '#fff',
            },
            Menu: {
              itemBg: 'transparent',
              itemSelectedBg: '#e6f7ff',
              itemSelectedColor: '#1890ff',
            },
            Card: {
              borderRadiusLG: 8,
            },
            Button: {
              borderRadius: 6,
            },
            Input: {
              borderRadius: 6,
            },
            Select: {
              borderRadius: 6,
            },
            Table: {
              headerBg: '#fafafa',
              headerColor: 'rgba(0, 0, 0, 0.85)',
              headerSortActiveBg: '#f0f0f0',
            },
            Modal: {
              borderRadiusLG: 8,
            },
            Drawer: {
              borderRadiusLG: 8,
            },
          },
        }}
      >
        <App />
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>
);

// 开发环境下的热重载支持
if (import.meta.env.DEV && import.meta.hot) {
  import.meta.hot.accept('./App', () => {
    const NextApp = require('./App').default;
    root.render(
      <React.StrictMode>
        <BrowserRouter>
          <ConfigProvider
            locale={zhCN}
            theme={{
              token: {
                colorPrimary: '#1890ff',
                borderRadius: 6,
                wireframe: false,
              },
            }}
          >
            <NextApp />
          </ConfigProvider>
        </BrowserRouter>
      </React.StrictMode>
    );
  });
}

// 服务工作者注册（用于PWA支持）
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// 导出类型定义（用于测试）
export type { };