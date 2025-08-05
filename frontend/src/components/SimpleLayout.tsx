import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Layout as AntdLayout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Space,
  Tooltip,
  Typography,
  theme,
} from 'antd';
import {
  DashboardOutlined,
  ProjectOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SunOutlined,
  MoonOutlined,
  TeamOutlined,
  FolderOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';
import { useTheme } from '../contexts/ThemeContext';

const { Header, Sider, Content, Footer } = AntdLayout;
const { Text, Title } = Typography;
const { useToken } = theme;

interface MenuItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  path: string;
}

// 简化的菜单项（移除权限控制）
const menuItems: MenuItem[] = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: '仪表板',
    path: '/dashboard',
  },
  {
    key: 'projects',
    icon: <ProjectOutlined />,
    label: '项目管理',
    path: '/projects',
  },
  {
    key: 'files',
    icon: <FolderOutlined />,
    label: '文件管理',
    path: '/files',
  },
  {
    key: 'reports',
    icon: <BarChartOutlined />,
    label: '报告中心',
    path: '/reports',
  },
  {
    key: 'users',
    icon: <TeamOutlined />,
    label: '用户管理',
    path: '/users',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '系统设置',
    path: '/settings',
  },
];

const SimpleLayout: React.FC = () => {
  const { user, logout } = useSimpleAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useToken();
  
  const [collapsed, setCollapsed] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);

  useEffect(() => {
    // 根据当前路径设置选中的菜单项
    const currentPath = location.pathname;
    const selectedItem = menuItems.find(item => item.path === currentPath);
    if (selectedItem) {
      setSelectedKeys([selectedItem.key]);
    }
  }, [location.pathname]);

  const handleMenuClick = ({ key }: { key: string }) => {
    const menuItem = menuItems.find(item => item.key === key);
    if (menuItem) {
      navigate(menuItem.path);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <AntdLayout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        style={{
          background: isDarkMode ? token.colorBgContainer : '#fff',
          borderRight: `1px solid ${token.colorBorder}`,
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: '64px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? '0' : '0 24px',
            borderBottom: `1px solid ${token.colorBorder}`,
          }}
        >
          {collapsed ? (
            <Avatar size={32} style={{ backgroundColor: token.colorPrimary }}>
              S
            </Avatar>
          ) : (
            <Space>
              <Avatar size={32} style={{ backgroundColor: token.colorPrimary }}>
                S
              </Avatar>
              <Title level={4} style={{ margin: 0, color: token.colorText }}>
                系统评审
              </Title>
            </Space>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          onClick={handleMenuClick}
          items={menuItems.map(item => ({
            key: item.key,
            icon: item.icon,
            label: item.label,
          }))}
          style={{
            border: 'none',
            background: 'transparent',
          }}
        />
      </Sider>

      <AntdLayout>
        {/* 头部 */}
        <Header
          style={{
            padding: '0 24px',
            background: isDarkMode ? token.colorBgContainer : '#fff',
            borderBottom: `1px solid ${token.colorBorder}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Space>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{
                fontSize: '16px',
                width: 40,
                height: 40,
              }}
            />
          </Space>

          <Space size="middle">
            {/* 主题切换 */}
            <Tooltip title={isDarkMode ? '切换到浅色模式' : '切换到深色模式'}>
              <Button
                type="text"
                icon={isDarkMode ? <SunOutlined /> : <MoonOutlined />}
                onClick={toggleTheme}
                style={{ fontSize: '16px' }}
              />
            </Tooltip>

            {/* 用户信息 */}
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              arrow
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  size={32}
                  icon={<UserOutlined />}
                  style={{ backgroundColor: token.colorPrimary }}
                />
                {!collapsed && (
                  <Space direction="vertical" size={0}>
                    <Text strong style={{ fontSize: '14px' }}>
                      {user?.username || 'Admin'}
                    </Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {user?.roles?.[0]?.displayName || user?.roles?.[0]?.name || 'Administrator'}
                    </Text>
                  </Space>
                )}
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* 内容区域 */}
        <Content
          style={{
            margin: '24px',
            padding: '24px',
            background: isDarkMode ? token.colorBgContainer : '#fff',
            borderRadius: token.borderRadius,
            minHeight: 'calc(100vh - 112px)',
          }}
        >
          <Outlet />
        </Content>

        {/* 底部 */}
        <Footer style={{ textAlign: 'center', color: token.colorTextSecondary }}>
          系统评审平台 ©2024 个人使用版
        </Footer>
      </AntdLayout>
    </AntdLayout>
  );
};

export default SimpleLayout;