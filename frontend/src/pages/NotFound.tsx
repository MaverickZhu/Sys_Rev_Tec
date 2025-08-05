import React from 'react';
import { Button, Space, Typography, Card } from 'antd';
import { HomeOutlined, ArrowLeftOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleSearch = () => {
    // 这里可以实现全局搜索功能
    console.log('Open global search');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '20px',
      }}
    >
      <Card
        style={{
          maxWidth: '500px',
          width: '100%',
          textAlign: 'center',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
        }}
        bordered={false}
      >
        <div style={{ padding: '20px 0' }}>
          {/* 404 动画数字 */}
          <div
            style={{
              fontSize: '120px',
              fontWeight: 'bold',
              background: 'linear-gradient(45deg, #667eea, #764ba2)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              lineHeight: 1,
              marginBottom: '20px',
              fontFamily: 'monospace',
            }}
          >
            404
          </div>

          <Title level={2} style={{ color: '#333', marginBottom: '16px' }}>
            页面未找到
          </Title>

          <Paragraph
            style={{
              color: '#666',
              fontSize: '16px',
              lineHeight: '1.6',
              marginBottom: '32px',
            }}
          >
            抱歉，您访问的页面不存在或已被移除。
            <br />
            请检查URL是否正确，或者返回首页继续浏览。
          </Paragraph>

          <Space size="middle" wrap>
            <Button
              type="primary"
              size="large"
              icon={<HomeOutlined />}
              onClick={handleGoHome}
              style={{
                borderRadius: '8px',
                height: '44px',
                paddingLeft: '24px',
                paddingRight: '24px',
              }}
            >
              返回首页
            </Button>

            <Button
              size="large"
              icon={<ArrowLeftOutlined />}
              onClick={handleGoBack}
              style={{
                borderRadius: '8px',
                height: '44px',
                paddingLeft: '24px',
                paddingRight: '24px',
              }}
            >
              返回上页
            </Button>

            <Button
              size="large"
              icon={<SearchOutlined />}
              onClick={handleSearch}
              style={{
                borderRadius: '8px',
                height: '44px',
                paddingLeft: '24px',
                paddingRight: '24px',
              }}
            >
              全局搜索
            </Button>
          </Space>

          {/* 常用链接 */}
          <div style={{ marginTop: '40px', paddingTop: '24px', borderTop: '1px solid #f0f0f0' }}>
            <Paragraph style={{ color: '#999', marginBottom: '16px' }}>
              您可能在寻找：
            </Paragraph>
            <Space wrap>
              <Button type="link" onClick={() => navigate('/dashboard')}>
                仪表板
              </Button>
              <Button type="link" onClick={() => navigate('/projects')}>
                项目管理
              </Button>
              <Button type="link" onClick={() => navigate('/files')}>
                文件管理
              </Button>
              <Button type="link" onClick={() => navigate('/reports')}>
                报告中心
              </Button>
              <Button type="link" onClick={() => navigate('/settings')}>
                系统设置
              </Button>
            </Space>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default NotFound;