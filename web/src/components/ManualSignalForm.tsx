/**
 * Manual Signal Submission Form
 *
 * Glassmorphic design with modern CSS features per UI_Concept.txt blueprint.
 * Features: backdrop blur, duotone gradients, smooth micro-interactions.
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { ManualSignalRequest, ManualSignalResponse } from '@/lib/types';

interface FormData {
  symbol: string;
  side: 'LONG' | 'SHORT';
  entry: string;
  stop: string;
  target: string;
  contracts: string;
  strategy: string;
  confidence: string;
  notes: string;
  asset_class: string;
}

const initialFormData: FormData = {
  symbol: 'MNQ',
  side: 'LONG',
  entry: '',
  stop: '',
  target: '',
  contracts: '1',
  strategy: 'Manual Signal',
  confidence: '0.8',
  notes: '',
  asset_class: 'futures',
};

export function ManualSignalForm() {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [apiKey, setApiKey] = useState<string>(
    localStorage.getItem('transmission_api_key') || ''
  );

  // Calculate risk metrics
  const calculateMetrics = () => {
    const entry = parseFloat(formData.entry);
    const stop = parseFloat(formData.stop);
    const target = parseFloat(formData.target);

    if (isNaN(entry) || isNaN(stop) || isNaN(target)) {
      return null;
    }

    const stopDistance = formData.side === 'LONG'
      ? entry - stop
      : stop - entry;

    const targetDistance = formData.side === 'LONG'
      ? target - entry
      : entry - target;

    const riskReward = stopDistance > 0 ? targetDistance / stopDistance : 0;

    return {
      stopDistance: stopDistance.toFixed(2),
      targetDistance: targetDistance.toFixed(2),
      riskReward: riskReward.toFixed(2),
    };
  };

  const metrics = calculateMetrics();

  // Submit signal mutation
  const submitSignal = useMutation({
    mutationFn: async (data: ManualSignalRequest) => {
      const response = await api.post<ManualSignalResponse>('/webhooks/generic', data);
      return response.data;
    },
    onSuccess: (data) => {
      console.log('Signal submitted successfully:', data);
      // Reset form on success
      setFormData(initialFormData);
    },
    onError: (error: any) => {
      console.error('Signal submission error:', error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Save API key to localStorage
    if (apiKey) {
      localStorage.setItem('transmission_api_key', apiKey);
    }

    // Build request payload
    const payload: ManualSignalRequest = {
      symbol: formData.symbol,
      side: formData.side,
      entry: parseFloat(formData.entry),
      stop: parseFloat(formData.stop),
      target: parseFloat(formData.target),
      contracts: parseInt(formData.contracts) || undefined,
      strategy: formData.strategy || undefined,
      confidence: parseFloat(formData.confidence) || undefined,
      notes: formData.notes || undefined,
      asset_class: formData.asset_class || undefined,
    };

    submitSignal.mutate(payload);
  };

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData({ ...formData, [field]: value });
  };

  return (
    <div className="glass rounded-2xl p-8 hover-lift transition-smooth">
      {/* Header with gradient text */}
      <div className="mb-6">
        <h2 className="text-gradient text-3xl font-bold mb-2">
          Manual Signal Submission
        </h2>
        <p className="text-neutral-400 text-sm">
          Submit trading signals directly to VEGUS for testing and validation
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* API Key Section - Glass panel */}
        <div className="glass rounded-xl p-6 space-y-3 border-2 border-purple-500/20">
          <Label htmlFor="apiKey" className="text-sm font-semibold flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
            API Key
          </Label>
          <Input
            id="apiKey"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk_..."
            required
            className="transition-smooth focus:scale-[1.01]"
          />
          <p className="text-xs text-neutral-400">
            Check server logs for default API key or create one via /api/auth
          </p>
        </div>

        {/* Symbol & Asset Class Row */}
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="symbol" className="font-semibold">Symbol</Label>
            <Input
              id="symbol"
              value={formData.symbol}
              onChange={(e) => handleChange('symbol', e.target.value)}
              placeholder="MNQ"
              required
              className="transition-smooth focus:scale-[1.01]"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="assetClass" className="font-semibold">Asset Class</Label>
            <Select
              id="assetClass"
              value={formData.asset_class}
              onChange={(e) => handleChange('asset_class', e.target.value)}
              className="transition-smooth focus:scale-[1.01]"
            >
              <option value="futures">🔮 Futures</option>
              <option value="equity">📈 Equity</option>
              <option value="crypto">₿ Crypto</option>
              <option value="forex">💱 Forex</option>
            </Select>
          </div>
        </div>

        {/* Direction with duotone gradient buttons */}
        <div className="space-y-3">
          <Label className="font-semibold">Direction</Label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => handleChange('side', 'LONG')}
              className={`py-4 px-6 rounded-xl font-semibold transition-smooth
                ${formData.side === 'LONG'
                  ? 'duotone-bg text-white shadow-strong scale-105'
                  : 'glass hover:scale-105'
                }`}
            >
              ⬆ LONG
            </button>
            <button
              type="button"
              onClick={() => handleChange('side', 'SHORT')}
              className={`py-4 px-6 rounded-xl font-semibold transition-smooth
                ${formData.side === 'SHORT'
                  ? 'bg-gradient-to-br from-red-500 to-pink-600 text-white shadow-strong scale-105'
                  : 'glass hover:scale-105'
                }`}
            >
              ⬇ SHORT
            </button>
          </div>
        </div>

        {/* Price Inputs - Glass morphic */}
        <div className="glass rounded-xl p-6 space-y-4">
          <h3 className="font-semibold text-lg mb-4">Entry & Exit Prices</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="entry" className="text-sm font-semibold">Entry Price</Label>
              <Input
                id="entry"
                type="number"
                step="0.01"
                value={formData.entry}
                onChange={(e) => handleChange('entry', e.target.value)}
                placeholder="20500.00"
                required
                className="text-lg font-mono transition-smooth focus:scale-[1.02]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="stop" className="text-sm font-semibold">Stop Price</Label>
              <Input
                id="stop"
                type="number"
                step="0.01"
                value={formData.stop}
                onChange={(e) => handleChange('stop', e.target.value)}
                placeholder="20450.00"
                required
                className="text-lg font-mono transition-smooth focus:scale-[1.02]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="target" className="text-sm font-semibold">Target Price</Label>
              <Input
                id="target"
                type="number"
                step="0.01"
                value={formData.target}
                onChange={(e) => handleChange('target', e.target.value)}
                placeholder="20600.00"
                required
                className="text-lg font-mono transition-smooth focus:scale-[1.02]"
              />
            </div>
          </div>

          {/* Risk Metrics Display - Animated */}
          {metrics && (
            <div className="mt-6 p-4 rounded-lg glass border border-indigo-500/30">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-xs text-neutral-400 mb-1">Stop Distance</div>
                  <div className="text-2xl font-bold text-gradient">{metrics.stopDistance}</div>
                  <div className="text-xs text-neutral-400">pts</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-neutral-400 mb-1">Target Distance</div>
                  <div className="text-2xl font-bold text-gradient">{metrics.targetDistance}</div>
                  <div className="text-xs text-neutral-400">pts</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-neutral-400 mb-1">Risk:Reward</div>
                  <div className={`text-2xl font-bold ${parseFloat(metrics.riskReward) >= 2 ? 'text-green-400' : 'text-amber-400'}`}>
                    1:{metrics.riskReward}
                  </div>
                  <div className="text-xs text-neutral-400">ratio</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Additional Settings */}
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="contracts" className="font-semibold">Contracts (optional)</Label>
            <Input
              id="contracts"
              type="number"
              min="1"
              value={formData.contracts}
              onChange={(e) => handleChange('contracts', e.target.value)}
              placeholder="1"
              className="transition-smooth"
            />
            <p className="text-xs text-neutral-400">
              Leave blank for VEGUS to calculate based on risk parameters
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confidence" className="font-semibold">Confidence (0-1)</Label>
            <Input
              id="confidence"
              type="number"
              step="0.1"
              min="0"
              max="1"
              value={formData.confidence}
              onChange={(e) => handleChange('confidence', e.target.value)}
              placeholder="0.8"
              className="transition-smooth"
            />
          </div>
        </div>

        {/* Strategy Name */}
        <div className="space-y-2">
          <Label htmlFor="strategy" className="font-semibold">Strategy Name</Label>
          <Input
            id="strategy"
            value={formData.strategy}
            onChange={(e) => handleChange('strategy', e.target.value)}
            placeholder="Manual Signal"
            className="transition-smooth"
          />
        </div>

        {/* Notes */}
        <div className="space-y-2">
          <Label htmlFor="notes" className="font-semibold">Trade Notes</Label>
          <textarea
            id="notes"
            value={formData.notes}
            onChange={(e) => handleChange('notes', e.target.value)}
            className="glass flex min-h-[100px] w-full rounded-xl px-4 py-3 text-sm transition-smooth
              focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:scale-[1.01]
              placeholder:text-neutral-400"
            placeholder="Trade setup notes, market conditions, confluence factors..."
          />
        </div>

        {/* Submit Button - Duotone gradient with animation */}
        <Button
          type="submit"
          disabled={submitSignal.isPending || !apiKey}
          className="w-full py-6 text-lg font-semibold duotone-bg hover:shadow-strong
            transition-smooth hover:scale-[1.02] active:scale-[0.98]
            disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {submitSignal.isPending ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Processing Signal...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Submit Signal to VEGUS
            </span>
          )}
        </Button>

        {/* Status Messages with glassmorphism */}
        {submitSignal.isSuccess && (
          <div className="glass rounded-xl p-4 border-2 border-green-500/50 bg-green-50/50 dark:bg-green-950/20 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-semibold text-green-900 dark:text-green-100">Success!</p>
                <p className="text-sm text-green-800 dark:text-green-200">{submitSignal.data?.message}</p>
                {submitSignal.data?.reason && (
                  <p className="text-xs text-green-700 dark:text-green-300 mt-1">{submitSignal.data.reason}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {submitSignal.isError && (
          <div className="glass rounded-xl p-4 border-2 border-red-500/50 bg-red-50/50 dark:bg-red-950/20 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="flex items-start gap-3">
              <svg className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-semibold text-red-900 dark:text-red-100">Error</p>
                <p className="text-sm text-red-800 dark:text-red-200">{submitSignal.error?.message || 'Failed to submit signal'}</p>
                <p className="text-xs text-red-700 dark:text-red-300 mt-1">
                  {submitSignal.error?.response?.data?.detail || 'Check console for details'}
                </p>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
