'use client';

import { useEffect, useState } from 'react';
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
  CircularProgress
} from '@mui/material';
import { Edit, Trash2, Save, X } from 'lucide-react';

interface ConfigItem {
  id: number | null;
  key: string;
  value: string;
  source: 'db' | 'env';
  created_at?: string;
  updated_at?: string;
}

export default function ConfigManagement() {
  const [configs, setConfigs] = useState<ConfigItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editDialog, setEditDialog] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<ConfigItem | null>(null);
  const [editValue, setEditValue] = useState('');
  const [clearingCache, setClearingCache] = useState(false);

  const fetchConfigs = async () => {
    try {
      const response = await fetch('http://localhost:8000/v1/admin/config');
      const data = await response.json();
      setConfigs(data);
    } catch (error) {
      console.error('Error fetching configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    if (!confirm('Clear all config cache from Redis? Configs will be re-cached from database on next access.')) {
      return;
    }

    setClearingCache(true);
    try {
      const response = await fetch('http://localhost:8000/v1/admin/config/clear-cache', {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        alert(data.message || 'Cache cleared successfully');
      } else {
        alert('Failed to clear cache');
      }
    } catch (error) {
      console.error('Error clearing cache:', error);
      alert('Error clearing cache');
    } finally {
      setClearingCache(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  const handleEdit = (config: ConfigItem) => {
    setSelectedConfig(config);
    setEditValue(config.value);
    setEditDialog(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedConfig || !selectedConfig.id) return;

    try {
      const response = await fetch(`http://localhost:8000/v1/admin/config/${selectedConfig.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: editValue })
      });

      if (response.ok) {
        await fetchConfigs();
        setEditDialog(false);
        setSelectedConfig(null);
        setEditValue('');
      }
    } catch (error) {
      console.error('Error updating config:', error);
    }
  };

  const handleDelete = async (config: ConfigItem) => {
    if (!config.id || config.source === 'env') return;

    if (confirm(`Reset ${config.key} to .env default?`)) {
      try {
        const response = await fetch(`http://localhost:8000/v1/admin/config/${config.id}`, {
          method: 'DELETE'
        });

        if (response.ok) {
          await fetchConfigs();
        }
      } catch (error) {
        console.error('Error deleting config:', error);
      }
    }
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
          Configuration Management
        </Typography>
        <Button
          variant="outlined"
          onClick={handleClearCache}
          disabled={clearingCache}
          sx={{
            borderColor: 'var(--gpt-accent)',
            color: 'var(--gpt-accent)',
            '&:hover': {
              borderColor: 'var(--gpt-accent)',
              background: 'var(--gpt-accent-light)'
            }
          }}
        >
          {clearingCache ? 'Clearing...' : 'Clear Config Cache'}
        </Button>
      </Box>

      <Card
        sx={{
          background: 'var(--gpt-background)',
          border: '1px solid var(--gpt-border)',
          boxShadow: 'var(--gpt-shadow-md)'
        }}
      >
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ background: 'var(--gpt-sidebar)' }}>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Key</TableCell>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Value</TableCell>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Source</TableCell>
                <TableCell sx={{ color: 'var(--gpt-text)', fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {configs.map((config) => (
                <TableRow
                  key={config.id || config.key}
                  sx={{
                    '&:hover': {
                      background: 'var(--gpt-hover)'
                    }
                  }}
                >
                  <TableCell sx={{ color: 'var(--gpt-text)', fontFamily: 'monospace' }}>
                    {config.key}
                  </TableCell>
                  <TableCell
                    sx={{
                      color: 'var(--gpt-text)',
                      fontFamily: 'monospace',
                      maxWidth: 300,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {config.value}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={config.source.toUpperCase()}
                      size="small"
                      sx={{
                        background: config.source === 'db' ? 'var(--gpt-accent-light)' : 'var(--gpt-hover)',
                        color: config.source === 'db' ? 'var(--gpt-accent)' : 'var(--gpt-text-secondary)',
                        fontWeight: 600
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(config)}
                        disabled={config.source === 'env'}
                        sx={{
                          color: 'var(--gpt-accent)',
                          '&:hover': {
                            background: 'var(--gpt-accent-light)'
                          },
                          '&:disabled': {
                            color: 'var(--gpt-text-muted)'
                          }
                        }}
                      >
                        <Edit size={18} />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(config)}
                        disabled={config.source === 'env'}
                        sx={{
                          color: '#ef4444',
                          '&:hover': {
                            background: 'rgba(239, 68, 68, 0.1)'
                          },
                          '&:disabled': {
                            color: 'var(--gpt-text-muted)'
                          }
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

      {/* Edit Dialog */}
      <Dialog
        open={editDialog}
        onClose={() => setEditDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: 'var(--gpt-background)',
            border: '1px solid var(--gpt-border)'
          }
        }}
      >
        <DialogTitle sx={{ color: 'var(--gpt-text)' }}>
          Edit Configuration
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}>
              Key
            </Typography>
            <TextField
              fullWidth
              value={selectedConfig?.key || ''}
              disabled
              sx={{
                mb: 2,
                '& .MuiInputBase-root': {
                  background: 'var(--gpt-input-bg)',
                  color: 'var(--gpt-text)'
                }
              }}
            />
            <Typography variant="body2" sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}>
              Value
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              sx={{
                '& .MuiInputBase-root': {
                  background: 'var(--gpt-input-bg)',
                  color: 'var(--gpt-text)',
                  fontFamily: 'monospace'
                }
              }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button
            onClick={() => setEditDialog(false)}
            startIcon={<X size={18} />}
            sx={{ color: 'var(--gpt-text-secondary)' }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveEdit}
            variant="contained"
            startIcon={<Save size={18} />}
            sx={{
              background: 'var(--gpt-accent)',
              '&:hover': {
                background: 'var(--gpt-accent-hover)'
              }
            }}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
}
