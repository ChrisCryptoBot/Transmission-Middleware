/**
 * Performance Charts Component
 *
 * Visualizes trading performance with:
 * 1. Cumulative P&L curve (R multiples)
 * 2. Drawdown chart (underwater curve)
 * 3. Heatmaps (weekday/hour performance)
 *
 * Uses Recharts for beautiful, responsive visualizations
 */

import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Card } from './ui/card';
import { api } from '@/lib/api';

interface Trade {
  trade_id: number;
  entry_timestamp: string;
  exit_timestamp: string;
  result_r: number;
  cumulative_r: number;
  drawdown_r: number;
  trade_type: string;
  strategy_used: string;
  symbol: string;
}

interface MetricsData {
  profit_factor: number;
  win_rate: number;
  expected_r: number;
  max_drawdown_r: number;
  total_trades: number;
  total_r: number;
}

export function PerformanceCharts() {
  // Fetch trades for charts
  const { data: tradesData, isLoading: tradesLoading } = useQuery({
    queryKey: ['trades'],
    queryFn: async () => {
      const response = await api.get<{ trades: Trade[] }>('/trades');
      return response.data.trades;
    },
    refetchInterval: 30000, // Refresh every 30s
  });

  // Fetch performance metrics
  const { data: metricsData } = useQuery({
    queryKey: ['metrics'],
    queryFn: async () => {
      const response = await api.get<MetricsData>('/metrics');
      return response.data;
    },
    refetchInterval: 30000,
  });

  if (tradesLoading || !tradesData) {
    return (
      <div className="space-y-6">
        <div className="h-96 glass rounded-2xl p-8 flex items-center justify-center">
          <div className="text-white/60">Loading performance data...</div>
        </div>
      </div>
    );
  }

  // Process trades for charts
  const chartData = tradesData.map((trade, index) => {
    // Calculate cumulative R (sum of all previous trades)
    const cumulative_r = tradesData
      .slice(0, index + 1)
      .reduce((sum, t) => sum + (t.result_r || 0), 0);

    // Calculate drawdown (distance from peak)
    const peak_r = Math.max(...tradesData.slice(0, index + 1).map((t) =>
      tradesData.slice(0, tradesData.indexOf(t) + 1)
        .reduce((sum, prev) => sum + (prev.result_r || 0), 0)
    ));
    const drawdown_r = cumulative_r - peak_r;

    return {
      trade_number: index + 1,
      date: new Date(trade.exit_timestamp || trade.entry_timestamp).toLocaleDateString(),
      cumulative_r: parseFloat(cumulative_r.toFixed(2)),
      drawdown_r: parseFloat(drawdown_r.toFixed(2)),
      result_r: trade.result_r,
      strategy: trade.strategy_used,
      symbol: trade.symbol,
    };
  });

  const metrics = metricsData || {
    profit_factor: 0,
    win_rate: 0,
    expected_r: 0,
    max_drawdown_r: 0,
    total_trades: tradesData.length,
    total_r: chartData[chartData.length - 1]?.cumulative_r || 0,
  };

  return (
    <div className="space-y-6">
      {/* Performance Metrics Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total R"
          value={metrics.total_r?.toFixed(2) || '0.00'}
          color={metrics.total_r >= 0 ? 'text-green-400' : 'text-red-400'}
        />
        <MetricCard
          label="Max Drawdown"
          value={`-${Math.abs(metrics.max_drawdown_r || 0).toFixed(2)}R`}
          color="text-red-400"
        />
        <MetricCard
          label="Profit Factor"
          value={metrics.profit_factor?.toFixed(2) || '0.00'}
          color={metrics.profit_factor >= 1.5 ? 'text-green-400' : 'text-yellow-400'}
        />
        <MetricCard
          label="Win Rate"
          value={`${(metrics.win_rate * 100).toFixed(1)}%`}
          color={metrics.win_rate >= 0.5 ? 'text-green-400' : 'text-yellow-400'}
        />
      </div>

      {/* Cumulative P&L Chart */}
      <Card className="glass p-6">
        <h3 className="text-xl font-semibold text-white mb-4">
          Cumulative P&L (R Multiples)
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="date"
              stroke="rgba(255,255,255,0.5)"
              tick={{ fill: 'rgba(255,255,255,0.7)' }}
            />
            <YAxis
              stroke="rgba(255,255,255,0.5)"
              tick={{ fill: 'rgba(255,255,255,0.7)' }}
              label={{ value: 'R Multiples', angle: -90, position: 'insideLeft', fill: 'white' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '8px',
                backdropFilter: 'blur(10px)',
              }}
              labelStyle={{ color: 'white' }}
              itemStyle={{ color: 'white' }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="cumulative_r"
              name="Cumulative R"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              animationDuration={1000}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Drawdown Chart */}
      <Card className="glass p-6">
        <h3 className="text-xl font-semibold text-white mb-4">
          Drawdown (Underwater Curve)
        </h3>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="date"
              stroke="rgba(255,255,255,0.5)"
              tick={{ fill: 'rgba(255,255,255,0.7)' }}
            />
            <YAxis
              stroke="rgba(255,255,255,0.5)"
              tick={{ fill: 'rgba(255,255,255,0.7)' }}
              label={{ value: 'Drawdown (R)', angle: -90, position: 'insideLeft', fill: 'white' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '8px',
                backdropFilter: 'blur(10px)',
              }}
              labelStyle={{ color: 'white' }}
              itemStyle={{ color: 'white' }}
            />
            <Area
              type="monotone"
              dataKey="drawdown_r"
              name="Drawdown"
              stroke="#ef4444"
              fill="url(#colorDrawdown)"
              animationDuration={1000}
            />
            <defs>
              <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
              </linearGradient>
            </defs>
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      {/* Trade Statistics Table */}
      <Card className="glass p-6">
        <h3 className="text-xl font-semibold text-white mb-4">
          Recent Trades
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/10">
                <th className="py-2 px-4 text-white/70">#</th>
                <th className="py-2 px-4 text-white/70">Date</th>
                <th className="py-2 px-4 text-white/70">Symbol</th>
                <th className="py-2 px-4 text-white/70">Strategy</th>
                <th className="py-2 px-4 text-white/70 text-right">Result (R)</th>
                <th className="py-2 px-4 text-white/70 text-right">Cumulative (R)</th>
              </tr>
            </thead>
            <tbody>
              {chartData.slice(-10).reverse().map((trade) => (
                <tr key={trade.trade_number} className="border-b border-white/5 hover:bg-white/5">
                  <td className="py-2 px-4 text-white/90">{trade.trade_number}</td>
                  <td className="py-2 px-4 text-white/90">{trade.date}</td>
                  <td className="py-2 px-4 text-white/90">{trade.symbol}</td>
                  <td className="py-2 px-4 text-white/90">{trade.strategy}</td>
                  <td className={`py-2 px-4 text-right font-semibold ${
                    trade.result_r >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.result_r >= 0 ? '+' : ''}{trade.result_r?.toFixed(2)}R
                  </td>
                  <td className="py-2 px-4 text-right text-white/90">
                    {trade.cumulative_r?.toFixed(2)}R
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="glass rounded-lg p-4">
      <div className="text-white/60 text-sm mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
