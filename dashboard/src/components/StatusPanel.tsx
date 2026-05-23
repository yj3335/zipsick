'use client';
import React from 'react';
import type { LiveStatus } from '@/lib/use-live-data';

const proofLabels: Record<string, string> = { nimble: 'Nimble', clickhouse: 'ClickHouse', clinical: 'Clinical', datadog: 'Datadog', senso: 'Senso', x402: 'x402' };
const proofColors: Record<string, string> = { nimble: 'text-emerald-400', clickhouse: 'text-yellow-400', clinical: 'text-blue-400', datadog: 'text-violet-400', senso: 'text-purple-400', x402: 'text-orange-400' };

export default function StatusPanel({ status, loading }: { status: LiveStatus | null; loading: boolean }) {
  if (loading) return <div className="glass-card p-8 text-center"><p className="text-gray-400 animate-pulse">Loading...</p></div>;
  if (!status) return <div className="glass-card p-8 text-center"><p className="text-gray-500">No data. Start the backend.</p></div>;

  const counts = status.database?.counts;
  const alerts = status.database?.latest_alerts || [];

  return (
    <div className="space-y-6">
      <div className="glass-card p-5 glow-green">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">📡 Agent Status</h2>
          <div className="flex items-center gap-2"><span className="status-dot status-running"></span><span className="text-sm text-green-400 font-medium">{status.stage || 'running'}</span></div>
        </div>
        <div className="flex items-center gap-6 mb-4 pb-3 border-b border-gray-700/50">
          <div><span className="text-xs text-gray-500 block">Run ID</span><span className="mono text-sm text-green-300">{status.run_id}</span></div>
          <div><span className="text-xs text-gray-500 block">Stage</span><span className="mono text-sm text-gray-200">{status.stage}</span></div>
          {status.database_error && <div><span className="text-xs text-red-400">DB: {status.database_error}</span></div>}
        </div>
        <div><span className="text-xs text-gray-500 block mb-2">Sponsor Proof</span>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(status.proof).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between bg-gray-800/50 rounded-lg px-3 py-2">
                <span className={`text-xs font-medium ${proofColors[k] || 'text-gray-400'}`}>{proofLabels[k]}</span>
                <span className={`text-xs mono ${v !== 'pending' ? 'text-green-400' : 'text-gray-500'}`}>{v !== 'pending' ? '✓' : '○'} {v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {counts && (
        <div className="grid grid-cols-4 gap-4">
          {[
            { l: 'Total Signals', v: counts.total_signals, c: 'border-emerald-500/20 text-emerald-300' },
            { l: 'Real Signals', v: counts.real_signals, c: 'border-green-500/20 text-green-300' },
            { l: 'Nimble Real', v: counts.nimble_real_signals, c: 'border-emerald-500/20 text-emerald-300' },
            { l: 'Synthetic', v: counts.synthetic_signals, c: 'border-amber-500/20 text-amber-300' },
          ].map((s) => (
            <div key={s.l} className={`rounded-xl border p-4 bg-gray-900/40 ${s.c}`}>
              <span className="text-xs text-gray-400 block mb-1">{s.l}</span>
              <span className="text-2xl font-bold">{s.v ?? '—'}</span>
            </div>
          ))}
        </div>
      )}

      {alerts.length > 0 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Latest Alerts (ClickHouse)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-gray-700/50">
                <th className="text-left py-2 px-2 text-gray-400">alert_id</th>
                <th className="text-left py-2 px-2 text-gray-400">ZIP</th>
                <th className="text-left py-2 px-2 text-gray-400">Symptom</th>
                <th className="text-right py-2 px-2 text-gray-400">Count</th>
                <th className="text-right py-2 px-2 text-gray-400">Z-Score</th>
                <th className="text-left py-2 px-2 text-gray-400">Clinical</th>
                <th className="text-left py-2 px-2 text-gray-400">Payment</th>
              </tr></thead>
              <tbody>
                {alerts.map((a: any, i: number) => (
                  <tr key={i} className="border-b border-gray-800/50">
                    <td className="py-2 px-2 mono text-gray-300">{a.alert_id}</td>
                    <td className="py-2 px-2 mono text-gray-200">{a.zip}</td>
                    <td className="py-2 px-2"><span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400">{a.symptom}</span></td>
                    <td className="py-2 px-2 text-right mono text-gray-200">{a.recent_count}</td>
                    <td className="py-2 px-2 text-right"><span className={`mono font-semibold ${Number(a.z_score) >= 2.5 ? 'text-red-400' : 'text-gray-400'}`}>{Number(a.z_score).toFixed(2)}</span></td>
                    <td className="py-2 px-2"><span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${a.clinical_status === 'confirmed' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>{a.clinical_status}</span></td>
                    <td className="py-2 px-2"><span className={`text-xs ${a.payment_status === 'paid' ? 'text-orange-400' : 'text-gray-500'}`}>{a.payment_status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <details className="glass-card p-4">
        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-300">Raw /status JSON</summary>
        <pre className="mono text-[11px] text-gray-400 mt-3 overflow-auto max-h-64">{JSON.stringify(status, null, 2)}</pre>
      </details>
    </div>
  );
}
