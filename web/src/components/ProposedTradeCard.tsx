/**
 * Proposed Trade Card - For Assisted Mode
 * Shows proposed trade with entry, SL, TP, R multiple, strategy confidence
 */

import { GlassCard } from './ui/GlassCard';
import { StatusBadge } from './ui/StatusBadge';
import { CheckCircle, XCircle } from 'lucide-react';

interface ProposedTrade {
  symbol: string;
  direction: 'long' | 'short';
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  size: number;
  projectedR: number;
  strategyConfidence: number;
  reasonTags: string[];
  currentRisk: string;
  environmentQuality: string;
}

interface ProposedTradeCardProps {
  trade: ProposedTrade | null;
  onConfirm: () => void;
  onReject: () => void;
}

export function ProposedTradeCard({ trade, onConfirm, onReject }: ProposedTradeCardProps) {
  if (!trade) return null;

  return (
    <GlassCard className="border-2 border-yellow-400/50">
      <div className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <span>⚡ Proposed Trade</span>
        <StatusBadge status="Assisted Mode" color="yellow" />
      </div>

      {/* Trade Details */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-sm text-white/70 mb-1">Symbol</div>
          <div className="text-xl font-bold text-white">{trade.symbol}</div>
        </div>
        <div>
          <div className="text-sm text-white/70 mb-1">Direction</div>
          <div className={`text-xl font-bold ${trade.direction === 'long' ? 'text-green-400' : 'text-red-400'}`}>
            {trade.direction.toUpperCase()}
          </div>
        </div>
        <div>
          <div className="text-sm text-white/70 mb-1">Entry</div>
          <div className="text-lg font-bold text-white">{trade.entryPrice.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-sm text-white/70 mb-1">Stop Loss</div>
          <div className="text-lg font-bold text-red-400">{trade.stopLoss.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-sm text-white/70 mb-1">Take Profit</div>
          <div className="text-lg font-bold text-green-400">{trade.takeProfit.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-sm text-white/70 mb-1">Size</div>
          <div className="text-lg font-bold text-white">{trade.size}</div>
        </div>
      </div>

      {/* Projected R */}
      <div className="mb-4">
        <div className="text-sm text-white/70 mb-1">Projected R</div>
        <div className={`text-2xl font-bold ${trade.projectedR > 0 ? 'text-green-400' : 'text-red-400'}`}>
          {trade.projectedR > 0 ? '+' : ''}{trade.projectedR.toFixed(2)}R
        </div>
      </div>

      {/* Strategy Confidence */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-white/70">Strategy Confidence</span>
          <span className="text-sm font-semibold text-white">{(trade.strategyConfidence * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-purple-500 transition-all duration-500"
            style={{ width: `${trade.strategyConfidence * 100}%` }}
          />
        </div>
      </div>

      {/* Reason Tags */}
      {trade.reasonTags.length > 0 && (
        <div className="mb-4">
          <div className="text-sm text-white/70 mb-2">Reason Tags</div>
          <div className="flex flex-wrap gap-2">
            {trade.reasonTags.map((tag, i) => (
              <StatusBadge key={i} status={tag} color="blue" />
            ))}
          </div>
        </div>
      )}

      {/* Context */}
      <div className="mb-4 space-y-1 text-sm text-white/70">
        <div>Current Risk: {trade.currentRisk}</div>
        <div>Environment Quality: {trade.environmentQuality}</div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onConfirm}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-green-500/80 hover:bg-green-500 text-white font-semibold transition-all duration-200 hover:scale-105"
        >
          <CheckCircle className="w-5 h-5" />
          Confirm Trade
        </button>
        <button
          onClick={onReject}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-red-500/80 hover:bg-red-500 text-white font-semibold transition-all duration-200 hover:scale-105"
        >
          <XCircle className="w-5 h-5" />
          Reject
        </button>
      </div>
    </GlassCard>
  );
}

