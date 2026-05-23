'use client';
import React, { useState } from 'react';
import { usePaymentFlow } from '@/lib/use-live-data';

export default function PaymentGateway({ alerts }: { alerts: any[] }) {
  const confirmed = alerts.filter((a: any) => a.clinical_status === 'confirmed');
  const [selectedId, setSelectedId] = useState<string>(confirmed[0]?.alert_id || '');
  const { stage, alertData, paymentInfo, errorMsg, requestAlert, submitPayment, reset } = usePaymentFlow();

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">💰 x402 Payment Gateway <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/10 border border-orange-500/30 text-orange-400 ml-2">LIVE</span></h2>
        {stage !== 'idle' && <button onClick={reset} className="text-xs text-gray-500 hover:text-gray-300">Reset</button>}
      </div>

      {confirmed.length === 0 ? <p className="text-sm text-gray-500 mb-4">No confirmed alerts. Run the pipeline first.</p> : (
        <div className="mb-4">
          <label className="text-xs text-gray-500 block mb-1">Select confirmed alert:</label>
          <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 mono w-full">
            {confirmed.map((a: any) => <option key={a.alert_id} value={a.alert_id}>{a.alert_id} — ZIP {a.zip} / {a.symptom} (z={Number(a.z_score).toFixed(2)})</option>)}
          </select>
        </div>
      )}

      {stage === 'idle' && selectedId && (
        <button onClick={() => requestAlert(selectedId)} className="text-sm px-4 py-2 rounded-lg bg-orange-500/20 text-orange-400 border border-orange-500/30 hover:bg-orange-500/30 transition-all font-medium">
          ▶ GET /alerts/confirmed/{selectedId}
        </button>
      )}

      <div className="mt-4 bg-gray-950 rounded-lg p-4 border border-gray-800 mono text-xs space-y-2">
        {stage === 'idle' && <div className="text-gray-500"># Request a confirmed alert package via x402</div>}
        {stage === 'requesting' && <div className="text-blue-400 animate-pulse">→ GET /alerts/confirmed/{selectedId} ...</div>}
        {(stage === '402' || stage === 'paying' || stage === 'paid') && (<><div className="text-blue-400">→ GET /alerts/confirmed/{selectedId}</div><div className="text-red-400 mt-1">← 402 Payment Required</div>{paymentInfo && <pre className="text-gray-500 pl-4 whitespace-pre-wrap">{JSON.stringify(paymentInfo, null, 2)}</pre>}</>)}
        {(stage === 'paying' || stage === 'paid') && <div className="text-amber-400 mt-1">→ x-payment: demo-paid</div>}
        {stage === 'paid' && <div className="text-green-400 mt-1 font-semibold">← 200 OK ✓</div>}
        {stage === 'error' && <div className="text-red-400">✗ {errorMsg}</div>}
      </div>

      {stage === '402' && <button onClick={() => submitPayment(selectedId)} className="mt-4 text-sm px-4 py-2 rounded-lg bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30 font-medium">💳 Pay $0.25 via x402</button>}

      {stage === 'paid' && alertData && (
        <div className="mt-4 bg-green-500/5 border border-green-500/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3"><span className="text-green-400">✓</span><span className="text-sm font-medium text-green-300">Alert Package Delivered</span></div>
          <pre className="mono text-[11px] text-gray-300 overflow-auto whitespace-pre-wrap max-h-80">{JSON.stringify(alertData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
