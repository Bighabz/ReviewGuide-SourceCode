'use client';

import { useEffect, useState } from 'react';
import { useAdminAuth } from '@/contexts/AdminAuthContext';
import AdminProtectedRoute from '@/components/AdminProtectedRoute';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Box,
  Chip,
  CircularProgress,
  Switch,
  FormControlLabel,
  Alert,
} from '@mui/material';
import { Edit, Trash2, Save, X, UserPlus } from 'lucide-react';

interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

interface UserFormData {
  username: string;
  email: string;
  password: string;
  is_active: boolean;
}

function UsersPageContent() {
  const { token } = useAdminAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialog, setCreateDialog] = useState(false);
  const [editDialog, setEditDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
    is_active: true,
  });

  const fetchUsers = async () => {
    try {
      const response = await fetch('http://localhost:8000/v1/admin/users', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        setError('Failed to fetch users');
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      setError('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUsers();
    }
  }, [token]);

  const handleCreateUser = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      is_active: true,
    });
    setCreateDialog(true);
    setError('');
  };

  const handleEditUser = (user: AdminUser) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      is_active: user.is_active,
    });
    setEditDialog(true);
    setError('');
  };

  const handleSaveCreate = async () => {
    if (!formData.username || !formData.email || !formData.password) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/v1/admin/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        await fetchUsers();
        setCreateDialog(false);
        setSuccess('User created successfully');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to create user');
      }
    } catch (error) {
      console.error('Error creating user:', error);
      setError('Failed to create user');
    }
  };

  const handleSaveEdit = async () => {
    if (!selectedUser || !formData.username || !formData.email) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      const updateData: any = {
        username: formData.username,
        email: formData.email,
        is_active: formData.is_active,
      };

      if (formData.password) {
        updateData.password = formData.password;
      }

      const response = await fetch(`http://localhost:8000/v1/admin/users/${selectedUser.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updateData),
      });

      if (response.ok) {
        await fetchUsers();
        setEditDialog(false);
        setSelectedUser(null);
        setSuccess('User updated successfully');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to update user');
      }
    } catch (error) {
      console.error('Error updating user:', error);
      setError('Failed to update user');
    }
  };

  const handleDeleteUser = async (user: AdminUser) => {
    if (!confirm(`Are you sure you want to delete user "${user.username}"?`)) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/v1/admin/users/${user.id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchUsers();
        setSuccess('User deleted successfully');
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to delete user');
        setTimeout(() => setError(''), 3000);
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      setError('Failed to delete user');
      setTimeout(() => setError(''), 3000);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress sx={{ color: 'var(--gpt-accent)' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, background: 'var(--gpt-background)', minHeight: '100vh' }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>
          Admin Users
        </Typography>
        <Button
          variant="contained"
          startIcon={<UserPlus size={18} />}
          onClick={handleCreateUser}
          sx={{
            background: 'var(--gpt-accent)',
            textTransform: 'none',
            fontWeight: 600,
            '&:hover': {
              background: 'var(--gpt-accent-hover)',
            },
          }}
        >
          Create User
        </Button>
      </Box>

      {success && (
        <Alert
          severity="success"
          sx={{
            mb: 3,
            background: 'rgba(16, 185, 129, 0.1)',
            color: '#10b981',
            border: '1px solid rgba(16, 185, 129, 0.2)',
          }}
        >
          {success}
        </Alert>
      )}

      {error && !createDialog && !editDialog && (
        <Alert
          severity="error"
          sx={{
            mb: 3,
            background: 'rgba(239, 68, 68, 0.1)',
            color: '#ef4444',
            border: '1px solid rgba(239, 68, 68, 0.2)',
          }}
        >
          {error}
        </Alert>
      )}

      <Card
        sx={{
          background: 'var(--gpt-background)',
          border: '1px solid var(--gpt-border)',
          boxShadow: 'var(--gpt-shadow-md)',
        }}
      >
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ background: 'var(--gpt-sidebar)' }}>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Username</TableCell>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Email</TableCell>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Status</TableCell>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Created</TableCell>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Last Login</TableCell>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow
                  key={user.id}
                  sx={{
                    '&:hover': {
                      background: 'var(--gpt-hover)',
                    },
                  }}
                >
                  <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 500 }}>
                    {user.username}
                  </TableCell>
                  <TableCell sx={{ color: 'var(--gpt-text)' }}>{user.email}</TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      sx={{
                        background: user.is_active
                          ? 'rgba(16, 185, 129, 0.1)'
                          : 'rgba(239, 68, 68, 0.1)',
                        color: user.is_active ? '#10b981' : '#ef4444',
                        fontWeight: 600,
                      }}
                    />
                  </TableCell>
                  <TableCell sx={{ color: 'var(--gpt-text-secondary)', fontSize: '0.875rem' }}>
                    {formatDate(user.created_at)}
                  </TableCell>
                  <TableCell sx={{ color: 'var(--gpt-text-secondary)', fontSize: '0.875rem' }}>
                    {formatDate(user.last_login)}
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <IconButton
                        size="small"
                        onClick={() => handleEditUser(user)}
                        sx={{
                          color: 'var(--gpt-accent)',
                          '&:hover': {
                            background: 'var(--gpt-accent-light)',
                          },
                        }}
                      >
                        <Edit size={18} />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteUser(user)}
                        sx={{
                          color: '#ef4444',
                          '&:hover': {
                            background: 'rgba(239, 68, 68, 0.1)',
                          },
                        }}
                      >
                        <Trash2 size={18} />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Create User Dialog */}
      <Dialog
        open={createDialog}
        onClose={() => setCreateDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: 'var(--gpt-background)',
            border: '1px solid var(--gpt-border)',
          },
        }}
      >
        <DialogTitle sx={{ color: 'var(--gpt-text)' }}>Create Admin User</DialogTitle>
        <DialogContent>
          {error && (
            <Alert
              severity="error"
              sx={{
                mb: 2,
                background: 'rgba(239, 68, 68, 0.1)',
                color: '#ef4444',
                border: '1px solid rgba(239, 68, 68, 0.2)',
              }}
            >
              {error}
            </Alert>
          )}
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}>
              Username *
            </Typography>
            <TextField
              fullWidth
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="Enter username"
              sx={{
                mb: 2,
                '& .MuiInputBase-root': {
                  background: 'var(--gpt-input-bg)',
                  color: 'var(--gpt-text)',
                },
              }}
            />
            <Typography variant="body2" sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}>
              Email *
            </Typography>
            <TextField
              fullWidth
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="Enter email"
              sx={{
                mb: 2,
                '& .MuiInputBase-root': {
                  background: 'var(--gpt-input-bg)',
                  color: 'var(--gpt-text)',
                },
              }}
            />
            <Typography variant="body2" sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}>
              Password *
            </Typography>
            <TextField
              fullWidth
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="Enter password"
              sx={{
                mb: 2,
                '& .MuiInputBase-root': {
                  background: 'var(--gpt-input-bg)',
                  color: 'var(--gpt-text)',
                },
              }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': {
                      color: 'var(--gpt-accent)',
                    },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                      backgroundColor: 'var(--gpt-accent)',
                    },
                  }}
                />
              }
              label={<Typography sx={{ color: 'var(--gpt-text)' }}>Active</Typography>}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button
            onClick={() => setCreateDialog(false)}
            startIcon={<X size={18} />}
            sx={{ color: 'var(--gpt-text-secondary)', textTransform: 'none' }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveCreate}
            variant="contained"
            startIcon={<Save size={18} />}
            sx={{
              background: 'var(--gpt-accent)',
              textTransform: 'none',
              '&:hover': {
                background: 'var(--gpt-accent-hover)',
              },
            }}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog
        open={editDialog}
        onClose={() => setEditDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: 'var(--gpt-background)',
            border: '1px solid var(--gpt-border)',
          },
        }}
      >
        <DialogTitle sx={{ color: 'var(--gpt-text)' }}>Edit Admin User</DialogTitle>
        <DialogContent>
          {error && (
            <Alert
              severity="error"
              sx={{
                mb: 2,
                background: 'rgba(239, 68, 68, 0.1)',
                color: '#ef4444',
                border: '1px solid rgba(239, 68, 68, 0.2)',
              }}
            >
              {error}
            </Alert>
          )}
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}>
              Username *
            </Typography>
            <TextField
              fullWidth
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="Enter username"
              sx={{
                mb: 2,
                '& .MuiInputBase-root': {
                  background: 'var(--gpt-input-bg)',
                  color: 'var(--gpt-text)',
                },
              }}
            />
            <Typography variant="body2" sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}>
              Email *
            </Typography>
            <TextField
              fullWidth
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="Enter email"
              sx={{
                mb: 2,
                '& .MuiInputBase-root': {
                  background: 'var(--gpt-input-bg)',
                  color: 'var(--gpt-text)',
                },
              }}
            />
            <Typography variant="body2" sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}>
              Password (leave blank to keep current)
            </Typography>
            <TextField
              fullWidth
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="Enter new password"
              sx={{
                mb: 2,
                '& .MuiInputBase-root': {
                  background: 'var(--gpt-input-bg)',
                  color: 'var(--gpt-text)',
                },
              }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': {
                      color: 'var(--gpt-accent)',
                    },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                      backgroundColor: 'var(--gpt-accent)',
                    },
                  }}
                />
              }
              label={<Typography sx={{ color: 'var(--gpt-text)' }}>Active</Typography>}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button
            onClick={() => setEditDialog(false)}
            startIcon={<X size={18} />}
            sx={{ color: 'var(--gpt-text-secondary)', textTransform: 'none' }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveEdit}
            variant="contained"
            startIcon={<Save size={18} />}
            sx={{
              background: 'var(--gpt-accent)',
              textTransform: 'none',
              '&:hover': {
                background: 'var(--gpt-accent-hover)',
              },
            }}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default function UsersPage() {
  return (
    <AdminProtectedRoute>
      <UsersPageContent />
    </AdminProtectedRoute>
  );
}
