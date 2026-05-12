"use client";

import { useEffect, useState } from "react";
import { getApiBase } from "../lib/api";

type Position = {
  id: number;
  ticker: string;
  opened_at: string;
  closed_at: string | null;
  shares: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  close_price: number | null;
  close_reason: string | null;
  pred_return_at_entry: number | null;
  signal_strength_at_entry: string | null;
  is_open: boolean;
  unrealized_pnl: number | null;
  unrealized_pnl_pct: number | null;
  realized_pnl: number | null;
};

type Summary = {
  capital: number;
  capital_deployed: number;
  capital_available: number;
  realized_pnl: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  open_positions: number;
};

function fmt(n: number | null | undefined, decimals = 2) {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toFixed(decimals);
}

function PnlSpan({ n }: { n: number | null }) {
  if (n == null) return <span style={{ color: "#9ca3af" }}>—</span>;
  const color = n > 0 ? "#16a34a" : n < 0 ? "#dc2626" : "#555";
  return <span style={{ color, fontWeight: 600 }}>{n > 0 ? "+" : ""}{n.toFixed(2)}</span>;
}

export default function PositionsPage() {
  const [open, setOpen] = useState<Position[]>([]);
  const [history, setHistory] = useState<Position[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [closing, setClosing] = useState<number | null>(null);
  const [closePrices, setClosePrices] = useState<Record<number, string>>({});
  const [apiBase, setApiBase] = useState("http://localhost:8000/api/v1");

  useEffect(() => {
    const base = getApiBase();
    setApiBase(base);
    Promise.all([
      fetch(`${base}/positions`).then(r => r.json()),
      fetch(`${base}/positions/history`).then(r => r.json()),
      fetch(`${base}/positions/summary`).then(r => r.json()),
    ]).then(([o, h, s]) => {
      setOpen(o); setHistory(h); setSummary(s); setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  async function closePosition(id: number) {
    const price = parseFloat(closePrices[id] ?? "0");
    if (!price) { alert("Enter a close price first."); return; }
    setClosing(id);
    try {
      await fetch(`${apiBase}/positions/${id}/close`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ close_price: price, close_reason: "manual" }),
      });
      const [o, h, s] = await Promise.all([
        fetch(`${apiBase}/positions`).then(r => r.json()),
        fetch(`${apiBase}/positions/history`).then(r => r.json()),
        fetch(`${apiBase}/positions/summary`).then(r => r.json()),
      ]);
      setOpen(o); setHistory(h); setSummary(s);
    } finally {
      setClosing(null);
    }
  }

  if (loading) return <main style={page}><p style={{ color: "#666" }}>Loading positions...</p></main>;

  return (
    <main style={page}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Positions</h1>

      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10, marginBottom: 24 }}>
          <SummaryCard label="Capital" value={`$${summary.capital.toLocaleString()}`} />
          <SummaryCard label="Deployed" value={`$${summary.capital_deployed.toLocaleString()}`} />
          <SummaryCard label="Available" value={`$${summary.capital_available.toLocaleString()}`} />
          <SummaryCard label="Realized P&L" value={`$${summary.realized_pnl >= 0 ? "+" : ""}${summary.realized_pnl.toFixed(2)}`} color={summary.realized_pnl >= 0 ? "#16a34a" : "#dc2626"} />
          <SummaryCard label="Win Rate" value={`${summary.win_rate_pct.toFixed(1)}%`} />
          <SummaryCard label="Trades" value={`${summary.wins}W / ${summary.losses}L`} />
        </div>
      )}

      <h2 style={h2}>Open Positions ({open.length})</h2>
      {open.length === 0 ? (
        <p style={{ color: "#666", fontSize: 13, marginBottom: 24 }}>No open positions. Go to Signals to find buy candidates.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 24 }}>
          {open.map(p => (
            <div key={p.id} style={{ padding: 16, border: "1px solid #eee", borderRadius: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{ fontWeight: 700, fontSize: 16 }}>{p.ticker}</span>
                  {p.signal_strength_at_entry && (
                    <span style={{ fontSize: 11, padding: "2px 7px", borderRadius: 10, background: "#f3f4f6", color: "#555", fontWeight: 600 }}>
                      {p.signal_strength_at_entry}
                    </span>
                  )}
                  <span style={{ fontSize: 12, color: "#9ca3af" }}>{new Date(p.opened_at).toLocaleDateString()}</span>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <input
                    type="number"
                    placeholder="Close price"
                    value={closePrices[p.id] ?? ""}
                    onChange={e => setClosePrices(prev => ({ ...prev, [p.id]: e.target.value }))}
                    style={{ padding: "6px 10px", border: "1px solid #ddd", borderRadius: 8, fontSize: 13, width: 120 }}
                  />
                  <button
                    onClick={() => closePosition(p.id)}
                    disabled={closing === p.id}
                    style={{ ...btn, background: "#dc2626", color: "#fff", borderColor: "#dc2626" }}
                  >
                    {closing === p.id ? "Closing..." : "Close"}
                  </button>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 8, fontSize: 12 }}>
                <Stat label="Shares" value={fmt(p.shares, 4)} />
                <Stat label="Entry" value={`$${fmt(p.entry_price)}`} />
                <Stat label="Stop Loss" value={`$${fmt(p.stop_loss)}`} color="#dc2626" />
                <Stat label="Take Profit" value={`$${fmt(p.take_profit)}`} color="#16a34a" />
                <Stat label="Pred Return" value={p.pred_return_at_entry != null ? `${p.pred_return_at_entry > 0 ? "+" : ""}${fmt(p.pred_return_at_entry)}%` : "—"} />
                <div style={{ padding: "8px 10px", background: "#f9fafb", borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>Unrealized P&L</div>
                  <div style={{ fontWeight: 600, fontSize: 13 }}><PnlSpan n={p.unrealized_pnl_pct} />%</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <h2 style={h2}>Trade History ({history.length})</h2>
      {history.length === 0 ? (
        <p style={{ color: "#666", fontSize: 13 }}>No closed trades yet.</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #eee", textAlign: "left" }}>
                {["Ticker", "Opened", "Closed", "Shares", "Entry", "Exit", "Reason", "P&L"].map(h => (
                  <th key={h} style={{ ...tdStyle, fontWeight: 600, color: "#555", paddingBottom: 8 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {history.map((p, i) => (
                <tr key={p.id} style={{ borderBottom: "1px solid #f3f4f6", background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                  <td style={{ ...tdStyle, fontWeight: 700 }}>{p.ticker}</td>
                  <td style={tdStyle}>{new Date(p.opened_at).toLocaleDateString()}</td>
                  <td style={tdStyle}>{p.closed_at ? new Date(p.closed_at).toLocaleDateString() : "—"}</td>
                  <td style={tdStyle}>{fmt(p.shares, 4)}</td>
                  <td style={tdStyle}>${fmt(p.entry_price)}</td>
                  <td style={tdStyle}>{p.close_price ? `$${fmt(p.close_price)}` : "—"}</td>
                  <td style={tdStyle}>{p.close_reason ?? "—"}</td>
                  <td style={tdStyle}><PnlSpan n={p.realized_pnl} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ padding: "12px 14px", border: "1px solid #eee", borderRadius: 10 }}>
      <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 4 }}>{label}</div>
      <div style={{ fontWeight: 700, fontSize: 15, color: color ?? "#111" }}>{value}</div>
    </div>
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

const page: React.CSSProperties = { padding: 24, maxWidth: 1100, margin: "0 auto" };
const h2: React.CSSProperties = { fontSize: 18, marginBottom: 12, marginTop: 0 };
const btn: React.CSSProperties = { padding: "7px 14px", border: "1px solid #ddd", borderRadius: 8, cursor: "pointer", fontSize: 13 };
const tdStyle: React.CSSProperties = { padding: "10px 12px", whiteSpace: "nowrap" };
