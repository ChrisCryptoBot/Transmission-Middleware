/**
 * Account Selector Component
 * Based on UI_Concept.txt section 8.1 - Top Navbar
 */

import { useState } from 'react';
import { GlassCard } from './ui/GlassCard';
import { ChevronDown, DollarSign } from 'lucide-react';
import { AccountConfig } from '@/lib/types';
import { formatCurrency } from '@/lib/utils';

interface AccountSelectorProps {
  accounts: AccountConfig[];
  selectedAccountId: string;
  onAccountChange: (accountId: string) => void;
}

export function AccountSelector({ accounts, selectedAccountId, onAccountChange }: AccountSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const selectedAccount = accounts.find((acc) => acc.accountId === selectedAccountId);

  if (!selectedAccount) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 transition-all duration-200"
      >
        <DollarSign className="w-4 h-4 text-white/70" />
        <div className="text-left">
          <div className="text-xs text-white/60">Account</div>
          <div className="text-sm font-semibold text-white">
            {selectedAccount.accountId} • {formatCurrency(selectedAccount.equity)}
          </div>
        </div>
        <ChevronDown className={`w-4 h-4 text-white/70 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <GlassCard className="absolute top-full mt-2 right-0 z-50 min-w-[280px]">
            <div className="space-y-1">
              {accounts.map((account) => (
                <button
                  key={account.accountId}
                  onClick={() => {
                    onAccountChange(account.accountId);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-all ${
                    account.accountId === selectedAccountId
                      ? 'bg-purple-500/20 border border-purple-400/30'
                      : 'hover:bg-white/10'
                  }`}
                >
                  <div className="font-semibold text-white">{account.accountId}</div>
                  <div className="text-sm text-white/70">{formatCurrency(account.equity)}</div>
                </button>
              ))}
            </div>
          </GlassCard>
        </>
      )}
    </div>
  );
}

