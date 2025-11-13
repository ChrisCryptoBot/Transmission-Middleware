/**
 * GearIndicator Component
 *
 * Visual representation of the VEGUS gear state (P/R/N/D/L)
 * Animated, glassmorphism design with smooth transitions
 */

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

type GearType = 'P' | 'R' | 'N' | 'D' | 'L';

interface GearIndicatorProps {
  currentGear: GearType;
  reason: string;
  riskMultiplier: number;
  className?: string;
  showDetails?: boolean;
}

// Gear configurations
const GEAR_CONFIG: Record<GearType, {
  label: string;
  color: string;
  glow: string;
  description: string;
}> = {
  P: {
    label: 'PARK',
    color: 'text-red-400',
    glow: 'shadow-[0_0_30px_rgba(248,113,113,0.6)]',
    description: 'Trading locked'
  },
  R: {
    label: 'REVERSE',
    color: 'text-amber-400',
    glow: 'shadow-[0_0_30px_rgba(251,191,36,0.6)]',
    description: 'Recovery mode'
  },
  N: {
    label: 'NEUTRAL',
    color: 'text-neutral-400',
    glow: 'shadow-[0_0_30px_rgba(163,163,163,0.4)]',
    description: 'Standby'
  },
  D: {
    label: 'DRIVE',
    color: 'text-green-400',
    glow: 'shadow-[0_0_30px_rgba(74,222,128,0.6)]',
    description: 'Normal trading'
  },
  L: {
    label: 'LOW',
    color: 'text-blue-400',
    glow: 'shadow-[0_0_30px_rgba(96,165,250,0.6)]',
    description: 'Risk downshifted'
  }
};

export function GearIndicator({
  currentGear,
  reason,
  riskMultiplier,
  className = '',
  showDetails = true
}: GearIndicatorProps) {
  const [isShifting, setIsShifting] = useState(false);
  const [prevGear, setPrevGear] = useState<GearType>(currentGear);

  const config = GEAR_CONFIG[currentGear];

  // Detect gear shifts
  useEffect(() => {
    if (prevGear !== currentGear) {
      setIsShifting(true);
      setTimeout(() => setIsShifting(false), 600);
      setPrevGear(currentGear);
    }
  }, [currentGear, prevGear]);

  return (
    <div className={`relative ${className}`}>
      {/* Main gear display */}
      <div className="relative">
        {/* Glass morphism container */}
        <motion.div
          className={`
            relative overflow-hidden rounded-3xl
            bg-gradient-to-br from-white/10 to-white/5
            backdrop-blur-xl backdrop-saturate-150
            border border-white/20
            ${config.glow}
            transition-shadow duration-500
          `}
          animate={{
            scale: isShifting ? [1, 1.05, 1] : 1,
          }}
          transition={{
            duration: 0.6,
            ease: [0.43, 0.13, 0.23, 0.96]
          }}
        >
          {/* Animated background gradient */}
          <div className="absolute inset-0 opacity-20">
            <motion.div
              className={`absolute inset-0 bg-gradient-to-br ${
                currentGear === 'P' ? 'from-red-400 to-red-600' :
                currentGear === 'R' ? 'from-amber-400 to-amber-600' :
                currentGear === 'N' ? 'from-neutral-400 to-neutral-600' :
                currentGear === 'D' ? 'from-green-400 to-green-600' :
                'from-blue-400 to-blue-600'
              }`}
              animate={{
                opacity: isShifting ? [0.2, 0.4, 0.2] : 0.2,
              }}
              transition={{ duration: 0.6 }}
            />
          </div>

          {/* Content */}
          <div className="relative p-8 text-center">
            {/* Gear letter - large display */}
            <AnimatePresence mode="wait">
              <motion.div
                key={currentGear}
                initial={{ scale: 0.8, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.8, opacity: 0, y: -20 }}
                transition={{
                  duration: 0.4,
                  ease: [0.43, 0.13, 0.23, 0.96]
                }}
                className="mb-2"
              >
                <div className={`text-8xl font-black ${config.color} tracking-wider`}>
                  {currentGear}
                </div>
              </motion.div>
            </AnimatePresence>

            {/* Gear label */}
            <motion.div
              className={`text-xl font-semibold ${config.color} mb-1`}
              animate={{
                opacity: isShifting ? [1, 0.5, 1] : 1,
              }}
            >
              {config.label}
            </motion.div>

            {/* Description */}
            <div className="text-sm text-neutral-400">
              {config.description}
            </div>

            {/* Risk multiplier */}
            <motion.div
              className="mt-4 pt-4 border-t border-white/10"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <div className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
                Position Size
              </div>
              <div className={`text-2xl font-bold ${config.color}`}>
                {(riskMultiplier * 100).toFixed(0)}%
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Shift indicator pulse */}
        <AnimatePresence>
          {isShifting && (
            <motion.div
              className={`absolute inset-0 rounded-3xl border-2 ${config.color.replace('text-', 'border-')}`}
              initial={{ scale: 1, opacity: 0.8 }}
              animate={{ scale: 1.2, opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.6 }}
            />
          )}
        </AnimatePresence>
      </div>

      {/* Gear reason - details panel */}
      {showDetails && (
        <motion.div
          className="mt-4 p-4 rounded-xl bg-white/5 backdrop-blur-md border border-white/10"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="text-xs text-neutral-500 uppercase tracking-wider mb-2">
            Current Status
          </div>
          <div className="text-sm text-neutral-300 leading-relaxed">
            {reason}
          </div>
        </motion.div>
      )}

      {/* Gear pattern background decoration */}
      <div className="absolute -z-10 inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-32 h-32 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full blur-3xl" />
      </div>
    </div>
  );
}

/**
 * Compact Gear Indicator (for small spaces)
 */
export function GearIndicatorCompact({ currentGear, className = '' }: { currentGear: GearType; className?: string }) {
  const config = GEAR_CONFIG[currentGear];

  return (
    <motion.div
      className={`
        inline-flex items-center gap-2 px-4 py-2 rounded-full
        bg-gradient-to-r from-white/10 to-white/5
        backdrop-blur-md border border-white/20
        ${config.glow}
        ${className}
      `}
      whileHover={{ scale: 1.05 }}
      transition={{ duration: 0.2 }}
    >
      <div className={`text-2xl font-black ${config.color}`}>
        {currentGear}
      </div>
      <div className="text-xs text-neutral-400 uppercase tracking-wider">
        {config.label}
      </div>
    </motion.div>
  );
}
