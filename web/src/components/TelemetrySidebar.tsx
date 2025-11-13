/**
 * TelemetrySidebar Component
 *
 * Telemetry gauges showing system vitals:
 * - Market RPM (volatility)
 * - Mental State
 * - Spread Stability
 * - DLL Remaining (fuel gauge)
 * - Confidence Score
 * - Execution Quality
 */

import { motion } from 'framer-motion';
import { Activity, Brain, Zap, Droplet, Target, CheckCircle } from 'lucide-react';

interface TelemetryData {
  marketRPM: number;        // 0-100 (ATR percentile)
  mentalState: number;      // 1-5
  spreadStability: number;  // 0-100
  dllRemaining: number;     // 0-2 R
  confidenceScore: number;  // 0-1
  executionQuality: number; // 0-1
}

interface TelemetrySidebarProps {
  data: TelemetryData;
  className?: string;
}

// Gauge component
function Gauge({
  value,
  max,
  label,
  unit = '',
  icon: Icon,
  color = 'blue',
  size = 'md'
}: {
  value: number;
  max: number;
  label: string;
  unit?: string;
  icon: any;
  color?: 'red' | 'yellow' | 'green' | 'blue' | 'purple';
  size?: 'sm' | 'md' | 'lg';
}) {
  const percentage = Math.min((value / max) * 100, 100);

  const colorMap = {
    red: { bg: 'from-red-500 to-red-600', glow: 'shadow-[0_0_20px_rgba(239,68,68,0.5)]' },
    yellow: { bg: 'from-yellow-500 to-yellow-600', glow: 'shadow-[0_0_20px_rgba(234,179,8,0.5)]' },
    green: { bg: 'from-green-500 to-green-600', glow: 'shadow-[0_0_20px_rgba(34,197,94,0.5)]' },
    blue: { bg: 'from-blue-500 to-blue-600', glow: 'shadow-[0_0_20px_rgba(59,130,246,0.5)]' },
    purple: { bg: 'from-purple-500 to-purple-600', glow: 'shadow-[0_0_20px_rgba(168,85,247,0.5)]' }
  };

  const sizeMap = {
    sm: { container: 'h-16', value: 'text-xl', label: 'text-xs' },
    md: { container: 'h-24', value: 'text-2xl', label: 'text-sm' },
    lg: { container: 'h-32', value: 'text-3xl', label: 'text-base' }
  };

  const colors = colorMap[color];
  const sizes = sizeMap[size];

  return (
    <motion.div
      className="glass rounded-2xl p-4 hover-lift"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 text-${color}-500`} />
          <span className={`${sizes.label} font-medium text-gray-300 uppercase tracking-wider`}>
            {label}
          </span>
        </div>
      </div>

      {/* Circular gauge */}
      <div className={`relative ${sizes.container} flex items-center justify-center`}>
        {/* Background circle */}
        <svg className="absolute inset-0 w-full h-full transform -rotate-90">
          <circle
            cx="50%"
            cy="50%"
            r="40%"
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="8"
          />
          {/* Progress arc */}
          <motion.circle
            cx="50%"
            cy="50%"
            r="40%"
            fill="none"
            stroke={`url(#gradient-${color})`}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 40}, ${2 * Math.PI * 40}`}
            strokeDashoffset={2 * Math.PI * 40 * (1 - percentage / 100)}
            initial={{ strokeDashoffset: 2 * Math.PI * 40 }}
            animate={{ strokeDashoffset: 2 * Math.PI * 40 * (1 - percentage / 100) }}
            transition={{ duration: 1, ease: "easeOut" }}
            className={colors.glow}
          />
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={`var(--${color}-500)`} />
              <stop offset="100%" stopColor={`var(--${color}-600)`} />
            </linearGradient>
          </defs>
        </svg>

        {/* Center value */}
        <div className="relative z-10 text-center">
          <motion.div
            className={`${sizes.value} font-bold text-${color}-500`}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            {value.toFixed(value >= 10 ? 0 : 1)}{unit}
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}

// DLL Fuel Gauge (special horizontal gauge)
function FuelGauge({ value, max, label }: { value: number; max: number; label: string }) {
  const percentage = Math.min((value / max) * 100, 100);
  const isLow = percentage < 30;
  const isCritical = percentage < 15;

  return (
    <motion.div
      className="glass rounded-2xl p-4 hover-lift"
      whileHover={{ scale: 1.02 }}
      animate={isCritical ? { scale: [1, 1.02, 1] } : {}}
      transition={isCritical ? { duration: 1, repeat: Infinity } : { duration: 0.2 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Droplet className={`w-4 h-4 ${isCritical ? 'text-red-500' : isLow ? 'text-yellow-500' : 'text-green-500'}`} />
          <span className="text-sm font-medium text-gray-300 uppercase tracking-wider">
            {label}
          </span>
        </div>
        <span className={`text-lg font-bold ${isCritical ? 'text-red-500' : isLow ? 'text-yellow-500' : 'text-green-500'}`}>
          {value.toFixed(2)}R
        </span>
      </div>

      {/* Horizontal bar */}
      <div className="relative h-3 bg-white/10 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${
            isCritical ? 'bg-gradient-to-r from-red-500 to-red-600' :
            isLow ? 'bg-gradient-to-r from-yellow-500 to-yellow-600' :
            'bg-gradient-to-r from-green-500 to-green-600'
          }`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />

        {/* Glow effect */}
        {isCritical && (
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-red-500/50 to-transparent"
            animate={{ opacity: [0.5, 0.8, 0.5] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        )}
      </div>
    </motion.div>
  );
}

export function TelemetrySidebar({ data, className = '' }: TelemetrySidebarProps) {
  // Determine colors based on values
  const mentalColor = data.mentalState >= 4 ? 'green' : data.mentalState >= 3 ? 'blue' : data.mentalState >= 2 ? 'yellow' : 'red';
  const rpmColor = data.marketRPM >= 80 ? 'red' : data.marketRPM >= 60 ? 'yellow' : 'green';
  const spreadColor = data.spreadStability >= 80 ? 'green' : data.spreadStability >= 60 ? 'yellow' : 'red';

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="glass rounded-2xl p-4">
        <h3 className="text-lg font-bold text-gradient mb-1">System Telemetry</h3>
        <p className="text-xs text-gray-400">Live system vitals</p>
      </div>

      {/* Market RPM (Volatility) */}
      <Gauge
        value={data.marketRPM}
        max={100}
        label="Market RPM"
        unit="%"
        icon={Activity}
        color={rpmColor}
        size="md"
      />

      {/* Mental State */}
      <Gauge
        value={data.mentalState}
        max={5}
        label="Mental State"
        unit="/5"
        icon={Brain}
        color={mentalColor}
        size="md"
      />

      {/* Spread Stability */}
      <Gauge
        value={data.spreadStability}
        max={100}
        label="Spread Stability"
        unit="%"
        icon={Zap}
        color={spreadColor}
        size="sm"
      />

      {/* DLL Remaining (Fuel Gauge) */}
      <FuelGauge
        value={data.dllRemaining}
        max={2.0}
        label="DLL Remaining"
      />

      {/* Confidence Score */}
      <Gauge
        value={data.confidenceScore * 100}
        max={100}
        label="Confidence"
        unit="%"
        icon={Target}
        color="purple"
        size="sm"
      />

      {/* Execution Quality */}
      <Gauge
        value={data.executionQuality * 100}
        max={100}
        label="Execution Quality"
        unit="%"
        icon={CheckCircle}
        color="blue"
        size="sm"
      />
    </div>
  );
}
