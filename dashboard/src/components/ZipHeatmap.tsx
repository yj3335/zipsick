'use client';
import React, { useState } from 'react';

const zipCoords: Record<string, { name: string; lat: number; lng: number }> = {
  '10001': { name: 'Midtown South', lat: 40.7484, lng: -73.9967 },
  '10002': { name: 'Lower East Side', lat: 40.7157, lng: -73.9863 },
  '10003': { name: 'East Village', lat: 40.7317, lng: -73.9893 },
  '10004': { name: 'Financial District', lat: 40.6988, lng: -74.0384 },
  '10007': { name: 'City Hall', lat: 40.7135, lng: -74.0079 },
  '10009': { name: 'Alphabet City', lat: 40.7265, lng: -73.9793 },
  '10010': { name: 'Gramercy', lat: 40.7390, lng: -73.9826 },
  '10011': { name: 'Chelsea', lat: 40.7418, lng: -74.0002 },
  '10012': { name: 'SoHo', lat: 40.7258, lng: -73.9981 },
  '10013': { name: 'Tribeca', lat: 40.7195, lng: -74.0089 },
  '10014': { name: 'West Village', lat: 40.7338, lng: -74.0054 },
  '10036': { name: 'Times Square', lat: 40.7590, lng: -73.9845 },
};

