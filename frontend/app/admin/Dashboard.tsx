'use client';

import { useEffect, useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  Box,
  CircularProgress
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { TrendingUp, AlertCircle, Activity } from 'lucide-react';

interface MetricsData {
  request_volume: {
    requests_1h: number;
    requests_24h: number;
    rpm: number;
    chart_data: any[];
  };
  error_rate: {
    errors_24h: number;
    error_rate_percent: number;
    top_errors: any[];
  };
  business_metrics: {
    affiliate_ctr: number;
    travel_ctr: number;
    travel_impressions: number;
    cost_per_query: number;
  };
  top_queries: {
    popular: Array<{ query: string; count: number }>;
    expensive: any[];
  };
}

interface ChartData {
  data: Array<{ time: string; count: number }>;
  timeframe: string;
}

const MetricCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: any;
  color: string;
}) => (
  <Card
    sx={{
      height: '100%',
      background: 'var(--gpt-background)',
      border: '1px solid var(--gpt-border)',
      boxShadow: 'var(--gpt-shadow-md)',
      '&:hover': {
        boxShadow: 'var(--gpt-shadow-lg)',
        transform: 'translateY(-2px)',
        transition: 'all 0.2s'
      }
    }}
  >
    <CardContent>
      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
        <Box>
          <Typography
            variant="body2"
            sx={{ color: 'var(--gpt-text-secondary)', mb: 1 }}
          >
            {title}
          </Typography>
          <Typography
            variant="h4"
            sx={{
              color: 'var(--gpt-text)',
              fontWeight: 600,
              mb: 0.5
            }}
          >
            {value}
          </Typography>
          {subtitle && (
            <Typography
              variant="caption"
              sx={{ color: 'var(--gpt-text-muted)' }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box
          sx={{
            p: 1.5,
            borderRadius: 2,
            background: `${color}20`,
            color: color
          }}
        >
          <Icon size={24} />
        </Box>
      </Box>
    </CardContent>
  </Card>
);

export default function Dashboard() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [requestChartData, setRequestChartData] = useState<ChartData | null>(null);
  const [errorChartData, setErrorChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/v1/admin/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const fetchRequestChartData = async () => {
    try {
      const response = await fetch('http://localhost:8000/v1/admin/metrics/chart?timeframe=24h');
      const data = await response.json();
      setRequestChartData(data);
    } catch (error) {
      console.error('Error fetching request chart data:', error);
    }
  };

  const fetchErrorChartData = async () => {
    try {
      const response = await fetch('http://localhost:8000/v1/admin/metrics/errors/chart?timeframe=24h');
      const data = await response.json();
      setErrorChartData(data);
    } catch (error) {
      console.error('Error fetching error chart data:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchMetrics(), fetchRequestChartData(), fetchErrorChartData()]);
      setLoading(false);
    };

    loadData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchMetrics();
      fetchRequestChartData();
      fetchErrorChartData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  if (loading || !metrics) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress sx={{ color: 'var(--gpt-accent)' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, background: 'var(--gpt-background)', minHeight: '100vh' }}>
      <Typography
        variant="h4"
        sx={{
          mb: 3,
          color: 'var(--gpt-text)',
          fontWeight: 600
        }}
      >
        Admin Dashboard
      </Typography>

      {/* Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Requests (1 Hour)"
            value={metrics.request_volume.requests_1h}
            subtitle={`${metrics.request_volume.rpm} req/min`}
            icon={Activity}
            color="var(--gpt-accent)"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Requests (24 Hours)"
            value={metrics.request_volume.requests_24h}
            subtitle="Total requests"
            icon={TrendingUp}
            color="var(--gpt-accent-teal)"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Errors (24 Hours)"
            value={metrics.error_rate.errors_24h}
            subtitle="Total errors"
            icon={AlertCircle}
            color="#ef4444"
          />
        </Grid>
      </Grid>

      {/* Request Volume Chart (24h) - Full Width */}
      <Card
        sx={{
          background: 'var(--gpt-background)',
          border: '1px solid var(--gpt-border)',
          boxShadow: 'var(--gpt-shadow-md)',
          mb: 3
        }}
      >
        <CardHeader
          title={
            <Typography variant="h6" sx={{ color: 'var(--gpt-text)' }}>
              Request Volume (24 Hours)
            </Typography>
          }
        />
        <CardContent>
          <ResponsiveContainer width="100%" height={600}>
            <LineChart data={requestChartData?.data || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--gpt-border)" />
              <XAxis
                dataKey="time"
                stroke="var(--gpt-text-secondary)"
                tick={{ fill: 'var(--gpt-text-secondary)', fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
                }}
              />
              <YAxis
                stroke="var(--gpt-text-secondary)"
                tick={{ fill: 'var(--gpt-text-secondary)' }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--gpt-sidebar)',
                  border: '1px solid var(--gpt-border)',
                  borderRadius: '8px',
                  color: 'var(--gpt-text)'
                }}
                labelFormatter={(value) => new Date(value).toLocaleString()}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="var(--gpt-accent)"
                strokeWidth={2}
                name="User Requests"
                dot={false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Error Rate Chart (24h) - Full Width */}
      <Card
        sx={{
          background: 'var(--gpt-background)',
          border: '1px solid var(--gpt-border)',
          boxShadow: 'var(--gpt-shadow-md)',
          mb: 4
        }}
      >
        <CardHeader
          title={
            <Typography variant="h6" sx={{ color: 'var(--gpt-text)' }}>
              Error Rate (24 Hours)
            </Typography>
          }
        />
        <CardContent>
          <ResponsiveContainer width="100%" height={600}>
            <LineChart data={errorChartData?.data || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--gpt-border)" />
              <XAxis
                dataKey="time"
                stroke="var(--gpt-text-secondary)"
                tick={{ fill: 'var(--gpt-text-secondary)', fontSize: 12 }}
                tickFormatter={(value) => {
                  const date = new Date(value);
                  return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
                }}
              />
              <YAxis
                stroke="var(--gpt-text-secondary)"
                tick={{ fill: 'var(--gpt-text-secondary)' }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--gpt-sidebar)',
                  border: '1px solid var(--gpt-border)',
                  borderRadius: '8px',
                  color: 'var(--gpt-text)'
                }}
                labelFormatter={(value) => new Date(value).toLocaleString()}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#ef4444"
                strokeWidth={2}
                name="Errors"
                dot={false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

    </Box>
  );
}
