import { cn } from '@/lib/utils';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export function GlassCard({ children, className = '', hover = false }: GlassCardProps) {
  return (
    <div
      className={cn(
        'relative rounded-2xl p-6 bg-white/10 backdrop-blur-md border border-white/20',
        'shadow-[0_8px_32px_0_rgba(0,0,0,0.1),0_2px_8px_0_rgba(0,0,0,0.05)]',
        hover && 'transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_12px_48px_0_rgba(0,0,0,0.15)] hover:bg-white/15',
        className
      )}
    >
      {children}
    </div>
  );
}

