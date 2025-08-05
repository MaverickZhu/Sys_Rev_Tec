import { useEffect } from 'react';

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
          const resourceEntry = entry as PerformanceResourceTiming;
          sendMetric('slow-resource', {
            name: entry.name,
            duration: entry.duration,
            size: resourceEntry.transferSize || 0,
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