export default function ZipHeatmap({ alerts }: { alerts: any[] }) {
  const [selectedZip, setSelectedZip] = useState<string | null>(null);
  const minLat = 40.695, maxLat = 40.765, minLng = -74.045, maxLng = -73.970;
  const toX = (lng: number) => ((lng - minLng) / (maxLng - minLng)) * 520 + 40;
  const toY = (lat: number) => (1 - (lat - minLat) / (maxLat - minLat)) * 380 + 10;

  const zones = alerts.map((a: any) => {
    const coord = zipCoords[a.zip] || { name: a.zip, lat: 40.73, lng: -74.00 };
    const zScore = Number(a.z_score) || 0;
    const status = a.clinical_status === 'confirmed' ? 'critical' : zScore >= 2.5 ? 'elevated' : zScore >= 1.5 ? 'watch' : 'normal';
    return { ...a, ...coord, zScore, status };
  });

  const alertedZips = new Set(zones.map((z: any) => z.zip));
  const bgZones = Object.entries(zipCoords).filter(([zip]) => !alertedZips.has(zip)).map(([zip, c]) => ({ zip, ...c, zScore: 0, status: 'normal', recent_count: 0, symptom: '-' }));
  const allZones = [...zones, ...bgZones];

  const getR = (z: any) => z.status === 'critical' ? 28 : z.status === 'elevated' ? 22 : z.status === 'watch' ? 16 : 10;
  const getC = (z: any) => z.status === 'critical' ? '#ef4444' : z.status === 'elevated' ? '#f97316' : z.status === 'watch' ? '#eab308' : '#22c55e';
  const getO = (z: any) => z.status === 'critical' ? 0.75 : z.status === 'elevated' ? 0.6 : z.status === 'watch' ? 0.4 : 0.2;
  const sel = allZones.find((z: any) => z.zip === selectedZip);
  const manhattanPath = `M ${toX(-74.018)} ${toY(40.699)} L ${toX(-74.042)} ${toY(40.700)} L ${toX(-74.012)} ${toY(40.705)} L ${toX(-74.011)} ${toY(40.720)} L ${toX(-74.010)} ${toY(40.730)} L ${toX(-74.009)} ${toY(40.740)} L ${toX(-74.008)} ${toY(40.750)} L ${toX(-74.005)} ${toY(40.760)} L ${toX(-73.997)} ${toY(40.762)} L ${toX(-73.988)} ${toY(40.760)} L ${toX(-73.981)} ${toY(40.755)} L ${toX(-73.977)} ${toY(40.745)} L ${toX(-73.974)} ${toY(40.738)} L ${toX(-73.973)} ${toY(40.730)} L ${toX(-73.974)} ${toY(40.720)} L ${toX(-73.976)} ${toY(40.710)} L ${toX(-73.980)} ${toY(40.702)} L ${toX(-73.990)} ${toY(40.699)} L ${toX(-74.000)} ${toY(40.698)} Z`;

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">🗺️ ZIP Heatmap — Lower Manhattan</h2>
        <div className="flex items-center gap-4 text-[10px] text-gray-400">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500 opacity-75 inline-block"></span> Critical</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-orange-500 opacity-60 inline-block"></span> Elevated</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-yellow-500 opacity-40 inline-block"></span> Watch</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500 opacity-25 inline-block"></span> Normal</span>
        </div>
      </div>
      {alerts.length === 0 ? <p className="text-sm text-gray-500 py-8 text-center">No alert data yet.</p> : (
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 bg-gray-950/50 rounded-xl border border-gray-700/50">
            <svg viewBox="0 0 600 400" className="w-full" style={{ minHeight: '340px' }}>
              <rect x="0" y="0" width="40" height="400" fill="#1e3a5f" opacity="0.3" />
              <rect x="540" y="0" width="60" height="400" fill="#1e3a5f" opacity="0.2" />
              <path d={manhattanPath} fill="#1f2937" stroke="#4b5563" strokeWidth="1.5" />
              {allZones.map((z: any) => {
                const cx = toX(z.lng), cy = toY(z.lat), r = getR(z), color = getC(z), op = getO(z);
                return (
                  <g key={z.zip}>
                    {(z.status === 'critical' || z.status === 'elevated') && (
                      <circle cx={cx} cy={cy} r={r + 6} fill={color} opacity={0.12}>
                        <animate attributeName="r" values={`${r+4};${r+14};${r+4}`} dur="2.5s" repeatCount="indefinite" />
                      </circle>
                    )}
                    <circle cx={cx} cy={cy} r={r} fill={color} opacity={op} stroke={selectedZip === z.zip ? '#fff' : 'none'} strokeWidth={2} className="cursor-pointer" onClick={() => setSelectedZip(z.zip)} />
                    <text x={cx} y={cy+1} textAnchor="middle" dominantBaseline="middle" fontSize={z.status === 'critical' ? 10 : 8} fontWeight={z.status === 'critical' ? 700 : 500} fontFamily="monospace" fill="#fff" opacity={z.status === 'normal' ? 0.5 : 0.9} className="pointer-events-none">{z.zip}</text>
                  </g>
                );
              })}
            </svg>
          </div>
          <div className="space-y-3">
            {sel ? (
              <div className={`rounded-lg p-4 border ${sel.status === 'critical' ? 'bg-red-500/10 border-red-500/30' : sel.status === 'elevated' ? 'bg-orange-500/10 border-orange-500/30' : 'bg-gray-800/40 border-gray-700/30'}`}>
                <div className="flex items-center justify-between mb-2"><span className="mono text-lg font-bold text-white">{sel.zip}</span><span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${sel.status === 'critical' ? 'bg-red-500/20 text-red-400' : 'bg-gray-700 text-gray-400'}`}>{sel.status?.toUpperCase()}</span></div>
                <p className="text-sm text-gray-300 mb-3">{sel.name}</p>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between"><span className="text-gray-500">Symptom</span><span className="text-gray-200">{sel.symptom}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Signals</span><span className="text-gray-200">{sel.recent_count || 0}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Z-Score</span><span className={`font-bold ${sel.zScore >= 2.5 ? 'text-red-400' : 'text-gray-300'}`}>{sel.zScore?.toFixed(2)}</span></div>
                </div>
              </div>
            ) : <div className="rounded-lg p-4 border border-gray-700/30 bg-gray-800/30"><p className="text-xs text-gray-500">Click a zone</p></div>}
            <div><span className="text-xs text-gray-500 block mb-2">Active Zones</span>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {zones.sort((a: any, b: any) => b.zScore - a.zScore).map((z: any) => (
                  <div key={z.zip} onClick={() => setSelectedZip(z.zip)} className={`flex items-center justify-between py-1.5 px-2.5 rounded cursor-pointer text-xs ${selectedZip === z.zip ? 'bg-gray-800' : 'hover:bg-gray-800/50'}`}>
                    <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: getC(z) }}></div><span className="mono text-gray-300">{z.zip}</span><span className="text-gray-500">{z.name}</span></div>
                    <span className={`mono font-medium ${z.zScore >= 2.5 ? 'text-red-400' : 'text-gray-500'}`}>{z.zScore.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
