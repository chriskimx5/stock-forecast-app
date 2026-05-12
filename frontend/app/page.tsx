"use client";

import { useEffect, useMemo, useState } from "react";
import { getApiBase } from "./lib/api";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

type PriceRow = { ts: string; open: number; high: number; low: number; close: number; volume: number };
type TrainResp = { ticker: string; n_rows: number; n_train: number; window: number; rmse_return: number; trained_at: string };
type PredictResp = {
  ticker: string; asof_ts: string; last_close: number; pred_log_return: number;
  pred_close: number; pred_close_1sigma_low: number; pred_close_1sigma_high: number;
  model_window: number; trained_at?: string; rmse_return?: number; cached: boolean;
};
type WatchlistItem = { id: number; ticker: string; added_at: string };

function fmt(n: number) { return Number.isFinite(n) ? n.toFixed(2) : String(n); }

export default function Page() {
  const [ticker, setTicker] = useState("AAPL");
  const [prices, setPrices] = useState<PriceRow[]>([]);
  const [train, setTrain] = useState<TrainResp | null>(null);
  const [pred, setPred] = useState<PredictResp | null>(null);
  const [status, setStatus] = useState("");
  const [apiBase, setApiBase] = useState("http://localhost:8000/api/v1");
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);

  useEffect(() => { setApiBase(getApiBase()); }, []);

  useEffect(() => {
    if (!apiBase) return;
    fetch(`${apiBase}/watchlist`).then(r => r.json()).then(setWatchlist).catch(() => {});
  }, [apiBase]);

  const chartData = useMemo(() => prices.map(p => ({ ts: p.ts.slice(0, 10), close: p.close })), [prices]);

  async function callJson(url: string, init?: RequestInit) {
    setStatus("Working...");
    try {
      const r = await fetch(url, init);
      const txt = await r.text();
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${txt}`);
      const data = txt ? JSON.parse(txt) : null;
      setStatus("OK");
      return data;
    } catch (e: any) {
      setStatus(e?.message ?? "Error");
      throw e;
    }
  }

  async function loadPrices() {
    const t = ticker.trim().toUpperCase();
    const data = await callJson(`${apiBase}/prices/${t}?limit=400`);
    setPrices(data);
    setPred(null);
  }

  async function ingest() {
    const t = ticker.trim().toUpperCase();
    await callJson(`${apiBase}/ingest/${t}?period=1y&interval=1d`, { method: "POST" });
    await loadPrices();
  }

  async function trainModel() {
    const t = ticker.trim().toUpperCase();
    const data = await callJson(`${apiBase}/train/${t}?window=20`, { method: "POST" });
    setTrain(data);
  }

  async function predict() {
    const t = ticker.trim().toUpperCase();
    const data = await callJson(`${apiBase}/predict/${t}?ttl=60`);
    setPred(data);
  }

  async function addToWatchlist() {
    const t = ticker.trim().toUpperCase();
    try {
      await callJson(`${apiBase}/watchlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: t }),
      });
      const updated = await fetch(`${apiBase}/watchlist`).then(r => r.json());
      setWatchlist(updated);
    } catch {}
  }

  async function removeFromWatchlist(t: string) {
    await callJson(`${apiBase}/watchlist/${t}`, { method: "DELETE" });
    setWatchlist(w => w.filter(x => x.ticker !== t));
  }

  return (
    <main style={{ padding: 24, maxWidth: 980, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, marginBottom: 8 }}>Stock Forecasting</h1>

      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginTop: 16 }}>
        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          Ticker
          <input
            value={ticker}
            onChange={e => setTicker(e.target.value)}
            style={{ padding: "8px 10px", border: "1px solid #ccc", borderRadius: 8, width: 120 }}
          />
        </label>
        <button onClick={loadPrices} style={btn}>Load prices</button>
        <button onClick={ingest} style={btn}>Ingest (1y)</button>
        <button onClick={trainModel} style={btn}>Train</button>
        <button onClick={predict} style={btn}>Predict</button>
        <button onClick={addToWatchlist} style={{ ...btn, borderColor: "#aaa" }}>+ Watchlist</button>
        <span style={{ marginLeft: "auto", color: status.startsWith("OK") ? "green" : "#555" }}>{status}</span>
      </div>

      {watchlist.length > 0 && (
        <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {watchlist.map(w => (
            <span key={w.ticker} style={{ display: "flex", alignItems: "center", gap: 4, padding: "4px 10px", background: "#f5f5f5", borderRadius: 20, fontSize: 13 }}>
              <button onClick={() => setTicker(w.ticker)} style={{ background: "none", border: "none", cursor: "pointer", fontWeight: 600, padding: 0 }}>{w.ticker}</button>
              <button onClick={() => removeFromWatchlist(w.ticker)} style={{ background: "none", border: "none", cursor: "pointer", color: "#999", padding: 0, fontSize: 12 }}>✕</button>
            </span>
          ))}
        </div>
      )}

      <section style={{ marginTop: 18, padding: 16, border: "1px solid #eee", borderRadius: 12 }}>
        <h2 style={h2}>Chart</h2>
        {chartData.length === 0 ? (
          <p style={{ color: "#666" }}>No data loaded yet. Click "Load prices" or "Ingest".</p>
        ) : (
          <div style={{ width: "100%", height: 360 }}>
            <ResponsiveContainer>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="ts" minTickGap={24} />
                <YAxis domain={["auto", "auto"]} />
                <Tooltip />
                <Line type="monotone" dataKey="close" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section style={{ marginTop: 18, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div style={card}>
          <h2 style={h2}>Training</h2>
          {train ? (
            <div style={mono}>
              <div>ticker: {train.ticker}</div>
              <div>window: {train.window}</div>
              <div>rows: {train.n_rows}</div>
              <div>rmse_return: {train.rmse_return}</div>
              <div>trained_at: {train.trained_at}</div>
            </div>
          ) : <p style={{ color: "#666" }}>Click "Train" to fit a baseline model.</p>}
        </div>

        <div style={card}>
          <h2 style={h2}>Prediction</h2>
          {pred ? (
            <div style={mono}>
              <div>ticker: {pred.ticker}</div>
              <div>asof: {pred.asof_ts}</div>
              <div>last_close: {fmt(pred.last_close)}</div>
              <div>pred_close: {fmt(pred.pred_close)}</div>
              <div>1σ band: [{fmt(pred.pred_close_1sigma_low)}, {fmt(pred.pred_close_1sigma_high)}]</div>
              <div>cached: {String(pred.cached)}</div>
            </div>
          ) : <p style={{ color: "#666" }}>Click "Predict" after training.</p>}
        </div>
      </section>
    </main>
  );
}

const btn: React.CSSProperties = { padding: "8px 12px", border: "1px solid #ddd", borderRadius: 10, background: "white", cursor: "pointer" };
const card: React.CSSProperties = { padding: 16, border: "1px solid #eee", borderRadius: 12 };
const h2: React.CSSProperties = { marginTop: 0, fontSize: 18 };
const mono: React.CSSProperties = { fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace", fontSize: 12.5, lineHeight: 1.5 };
