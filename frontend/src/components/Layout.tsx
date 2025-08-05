import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Layout as AntdLayout,
  Menu,
  Button,
  Avatar,
  Dropdown,
  Space,
  Badge,
  Tooltip,
  Drawer,
  Typography,
  Divider,
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
  BellOutlined,
  SearchOutlined,
  QuestionCircleOutlined,
  SunOutlined,
  MoonOutlined,
  TeamOutlined,
  FolderOutlined,
  FileOutlined,
  BarChartOutlined,
  SafetyCertificateOutlined,
  ApiOutlined,
  DatabaseOutlined,
  ToolOutlined,
  BookOutlined,
  CustomerServiceOutlined,
  GithubOutlined,
} from '@ant-design/icons';
import { useSimpleAuth } from '../contexts/SimpleAuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useNotification } from '../contexts/NotificationContext';

const { Header, Sider, Content, Footer } = AntdLayout;
const { Text, Title } = Typography;
const { useToken } = theme;

interface MenuItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  path: string;
  roles?: string[];
  children?: MenuItem[];
}

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
    key: 'file-manager',
    icon: <FileOutlined />,
    label: '高级文件管理',
    path: '/file-manager',
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
    roles: ['admin', 'manager'],
  },
  {
    key: 'system',
    icon: <SettingOutlined />,
    label: '系统管理',
    path: '/system',
    roles: ['admin'],
    children: [
      {
        key: 'settings',
        icon: <ToolOutlined />,
        label: '系统设置',
        path: '/settings',
      },
      {
        key: 'security',
        icon: <SafetyCertificateOutlined />,
        label: '安全管理',
        path: '/security',
      },
      {
        key: 'api',
        icon: <ApiOutlined />,
        label: 'API管理',
        path: '/api',
      },
      {
        key: 'database',
        icon: <DatabaseOutlined />,
        label: '数据库',
        path: '/database',
      },
    ],
  },
];

