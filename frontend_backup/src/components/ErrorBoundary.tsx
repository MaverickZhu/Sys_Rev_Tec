import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Card, Space, Collapse } from 'antd';
import { BugOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // 调用错误处理回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 记录错误到控制台
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // 这里可以添加错误上报逻辑
    // reportError(error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义的 fallback UI，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认的错误 UI
      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            background: '#f5f5f5',
          }}
        >
          <Card
            style={{
              maxWidth: '600px',
              width: '100%',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
            }}
          >
            <Result
              status="error"
              icon={<BugOutlined style={{ color: '#ff4d4f' }} />}
              title="应用出现错误"
              subTitle="很抱歉，应用遇到了一个意外错误。请尝试刷新页面或联系技术支持。"
              extra={
                <Space>
                  <Button type="primary" icon={<ReloadOutlined />} onClick={this.handleReload}>
                    刷新页面
                  </Button>
                  <Button icon={<HomeOutlined />} onClick={this.handleGoHome}>
                    返回首页
                  </Button>
                  <Button onClick={this.handleReset}>
                    重试
                  </Button>
                </Space>
              }
            />

            {/* 开发环境下显示错误详情 */}
            {import.meta.env.DEV && this.state.error && (
              <div style={{ marginTop: '24px' }}>
                <Collapse ghost>
                  <Panel header="错误详情（开发模式）" key="error-details">
                    <div style={{ marginBottom: '16px' }}>
                      <Text strong>错误信息：</Text>
                      <Paragraph
                        code
                        copyable
                        style={{
                          background: '#f6f8fa',
                          padding: '12px',
                          borderRadius: '6px',
                          marginTop: '8px',
                        }}
                      >
                        {this.state.error.message}
                      </Paragraph>
                    </div>

                    <div style={{ marginBottom: '16px' }}>
                      <Text strong>错误堆栈：</Text>
                      <Paragraph
                        code
                        copyable
                        style={{
                          background: '#f6f8fa',
                          padding: '12px',
                          borderRadius: '6px',
                          marginTop: '8px',
                          fontSize: '12px',
                          lineHeight: '1.4',
                          maxHeight: '200px',
                          overflow: 'auto',
                        }}
                      >
                        {this.state.error.stack}
                      </Paragraph>
                    </div>

                    {this.state.errorInfo && (
                      <div>
                        <Text strong>组件堆栈：</Text>
                        <Paragraph
                          code
                          copyable
                          style={{
                            background: '#f6f8fa',
                            padding: '12px',
                            borderRadius: '6px',
                            marginTop: '8px',
                            fontSize: '12px',
                            lineHeight: '1.4',
                            maxHeight: '200px',
                            overflow: 'auto',
                          }}
                        >
                          {this.state.errorInfo.componentStack}
                        </Paragraph>
                      </div>
                    )}
                  </Panel>
                </Collapse>
              </div>
            )}
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// 简化的错误边界组件
export const SimpleErrorBoundary: React.FC<{
  children: ReactNode;
  fallback?: ReactNode;
}> = ({ children, fallback }) => {
  return (
    <ErrorBoundary
      fallback={
        fallback || (
          <Result
            status="error"
            title="出现错误"
            subTitle="请刷新页面重试"
            extra={
              <Button type="primary" onClick={() => window.location.reload()}>
                刷新页面
              </Button>
            }
          />
        )
      }
    >
      {children}
    </ErrorBoundary>
  );
};

export default ErrorBoundary;