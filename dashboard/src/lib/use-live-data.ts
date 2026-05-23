'use client';

import { useState, useEffect, useCallback } from 'react';

const API_BASE = '/api';

export interface LiveStatus {
  run_id: string;
  stage: string;
  proof: {
    nimble: string;
    clickhouse: string;
    clinical: string;
    datadog: string;
    senso: string;
    x402: string;
  };
  latest_decision: Record<string, any> | null;
  database?: {
    counts: Record<string, any>;
    latest_alerts: Record<string, any>[];
  };
  database_error?: string;
}

export function useLiveStatus(refreshInterval = 5000) {
  const [status, setStatus] = useState<LiveStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/status`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval]);

  return { status, error, loading, refresh };
}

export function usePaymentFlow() {
  const [stage, setStage] = useState<'idle' | 'requesting' | '402' | 'paying' | 'paid' | 'error'>('idle');
  const [alertData, setAlertData] = useState<any>(null);
  const [paymentInfo, setPaymentInfo] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const requestAlert = useCallback(async (alertId: string) => {
    setStage('requesting');
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/alerts/confirmed/${alertId}`, { cache: 'no-store' });
      const data = await res.json();
      if (res.status === 402) {
        setPaymentInfo(data.detail || data);
        setStage('402');
      } else if (res.status === 200) {
        setAlertData(data);
        setStage('paid');
      } else {
        setErrorMsg(data.detail || 'Request failed');
        setStage('error');
      }
    } catch (e) {
      setErrorMsg(String(e));
      setStage('error');
    }
  }, []);

  const submitPayment = useCallback(async (alertId: string) => {
    setStage('paying');
    try {
      const res = await fetch(`${API_BASE}/alerts/confirmed/${alertId}`, {
        headers: { 'x-payment': 'demo-paid' },
        cache: 'no-store',
      });
      const data = await res.json();
      if (res.status === 200) {
        setAlertData(data);
        setStage('paid');
      } else {
        setErrorMsg(data.detail || 'Payment failed');
        setStage('error');
      }
    } catch (e) {
      setErrorMsg(String(e));
      setStage('error');
    }
  }, []);

  const reset = useCallback(() => {
    setStage('idle');
    setAlertData(null);
    setPaymentInfo(null);
    setErrorMsg(null);
  }, []);

  return { stage, alertData, paymentInfo, errorMsg, requestAlert, submitPayment, reset };
}