const Layout: React.FC = () => {
  const { user, logout } = useSimpleAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const { notifications, unreadCount } = useNotification();
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useToken();
  
  const [collapsed, setCollapsed] = useState(false);
  const [notificationDrawerVisible, setNotificationDrawerVisible] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [openKeys, setOpenKeys] = useState<string[]>([]);

  useEffect(() => {
    // 根据当前路径设置选中的菜单项
    const currentPath = location.pathname;
    const findSelectedKey = (items: MenuItem[], path: string): string | null => {
      for (const item of items) {
        if (item.path === path) {
          return item.key;
        }
        if (item.children) {
          const childKey = findSelectedKey(item.children, path);
          if (childKey) {
            setOpenKeys(prev => [...new Set([...prev, item.key])]);
            return childKey;
          }
        }
      }
      return null;
    };
    
    const selectedKey = findSelectedKey(menuItems, currentPath);
    if (selectedKey) {
      setSelectedKeys([selectedKey]);
    }
  }, [location.pathname]);

  const handleMenuClick = ({ key }: { key: string }) => {
    const findMenuItem = (items: MenuItem[], targetKey: string): MenuItem | null => {
      for (const item of items) {
        if (item.key === targetKey) {
          return item;
        }
        if (item.children) {
          const childItem = findMenuItem(item.children, targetKey);
          if (childItem) {
            return childItem;
          }
        }
      }
      return null;
    };
    
    const menuItem = findMenuItem(menuItems, key);
    if (menuItem) {
      navigate(menuItem.path);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const filterMenuItems = (items: MenuItem[]): MenuItem[] => {
    return items.filter(item => {
      if (item.roles && user?.roles) {
        const userRoles = user.roles.map(role => role.name);
        const hasPermission = item.roles.some(role => userRoles.includes(role));
        if (!hasPermission) {
          return false;
        }
      }
      
      if (item.children) {
        item.children = filterMenuItems(item.children);
      }
      
      return true;
    });
  };

  const filteredMenuItems = filterMenuItems([...menuItems]);

  const convertToAntdMenuItems = (items: MenuItem[]): any[] => {
    return items.map(item => ({
      key: item.key,
      icon: item.icon,
      label: item.label,
      children: item.children ? convertToAntdMenuItems(item.children) : undefined,
    }));
  };

  const userMenu = (
    <Menu>
      <Menu.Item key="profile" icon={<UserOutlined />} onClick={() => navigate('/profile')}>
        个人资料
      </Menu.Item>
      <Menu.Item key="settings" icon={<SettingOutlined />} onClick={() => navigate('/settings')}>
        设置
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="help" icon={<QuestionCircleOutlined />}>
        帮助中心
      </Menu.Item>
      <Menu.Item key="feedback" icon={<CustomerServiceOutlined />}>
        意见反馈
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={handleLogout}>
        退出登录
      </Menu.Item>
    </Menu>
  );

  const notificationMenu = (
    <Menu>
      <Menu.Item key="all" onClick={() => setNotificationDrawerVisible(true)}>
        查看所有通知
      </Menu.Item>
      <Menu.Item key="mark-read">
        标记全部已读
      </Menu.Item>
      <Menu.Item key="settings">
        通知设置
      </Menu.Item>
    </Menu>
  );

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
          openKeys={openKeys}
          onOpenChange={setOpenKeys}
          onClick={handleMenuClick}
          items={convertToAntdMenuItems(filteredMenuItems)}
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
            {/* 搜索 */}
            <Tooltip title="全局搜索">
              <Button
                type="text"
                icon={<SearchOutlined />}
                style={{ fontSize: '16px' }}
                onClick={() => {
                  console.log('Global search');
                }}
              />
            </Tooltip>

            {/* 主题切换 */}
            <Tooltip title={isDarkMode ? '切换到浅色模式' : '切换到深色模式'}>
              <Button
                type="text"
                icon={isDarkMode ? <SunOutlined /> : <MoonOutlined />}
                onClick={toggleTheme}
                style={{ fontSize: '16px' }}
              />
            </Tooltip>

            {/* 通知 */}
            <Dropdown overlay={notificationMenu} trigger={['click']}>
              <Badge count={unreadCount} size="small">
                <Button
                  type="text"
                  icon={<BellOutlined />}
                  style={{ fontSize: '16px' }}
                />
              </Badge>
            </Dropdown>

            {/* 用户菜单 */}
            <Dropdown overlay={userMenu} trigger={['click']}>
              <Space style={{ cursor: 'pointer' }}>
                <Avatar
                  size={32}
                  src={user?.avatar}
                  style={{ backgroundColor: token.colorPrimary }}
                >
                  {user?.name?.charAt(0) || user?.username?.charAt(0)}
                </Avatar>
                {!collapsed && (
                  <Text style={{ color: token.colorText }}>
                    {user?.name || user?.username}
                  </Text>
                )}
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* 内容区域 */}
        <Content
          style={{
            background: isDarkMode ? token.colorBgLayout : '#f0f2f5',
            minHeight: 'calc(100vh - 64px - 70px)',
            padding: '24px',
          }}
        >
          <Outlet />
        </Content>

        {/* 页脚 */}
        <Footer
          style={{
            textAlign: 'center',
            background: isDarkMode ? token.colorBgContainer : '#fff',
            borderTop: `1px solid ${token.colorBorder}`,
            padding: '16px 24px',
          }}
        >
          <Space split={<Divider type="vertical" />}>
            <Text type="secondary">© 2024 系统评审技术平台</Text>
            <Text type="secondary">版本 1.0.0</Text>
            <Space>
              <Button type="link" size="small" icon={<BookOutlined />}>
                文档
              </Button>
              <Button type="link" size="small" icon={<GithubOutlined />}>
                GitHub
              </Button>
              <Button type="link" size="small" icon={<CustomerServiceOutlined />}>
                支持
              </Button>
            </Space>
          </Space>
        </Footer>
      </AntdLayout>

      {/* 通知抽屉 */}
      <Drawer
        title="通知中心"
        placement="right"
        onClose={() => setNotificationDrawerVisible(false)}
        open={notificationDrawerVisible}
        width={400}
      >
        <div style={{ marginBottom: '16px' }}>
          <Space>
            <Button size="small">全部</Button>
            <Button size="small">未读</Button>
            <Button size="small">系统</Button>
            <Button size="small">项目</Button>
          </Space>
        </div>
        
        {notifications.length > 0 ? (
          <div>
            {notifications.map(notification => (
              <div
                key={notification.id}
                style={{
                  padding: '12px',
                  borderBottom: `1px solid ${token.colorBorder}`,
                  backgroundColor: notification.read ? 'transparent' : token.colorBgTextHover,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <Text strong={!notification.read}>{notification.title}</Text>
                    <div style={{ marginTop: '4px' }}>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {notification.content}
                      </Text>
                    </div>
                    <div style={{ marginTop: '8px' }}>
                      <Text type="secondary" style={{ fontSize: '11px' }}>
                        {notification.createdAt}
                      </Text>
                    </div>
                  </div>
                  {!notification.read && (
                    <Badge status="processing" />
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <BellOutlined style={{ fontSize: '48px', color: token.colorTextTertiary }} />
            <div style={{ marginTop: '16px' }}>
              <Text type="secondary">暂无通知</Text>
            </div>
          </div>
        )}
      </Drawer>
    </AntdLayout>
  );
};

export default Layout;