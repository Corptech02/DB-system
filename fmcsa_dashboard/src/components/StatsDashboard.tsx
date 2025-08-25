import React from 'react';
import { useQuery } from 'react-query';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, Users, AlertTriangle, Shield, Truck } from 'lucide-react';
import api from '../services/api';

const StatsDashboard: React.FC = () => {
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery(
    'statistics',
    () => api.getStatistics(),
    {
      onError: (error) => console.error('Stats error:', error),
      retry: 1
    }
  );
  
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useQuery(
    'summary-stats',
    () => api.getSummaryStats(),
    {
      onError: (error) => console.error('Summary error:', error),
      retry: 1
    }
  );
  
  const { data: topStates, isLoading: statesLoading, error: statesError } = useQuery(
    'top-states',
    () => api.getTopStates(10),
    {
      onError: (error) => console.error('Top states error:', error),
      retry: 1
    }
  );
  
  const { data: forecast, isLoading: forecastLoading, error: forecastError } = useQuery(
    'insurance-forecast',
    () => api.getInsuranceForecast(90),
    {
      onError: (error) => console.error('Forecast error:', error),
      retry: 1
    }
  );
  
  // Log for debugging
  console.log('Stats Dashboard State:', {
    statsLoading,
    summaryLoading,
    statsError,
    summaryError,
    stats,
    summary
  });
  
  if (statsError || summaryError) {
    return (
      <div className="flex flex-col justify-center items-center h-64 space-y-4">
        <div className="text-red-600 text-xl">Error loading statistics</div>
        <div className="text-gray-600">
          {statsError?.message || summaryError?.message || 'Please check if the API server is running'}
        </div>
        <div className="text-sm text-gray-500">
          Make sure the API is running on http://localhost:8000
        </div>
      </div>
    );
  }
  
  if (statsLoading || summaryLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }
  
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
  
  // Prepare data for charts
  const entityTypeData = stats?.by_entity_type
    ? Object.entries(stats.by_entity_type).map(([type, count]) => ({
        name: type,
        value: count as number,
      }))
    : [];
  
  const insuranceData = [
    { name: 'Valid', value: stats?.insurance_stats?.valid || 0, color: '#10b981' },
    { name: 'Expiring 30d', value: stats?.insurance_stats?.expiring_30_days || 0, color: '#f59e0b' },
    { name: 'Expiring 60d', value: stats?.insurance_stats?.expiring_60_days || 0, color: '#fb923c' },
    { name: 'Expiring 90d', value: stats?.insurance_stats?.expiring_90_days || 0, color: '#fbbf24' },
    { name: 'Expired', value: stats?.insurance_stats?.expired || 0, color: '#ef4444' },
    { name: 'Unknown', value: stats?.insurance_stats?.unknown || 0, color: '#9ca3af' },
  ];
  
  const forecastData = forecast
    ? [
        { period: 'Week 1', carriers: forecast.expiring_week_1 || 0 },
        { period: 'Week 2', carriers: forecast.expiring_week_2 || 0 },
        { period: 'Month 1', carriers: forecast.expiring_month_1 || 0 },
        { period: 'Month 2', carriers: forecast.expiring_month_2 || 0 },
        { period: 'Month 3', carriers: forecast.expiring_month_3 || 0 },
      ]
    : [];
  
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Carriers</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary?.total_carriers?.toLocaleString() || 0}
              </p>
            </div>
            <Users className="w-8 h-8 text-primary-500" />
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Carriers</p>
              <p className="text-2xl font-bold text-success-600">
                {summary?.active_carriers?.toLocaleString() || 0}
              </p>
              <p className="text-xs text-gray-500">
                {summary?.total_carriers > 0 
                  ? `${((summary.active_carriers / summary.total_carriers) * 100).toFixed(1)}% of total`
                  : 'N/A'}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-success-500" />
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Expired Insurance</p>
              <p className="text-2xl font-bold text-danger-600">
                {summary?.expired_insurance?.toLocaleString() || 0}
              </p>
              <p className="text-xs text-warning-600">
                +{summary?.expiring_soon || 0} expiring soon
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-danger-500" />
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Hazmat Carriers</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary?.hazmat_carriers?.toLocaleString() || 0}
              </p>
              <p className="text-xs text-gray-500">
                {summary?.states_covered || 0} states covered
              </p>
            </div>
            <Shield className="w-8 h-8 text-warning-500" />
          </div>
        </div>
      </div>
      
      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top States */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Top States by Carrier Count</h3>
          {topStates && topStates.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topStates}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="state" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total_carriers" fill="#3b82f6" />
                <Bar dataKey="active_carriers" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              {statesLoading ? 'Loading...' : 'No data available'}
            </div>
          )}
        </div>
        
        {/* Entity Type Distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Entity Type Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={entityTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {entityTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Insurance Status */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Insurance Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={insuranceData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toLocaleString()}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {insuranceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        {/* Insurance Expiration Forecast */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Insurance Expiration Forecast</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="carriers" stroke="#f59e0b" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* Additional Stats */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Fleet Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-600">Average Power Units</p>
            <p className="text-xl font-bold">{stats?.avg_power_units?.toFixed(1) || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Average Drivers</p>
            <p className="text-xl font-bold">{stats?.avg_drivers?.toFixed(1) || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Last Updated</p>
            <p className="text-xl font-bold">
              {stats?.last_updated
                ? new Date(stats.last_updated).toLocaleDateString()
                : 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatsDashboard;