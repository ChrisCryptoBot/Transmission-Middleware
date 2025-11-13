/**
 * Left Sidebar Navigation
 * Based on UI_Concept.txt section 8.1
 */

import { NavLink } from 'react-router-dom';
import { GlassCard } from './ui/GlassCard';
import {
  LayoutDashboard,
  Gauge,
  TrendingUp,
  BarChart3,
  Shield,
  Zap,
  Activity,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  className?: string;
}

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/transmission', label: 'Odds / Transmission', icon: Gauge },
  { path: '/strategies', label: 'Strategies', icon: TrendingUp },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/risk', label: 'Risk', icon: Shield },
  { path: '/execution', label: 'Execution', icon: Zap },
  { path: '/system', label: 'System Health', icon: Activity },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar({ className }: SidebarProps) {
  return (
    <aside className={cn('w-64 flex-shrink-0', className)}>
      <GlassCard padding="sm" className="h-full">
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-gradient-to-r from-purple-500/80 to-blue-500/80 text-white shadow-lg'
                    : 'text-white/60 hover:bg-white/10 hover:text-white'
                )
              }
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </GlassCard>
    </aside>
  );
}

