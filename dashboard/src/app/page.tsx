'use client';

import React, { useState } from 'react';
import { useLiveStatus } from '@/lib/use-live-data';
import StatusPanel from '@/components/StatusPanel';
import AlertsPanel from '@/components/AlertsPanel';
import ZipHeatmap from '@/components/ZipHeatmap';
import PaymentGateway from '@/components/PaymentGateway';

type Tab = 'status' | 'alerts' | 'heatmap' | 'payment';

const tabs: { id: Tab; label: string; icon: string }[] = [
  { id: 'status', label: '/status', icon: '📡' },
  { id: 'alerts', label: 'Alerts', icon: '🔔' },
  { id: 'heatmap', label: 'Heatmap', icon: '🗺️' },
  { id: 'payment', label: 'x402 Payment', icon: '💰' },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('status');
  const { status, error, loading, refresh } = useLiveStatus(4000);

  return (
    <div className="min-h-screen bg-[#0a0e1a]">
      <header className="border-b border-gray-800/60 bg-gray-900/40 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <rect x="8" y="4" width="4" height="12" rx="1" fill="white" opacity="0.9"/>
                <rect x="4" y="8" width="12" height="4" rx="1" fill="white" opacity="0.9"/>
                <path d="M2 14 L5 14 L7 10 L9 17 L11 7 L13 14 L15 14 L18 14" stroke="white" strokeWidth="1.2" opacity="0.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div>
              <h1 className="text-base font-semibold text-white">Zipsick</h1>
              <p className="text-[11px] text-gray-500">Public-Health Signal Agent</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {loading ? (
              <span className="text-xs text-gray-500 animate-pulse">Connecting...</span>
            ) : error ? (
              <span className="text-xs text-red-400">⚠ Backend offline</span>
            ) : (
              <>
                <span className="status-dot status-running"></span>
                <span className="text-xs text-green-400 font-medium">Live</span>
                <span className="text-xs text-gray-600">|</span>
                <span className="mono text-xs text-gray-400">{status?.run_id}</span>
              </>
            )}
            <button onClick={refresh} className="text-xs px-2.5 py-1 rounded bg-gray-800 text-gray-400 hover:text-white border border-gray-700 transition-colors">
              ↻
            </button>
          </div>
        </div>
      </header>

      <nav className="border-b border-gray-800/40 bg-gray-900/20">
        <div className="max-w-[1600px] mx-auto px-6 flex gap-1 py-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === t.id ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
            >
              <span>{t.icon}</span>
              <span>{t.label}</span>
            </button>
          ))}
        </div>
      </nav>

      <main className="max-w-[1600px] mx-auto px-6 py-6">
        {error && !loading && (
          <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4">
            <p className="text-sm text-red-300 mb-1">Cannot reach backend at <code className="mono">localhost:8000</code></p>
            <p className="text-xs text-red-400/70 mono">Run: uvicorn app:app --host 0.0.0.0 --port 8000</p>
          </div>
        )}

        {activeTab === 'status' && <StatusPanel status={status} loading={loading} />}
        {activeTab === 'alerts' && <AlertsPanel status={status} />}
        {activeTab === 'heatmap' && <ZipHeatmap alerts={status?.database?.latest_alerts || []} />}
        {activeTab === 'payment' && <PaymentGateway alerts={status?.database?.latest_alerts || []} />}
      </main>

      <footer className="border-t border-gray-800/40 mt-8">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex justify-between">
          <span className="text-xs text-gray-600">Nimble • ClickHouse • Datadog • Senso • x402/CDP</span>
          <span className="text-xs text-gray-600">Zipsick — No patient-level PHI stored</span>
        </div>
      </footer>
    </div>
  );
}
