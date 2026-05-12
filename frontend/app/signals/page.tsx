"use client";

import { useEffect, useState } from "react";
import { getApiBase } from "../lib/api";

type Signal = {
  ticker: string;
  computed_at: string;
  price: number | null;
  pred_return: number | null;
  rmse: number | null;
  signal_strength: string | null;
  above_ma20: boolean | null;
  criteria_met: boolean;
  suggested_shares: number | null;
  suggested_stop_loss: number | null;
  suggested_take_profit: number | null;
};

function fmt(n: number | null | undefined, decimals = 2) {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toFixed(decimals);
}

function Check({ ok }: { ok: boolean | null }) {
  if (ok === null) return <span style={{ color: "#9ca3af" }}>—</span>;
  return ok
    ? <span style={{ color: "#16a34a", fontWeight: 700 }}>✓</span>
    : <span style={{ color: "#dc2626" }}>✗</span>;
}

function SignalBadge({ s }: { s: string | null }) {
  if (!s) return <span style={{ color: "#9ca3af" }}>—</span>;
  const map: Record<string, { bg: string; color: string }> = {
    Strong: { bg: "#dcfce7", color: "#16a34a" },
    Medium: { bg: "#fef9c3", color: "#ca8a04" },
    Weak: { bg: "#f3f4f6", color: "#6b7280" },
  };
  const style = map[s] ?? { bg: "#f3f4f6", color: "#333" };
  return (
    <span style={{ padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600, background: style.bg, color: style.color }}>
      {s}
    </span>
  );
}

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);
  const [apiBase, setApiBase] = useState("http://localhost:8000/api/v1");

  useEffect(() => {
    const base = getApiBase();
    setApiBase(base);
    fetch(`${base}/signals`)
      .then(r => r.json())
      .then(data => { setSignals(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  async function recompute() {
    setComputing(true);
    try {
      const data = await fetch(`${apiBase}/signals/compute`, { method: "POST" }).then(r => r.json());
      setSignals(data);
    } finally {
      setComputing(false);
    }
  }

  async function openPosition(s: Signal) {
    if (!s.price || !s.suggested_shares || !s.suggested_stop_loss || !s.suggested_take_profit) return;
    await fetch(`${apiBase}/positions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticker: s.ticker,
        shares: s.suggested_shares,
        entry_price: s.price,
        stop_loss: s.suggested_stop_loss,
        take_profit: s.suggested_take_profit,
        pred_return_at_entry: s.pred_return,
        signal_strength_at_entry: s.signal_strength,
      }),
    });
    alert(`Position logged: ${s.suggested_shares} shares of ${s.ticker} @ $${s.price}`);
  }

  if (loading) return <main style={page}><p style={{ color: "#666" }}>Loading signals...</p></main>;

  const actionable = signals.filter(s => s.criteria_met);

  return (
    <main style={page}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>Trade Signals</h1>
        <button onClick={recompute} disabled={computing} style={btn}>
          {computing ? "Computing..." : "↻ Recompute"}
        </button>
      </div>
      <p style={{ color: "#666", marginTop: 4, marginBottom: 20, fontSize: 13 }}>
        {actionable.length > 0
          ? `${actionable.length} ticker${actionable.length > 1 ? "s" : ""} meet all buy criteria today.`
          : "No tickers meet all buy criteria today. Check back after market close."}
      </p>

      {signals.length === 0 ? (
        <p style={{ color: "#666" }}>No signals yet. Add tickers to your watchlist and click Recompute.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {signals.map(s => (
            <div key={s.ticker} style={{
              padding: 16,
              border: `1px solid ${s.criteria_met ? "#86efac" : "#eee"}`,
              borderRadius: 12,
              background: s.criteria_met ? "#f0fdf4" : "#fff",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{ fontWeight: 700, fontSize: 18 }}>{s.ticker}</span>
                  <SignalBadge s={s.signal_strength} />
                  {s.criteria_met && (
                    <span style={{ padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 700, background: "#16a34a", color: "#fff" }}>
                      BUY SIGNAL
                    </span>
                  )}
                  <span style={{ fontSize: 12, color: "#9ca3af" }}>
                    {s.computed_at ? new Date(s.computed_at).toLocaleString() : ""}
                  </span>
                </div>
                {s.criteria_met && (
                  <button onClick={() => openPosition(s)} style={{ ...btn, background: "#000", color: "#fff", borderColor: "#000" }}>
                    Log Position
                  </button>
                )}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 8, marginBottom: 12 }}>
                <Stat label="Price" value={s.price != null ? `$${fmt(s.price)}` : "—"} />
                <Stat label="Pred Return" value={s.pred_return != null ? `${s.pred_return > 0 ? "+" : ""}${fmt(s.pred_return)}%` : "—"} color={s.pred_return != null ? (s.pred_return > 0 ? "#16a34a" : "#dc2626") : undefined} />
                <Stat label="Recent Error" value={s.rmse != null ? `±${fmt(s.rmse)}%` : "—"} />
                {s.criteria_met && <Stat label="Shares" value={fmt(s.suggested_shares, 4)} />}
                {s.criteria_met && <Stat label="Stop Loss" value={s.suggested_stop_loss != null ? `$${fmt(s.suggested_stop_loss)}` : "—"} color="#dc2626" />}
                {s.criteria_met && <Stat label="Take Profit" value={s.suggested_take_profit != null ? `$${fmt(s.suggested_take_profit)}` : "—"} color="#16a34a" />}
              </div>

              <div style={{ display: "flex", gap: 20, fontSize: 12, color: "#555" }}>
                <span>Criteria:</span>
                <span><Check ok={s.pred_return != null ? s.pred_return > 0 : null} /> pred &gt; 0</span>
                <span><Check ok={s.above_ma20} /> above MA20</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ padding: "8px 10px", background: "#f9fafb", borderRadius: 8 }}>
      <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>{label}</div>
      <div style={{ fontWeight: 600, fontSize: 13, color: color ?? "#111" }}>{value}</div>
    </div>
  );
}

const page: React.CSSProperties = { padding: 24, maxWidth: 1000, margin: "0 auto" };
const btn: React.CSSProperties = { padding: "8px 14px", border: "1px solid #ddd", borderRadius: 8, cursor: "pointer", fontSize: 13, background: "#fff" };
