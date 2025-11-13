/**
 * GlassCard - Glassmorphism card component
 * Based on UI_Concept.txt design system
 */

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: 'sm' | 'md' | 'lg';
}

export function GlassCard({ children, className, hover = false, padding = 'md' }: GlassCardProps) {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={cn(
        'glass rounded-2xl',
        paddingClasses[padding],
        'border border-white/10',
        'shadow-[0_8px_32px_0_rgba(0,0,0,0.1),0_2px_8px_0_rgba(0,0,0,0.05)]',
        hover && 'transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_12px_48px_0_rgba(0,0,0,0.15)] hover:bg-black/50',
        className
      )}
    >
      {children}
    </div>
  );
}

