'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { AdminAuthProvider, useAdminAuth } from '@/contexts/AdminAuthContext';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  AppBar,
  Toolbar,
  IconButton,
  Avatar,
} from '@mui/material';
import {
  LayoutDashboard,
  Settings,
  Users,
  LogOut,
  Menu,
} from 'lucide-react';

const drawerWidth = 260;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    path: '/admin/dashboard',
    icon: <LayoutDashboard size={20} />,
  },
  {
    label: 'Configuration',
    path: '/admin/configuration',
    icon: <Settings size={20} />,
  },
  {
    label: 'Admin Users',
    path: '/admin/users',
    icon: <Users size={20} />,
  },
];

function AdminLayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, user, logout, loading } = useAdminAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isLoginPage = pathname === '/admin/login';

  useEffect(() => {
    if (!loading && isAuthenticated && isLoginPage) {
      router.push('/admin/dashboard');
    }
  }, [isAuthenticated, isLoginPage, loading, router]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path: string) => {
    router.push(path);
    setMobileOpen(false);
  };

  const handleLogout = () => {
    logout();
  };

  const drawer = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--gpt-sidebar)',
      }}
    >
      {/* Logo/Brand */}
      <Box
        sx={{
          p: 3,
          borderBottom: '1px solid var(--gpt-border)',
        }}
      >
        <Typography
          variant="h6"
          sx={{
            color: 'var(--gpt-text)',
            fontWeight: 700,
            fontSize: '1.25rem',
          }}
        >
          ReviewGuide.ai
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: 'var(--gpt-text-secondary)',
            fontSize: '0.75rem',
          }}
        >
          Admin Panel
        </Typography>
      </Box>

      {/* Navigation */}
      <List sx={{ flex: 1, pt: 2, px: 1.5 }}>
        {navItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  px: 2,
                  py: 1.5,
                  background: isActive ? 'var(--gpt-accent-light)' : 'transparent',
                  color: isActive ? 'var(--gpt-accent)' : 'var(--gpt-text-secondary)',
                  '&:hover': {
                    background: isActive ? 'var(--gpt-accent-light)' : 'var(--gpt-hover)',
                    color: isActive ? 'var(--gpt-accent)' : 'var(--gpt-text)',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: 'inherit',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.9375rem',
                    fontWeight: isActive ? 600 : 500,
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* User info and logout */}
      {user && (
        <Box
          sx={{
            p: 2,
            borderTop: '1px solid var(--gpt-border)',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1.5,
              p: 1.5,
              borderRadius: 2,
              background: 'var(--gpt-hover)',
            }}
          >
            <Avatar
              sx={{
                width: 36,
                height: 36,
                background: 'var(--gpt-accent)',
                fontSize: '0.875rem',
              }}
            >
              {user.username.charAt(0).toUpperCase()}
            </Avatar>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography
                variant="body2"
                sx={{
                  color: 'var(--gpt-text)',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {user.username}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: 'var(--gpt-text-secondary)',
                  fontSize: '0.75rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  display: 'block',
                }}
              >
                {user.email}
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={handleLogout}
              sx={{
                color: 'var(--gpt-text-secondary)',
                '&:hover': {
                  color: '#ef4444',
                  background: 'rgba(239, 68, 68, 0.1)',
                },
              }}
            >
              <LogOut size={18} />
            </IconButton>
          </Box>
        </Box>
      )}
    </Box>
  );

  if (isLoginPage) {
    return <Box sx={{ background: 'var(--gpt-background)', minHeight: '100vh' }}>{children}</Box>;
  }

  // Show loading state while checking authentication
  if (loading) {
    return <Box sx={{ background: 'var(--gpt-background)', minHeight: '100vh' }}>{children}</Box>;
  }

  // If not authenticated and not on login page, don't render the admin layout
  if (!isAuthenticated) {
    return <Box sx={{ background: 'var(--gpt-background)', minHeight: '100vh' }}>{children}</Box>;
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', background: 'var(--gpt-background)' }}>
      {/* Mobile AppBar */}
      <AppBar
        position="fixed"
        sx={{
          display: { xs: 'block', md: 'none' },
          width: '100%',
          background: 'var(--gpt-sidebar)',
          borderBottom: '1px solid var(--gpt-border)',
          boxShadow: 'var(--gpt-shadow-md)',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, color: 'var(--gpt-text)' }}
          >
            <Menu />
          </IconButton>
          <Typography variant="h6" sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>
            ReviewGuide.ai
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Desktop Drawer */}
      <Box
        component="nav"
        sx={{
          width: { md: drawerWidth },
          flexShrink: { md: 0 },
        }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              border: 'none',
            },
          }}
        >
          {drawer}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              border: 'none',
              borderRight: '1px solid var(--gpt-border)',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { xs: '100%', md: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          background: 'var(--gpt-background)',
          pt: { xs: '64px', md: 0 },
        }}
      >
        {children}
      </Box>
    </Box>
  );
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminAuthProvider>
      <AdminLayoutContent>{children}</AdminLayoutContent>
    </AdminAuthProvider>
  );
}
