import React from 'react';
import { Spin, Typography, Space } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface LoadingProps {
  size?: 'small' | 'default' | 'large';
  tip?: string;
  spinning?: boolean;
  children?: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
  fullScreen?: boolean;
}

const Loading: React.FC<LoadingProps> = ({
  size = 'large',
  tip = '加载中...',
  spinning = true,
  children,
  style,
  className,
  fullScreen = false,
}) => {
  const antIcon = <LoadingOutlined style={{ fontSize: size === 'large' ? 24 : size === 'default' ? 18 : 14 }} spin />;

  const loadingContent = (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: fullScreen ? '100vh' : '200px',
        ...style,
      }}
      className={className}
    >
      <Space direction="vertical" align="center" size="middle">
        <Spin indicator={antIcon} size={size} />
        {tip && (
          <Text type="secondary" style={{ fontSize: '14px' }}>
            {tip}
          </Text>
        )}
      </Space>
    </div>
  );

  if (children) {
    return (
      <Spin
        spinning={spinning}
        indicator={antIcon}
        tip={tip}
        size={size}
        style={style}
        className={className}
      >
        {children}
      </Spin>
    );
  }

  return loadingContent;
};

// 全屏加载组件
export const FullScreenLoading: React.FC<{ tip?: string }> = ({ tip = '加载中...' }) => {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        zIndex: 9999,
      }}
    >
      <Loading tip={tip} />
    </div>
  );
};

// 页面加载组件
export const PageLoading: React.FC<{ tip?: string }> = ({ tip = '页面加载中...' }) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
        width: '100%',
      }}
    >
      <Loading tip={tip} />
    </div>
  );
};

// 内容加载组件
export const ContentLoading: React.FC<{ tip?: string; children?: React.ReactNode }> = ({ 
  tip = '内容加载中...', 
  children 
}) => {
  return (
    <div style={{ position: 'relative', minHeight: '100px' }}>
      <Loading tip={tip}>
        {children}
      </Loading>
    </div>
  );
};

export default Loading;