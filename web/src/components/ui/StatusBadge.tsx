interface StatusBadgeProps {
  status: string;
  color: 'green' | 'yellow' | 'red' | 'blue' | 'purple';
}

export function StatusBadge({ status, color }: StatusBadgeProps) {
  const colorClasses = {
    green: 'bg-emerald-500/20 border-emerald-400/30 text-emerald-100',
    yellow: 'bg-yellow-500/20 border-yellow-400/30 text-yellow-100',
    red: 'bg-red-500/20 border-red-400/30 text-red-100',
    blue: 'bg-blue-500/20 border-blue-400/30 text-blue-100',
    purple: 'bg-purple-500/20 border-purple-400/30 text-purple-100',
  };

  return (
    <span
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium backdrop-blur-md border transition-all duration-200 ${colorClasses[color]}`}
    >
      {status}
    </span>
  );
}

