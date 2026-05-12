"use client";

import { useEffect, useState } from "react";
import { getApiBase } from "../lib/api";

type DashboardRow = {
  ticker: string;
  status: string;
  price?: number;
  ret_1d?: number;
  ret_5d?: number;
  ret_20d?: number;
  volatility?: number;
  dist_ma20?: number;
  dist_ma50?: number;
  pred_return?: number;
  pred_close?: number;
  rmse_return?: number;
  signal_strength?: string;
  trained_at?: string;
};

function fmt(n: number | undefined | null, decimals = 2) {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toFixed(decimals);
}

function pctCell(n: number | undefined | null) {
  if (n == null || !Number.isFinite(n)) return <td style={td}>—</td>;
  const color = n > 0 ? "#16a34a" : n < 0 ? "#dc2626" : "#333";
  return <td style={{ ...td, color, fontWeight: 500 }}>{n > 0 ? "+" : ""}{n.toFixed(2)}%</td>;
}

function signalBadge(s: string | undefined) {
  if (!s) return "—";
  const colors: Record<string, { bg: string; color: string }> = {
    Strong: { bg: "#dcfce7", color: "#16a34a" },
    Medium: { bg: "#fef9c3", color: "#ca8a04" },
    Weak: { bg: "#f3f4f6", color: "#6b7280" },
  };
  const style = colors[s] ?? { bg: "#f3f4f6", color: "#333" };
  return (
    <span style={{ padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600, background: style.bg, color: style.color }}>
      {s}
    </span>
  );
}

export default function DashboardPage() {
  const [rows, setRows] = useState<DashboardRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const base = getApiBase();
    fetch(`${base}/dashboard`)
      .then(r => r.json())
      .then(data => { setRows(data); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <main style={page}><p style={{ color: "#666" }}>Loading dashboard...</p></main>;
  if (error) return <main style={page}><p style={{ color: "#dc2626" }}>{error}</p></main>;
  if (rows.length === 0) return (
    <main style={page}>
      <p style={{ color: "#666" }}>No tickers in watchlist. Add some from the Chart page.</p>
    </main>
  );

  return (
    <main style={page}>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Dashboard</h1>
      <p style={{ color: "#666", marginTop: 0, marginBottom: 16, fontSize: 13 }}>
        Ranked by volatility + signal strength. Refresh to update.
      </p>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #eee", textAlign: "left" }}>
              {["Ticker", "Price", "1D", "5D", "20D", "Volatility", "vs MA20", "vs MA50", "Pred Return", "Pred Close", "Recent Error", "Signal"].map(h => (
                <th key={h} style={{ ...td, fontWeight: 600, color: "#555", paddingBottom: 8 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.ticker} style={{ borderBottom: "1px solid #f3f4f6", background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                <td style={{ ...td, fontWeight: 700 }}>{r.ticker}</td>
                {r.status === "no_data" ? (
                  <td colSpan={11} style={{ ...td, color: "#9ca3af", fontStyle: "italic" }}>no data — ingest first</td>
                ) : (
                  <>
                    <td style={td}>${fmt(r.price)}</td>
                    {pctCell(r.ret_1d)}
                    {pctCell(r.ret_5d)}
                    {pctCell(r.ret_20d)}
                    <td style={td}>{fmt(r.volatility)}%</td>
                    {pctCell(r.dist_ma20)}
                    {pctCell(r.dist_ma50)}
                    {pctCell(r.pred_return)}
                    <td style={td}>{r.pred_close ? `$${fmt(r.pred_close)}` : "—"}</td>
                    <td style={td}>{r.rmse_return ? `±${(r.rmse_return * 100).toFixed(2)}%` : "—"}</td>
                    <td style={td}>{signalBadge(r.signal_strength)}</td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

const page: React.CSSProperties = { padding: 24, maxWidth: 1200, margin: "0 auto" };
const td: React.CSSProperties = { padding: "10px 12px", whiteSpace: "nowrap" };
