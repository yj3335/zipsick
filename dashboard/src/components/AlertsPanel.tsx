'use client';
import React, { useState } from 'react';
import type { LiveStatus } from '@/lib/use-live-data';

export default function AlertsPanel({ status }: { status: LiveStatus | null }) {
  const [selectedAlert, setSelectedAlert] = useState<any>(null);
  const [publishedContent, setPublishedContent] = useState<any>(null);
  const alerts = status?.database?.latest_alerts || [];
  const latestDecision = status?.latest_decision;

  const fetchPublished = async (alertId: string) => {
    try { const res = await fetch(`/api/alerts/published/${alertId}`); setPublishedContent(res.ok ? await res.json() : null); } catch { setPublishedContent(null); }
  };

  return (
    <div className="space-y-6">
      {latestDecision && (
        <div className={`glass-card p-5 ${latestDecision.clinical_status === 'confirmed' ? 'glow-red' : ''}`}>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-white">🚨 Latest Decision</h2>
            <span className={`text-xs font-semibold px-3 py-1 rounded-full ${latestDecision.clinical_status === 'confirmed' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-gray-700 text-gray-400'}`}>{latestDecision.clinical_status?.toUpperCase()}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div><span className="text-xs text-gray-500 block">ZIP</span><span className="mono text-lg text-white font-bold">{latestDecision.zip}</span></div>
            <div><span className="text-xs text-gray-500 block">Symptom</span><span className="text-sm text-amber-400">{latestDecision.symptom}</span></div>
            <div><span className="text-xs text-gray-500 block">Z-Score</span><span className={`mono text-lg font-bold ${Number(latestDecision.z_score) >= 2.5 ? 'text-red-400' : 'text-gray-300'}`}>{Number(latestDecision.z_score).toFixed(2)}</span></div>
            <div><span className="text-xs text-gray-500 block">Clinical Aggregate</span><span className="mono text-lg text-blue-400 font-bold">{latestDecision.clinical_aggregate_count}</span></div>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-700/50 grid grid-cols-3 gap-4 text-xs">
            <div><span className="text-gray-500">Sources:</span> <span className="text-gray-200">{latestDecision.source_count}</span></div>
            <div><span className="text-gray-500">Diversity:</span> <span className="text-gray-200">{latestDecision.source_diversity}</span></div>
            <div><span className="text-gray-500">Payment:</span> <span className={latestDecision.payment_status === 'paid' ? 'text-orange-400' : 'text-gray-400'}>{latestDecision.payment_status}</span></div>
          </div>
          {latestDecision.senso_url && <div className="mt-2 text-xs text-purple-400">📄 Published: {latestDecision.senso_url}</div>}
        </div>
      )}

      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-white mb-3">All Alerts (ClickHouse)</h3>
        {alerts.length === 0 ? <p className="text-sm text-gray-500">No alerts yet. Run the anomaly engine.</p> : (
          <div className="space-y-2">
            {alerts.map((alert: any, i: number) => (
              <div key={i} onClick={() => { setSelectedAlert(alert); fetchPublished(alert.alert_id); }}
                className={`flex items-center justify-between py-3 px-4 rounded-lg cursor-pointer transition-all ${selectedAlert?.alert_id === alert.alert_id ? 'bg-gray-800 border border-gray-600' : 'bg-gray-800/40 hover:bg-gray-800/70 border border-transparent'}`}>
                <div className="flex items-center gap-4">
                  <span className={`w-2 h-2 rounded-full ${alert.clinical_status === 'confirmed' ? 'bg-red-500' : 'bg-gray-500'}`}></span>
                  <span className="mono text-xs text-gray-300">{alert.alert_id}</span>
                  <span className="text-xs text-gray-400">{alert.zip}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400">{alert.symptom}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`mono text-xs font-semibold ${Number(alert.z_score) >= 2.5 ? 'text-red-400' : 'text-gray-400'}`}>z={Number(alert.z_score).toFixed(2)}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${alert.clinical_status === 'confirmed' ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'}`}>{alert.clinical_status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedAlert && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Detail: {selectedAlert.alert_id}</h3>
          <pre className="mono text-[11px] text-gray-300 overflow-x-auto bg-gray-950 rounded-lg p-4 border border-gray-800">{JSON.stringify(selectedAlert, null, 2)}</pre>
          {publishedContent && (
            <div className="mt-4 pt-4 border-t border-gray-700/50">
              <h4 className="text-xs font-semibold text-purple-400 mb-2">📄 Published (Senso/cited.md)</h4>
              <div className="bg-purple-500/5 border border-purple-500/20 rounded-lg p-4">
                <p className="text-sm font-medium text-white mb-1">{publishedContent.title}</p>
                <p className="text-xs text-gray-300 mb-2">{publishedContent.summary}</p>
                {publishedContent.citations?.map((c: string, i: number) => <div key={i} className="text-xs text-blue-400">→ {c}</div>)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
