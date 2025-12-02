import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Server,
  Database,
  HardDrive,
  Clock,
  Info,
} from 'lucide-react';
import { adminApi } from '../../services/api';

const StatusIcon = ({ status }) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="text-green-500" size={24} />;
    case 'degraded':
      return <AlertTriangle className="text-yellow-500" size={24} />;
    case 'unhealthy':
      return <XCircle className="text-red-500" size={24} />;
    default:
      return <Info className="text-gray-500" size={24} />;
  }
};

const StatusBadge = ({ status }) => {
  const colors = {
    healthy: 'bg-green-500/20 text-green-500 border-green-500/30',
    degraded: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
    unhealthy: 'bg-red-500/20 text-red-500 border-red-500/30',
  };

  return (
    <span
      className={`px-3 py-1 rounded-full text-sm font-medium border ${colors[status] || 'bg-gray-500/20 text-gray-500 border-gray-500/30'}`}
    >
      {status?.charAt(0).toUpperCase() + status?.slice(1)}
    </span>
  );
};

const formatUptime = seconds => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

  return parts.join(' ');
};

const ServiceCard = ({ title, icon: Icon, status, message, responseTime }) => {
  return (
    <div className="bg-[var(--bg-secondary)] rounded-lg p-6 border border-[var(--border-color)]">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[var(--bg-primary)] rounded-lg">
            <Icon size={24} className="text-[var(--text-secondary)]" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h3>
            <p className="text-sm text-[var(--text-secondary)]">{message}</p>
          </div>
        </div>
        <StatusIcon status={status} />
      </div>
      <div className="flex items-center justify-between">
        <StatusBadge status={status} />
        {responseTime !== null && responseTime !== undefined && (
          <span className="text-sm text-[var(--text-secondary)]">{responseTime}ms response time</span>
        )}
      </div>
    </div>
  );
};

const AdminSystemTab = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const {
    data: systemStatus,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['admin-system-status'],
    queryFn: async () => {
      const response = await adminApi.getSystemStatus();
      return response.data;
    },
    refetchInterval: 60000, // Refresh every 60 seconds
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="animate-spin text-[var(--text-secondary)]" size={32} />
        <span className="ml-3 text-[var(--text-secondary)]">Loading system status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
        <XCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
        <div>
          <p className="text-red-500 font-medium">Failed to load system status</p>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            {error.message || 'An error occurred while fetching system status.'}
          </p>
          <button
            onClick={handleRefresh}
            className="mt-3 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Refresh Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">System Status</h2>
          <p className="text-sm text-[var(--text-secondary)]">
            Monitor the health and status of your system components
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            isRefreshing
              ? 'bg-gray-500 cursor-not-allowed opacity-50'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          <RefreshCw size={18} className={isRefreshing ? 'animate-spin' : ''} />
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-3 mb-2">
            <Clock size={20} className="text-[var(--text-secondary)]" />
            <span className="text-sm text-[var(--text-secondary)]">Uptime</span>
          </div>
          <p className="text-xl font-semibold text-[var(--text-primary)]">
            {formatUptime(systemStatus?.uptime_seconds || 0)}
          </p>
        </div>

        <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-3 mb-2">
            <Info size={20} className="text-[var(--text-secondary)]" />
            <span className="text-sm text-[var(--text-secondary)]">Version</span>
          </div>
          <p className="text-xl font-semibold text-[var(--text-primary)]">
            {systemStatus?.version || 'Unknown'}
          </p>
        </div>

        <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-3 mb-2">
            <Clock size={20} className="text-[var(--text-secondary)]" />
            <span className="text-sm text-[var(--text-secondary)]">Last Checked</span>
          </div>
          <p className="text-sm font-medium text-[var(--text-primary)]">
            {systemStatus?.timestamp
              ? new Date(systemStatus.timestamp).toLocaleString()
              : 'Unknown'}
          </p>
        </div>

        <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-3 mb-2">
            <Server size={20} className="text-[var(--text-secondary)]" />
            <span className="text-sm text-[var(--text-secondary)]">Overall Status</span>
          </div>
          <div className="flex items-center gap-2">
            {systemStatus?.backend?.status === 'healthy' &&
            systemStatus?.database?.status === 'healthy' ? (
              <>
                <CheckCircle className="text-green-500" size={20} />
                <span className="text-green-500 font-medium">All Systems Operational</span>
              </>
            ) : (
              <>
                <AlertTriangle className="text-yellow-500" size={20} />
                <span className="text-yellow-500 font-medium">Some Issues Detected</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Service Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ServiceCard
          title="Backend"
          icon={Server}
          status={systemStatus?.backend?.status}
          message={systemStatus?.backend?.message}
          responseTime={systemStatus?.backend?.response_time_ms}
        />
        <ServiceCard
          title="Database"
          icon={Database}
          status={systemStatus?.database?.status}
          message={systemStatus?.database?.message}
          responseTime={systemStatus?.database?.response_time_ms}
        />
        <ServiceCard
          title="Redis Cache"
          icon={HardDrive}
          status={systemStatus?.redis?.status}
          message={systemStatus?.redis?.message}
          responseTime={systemStatus?.redis?.response_time_ms}
        />
      </div>

      {/* Status Legend */}
      <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border-color)]">
        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-3">Status Legend</h3>
        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-2">
            <CheckCircle className="text-green-500" size={18} />
            <span className="text-sm text-[var(--text-secondary)]">
              Healthy - Service is operating normally
            </span>
          </div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-yellow-500" size={18} />
            <span className="text-sm text-[var(--text-secondary)]">
              Degraded - Service is functional but with issues
            </span>
          </div>
          <div className="flex items-center gap-2">
            <XCircle className="text-red-500" size={18} />
            <span className="text-sm text-[var(--text-secondary)]">
              Unhealthy - Service is not functioning properly
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminSystemTab;
