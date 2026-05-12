"use client";

import { useEffect, useState } from "react";
import { getApiBase } from "../lib/api";

type JournalEntry = {
  id: number;
  created_at: string;
  ticker: string;
  action: string;
  reasoning: string;
  entry_price: number | null;
  pred_return: number | null;
  pred_close: number | null;
  signal_strength: string | null;
  outcome_1d: number | null;
  outcome_1w: number | null;
  outcome_1m: number | null;
  outcome_filled_at: string | null;
};

const ACTIONS = ["watch", "buy", "sell", "pass"];

function fmt(n: number | null, decimals = 2) {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toFixed(decimals);
}

function outcomeCell(n: number | null) {
  if (n == null) return <span style={{ color: "#9ca3af" }}>pending</span>;
  const color = n > 0 ? "#16a34a" : n < 0 ? "#dc2626" : "#333";
  return <span style={{ color, fontWeight: 500 }}>{n > 0 ? "+" : ""}{n.toFixed(2)}%</span>;
}

function signalBadge(s: string | null) {
  if (!s) return null;
  const colors: Record<string, { bg: string; color: string }> = {
    Strong: { bg: "#dcfce7", color: "#16a34a" },
    Medium: { bg: "#fef9c3", color: "#ca8a04" },
    Weak: { bg: "#f3f4f6", color: "#6b7280" },
  };
  const style = colors[s] ?? { bg: "#f3f4f6", color: "#333" };
  return (
    <span style={{ padding: "1px 7px", borderRadius: 10, fontSize: 11, fontWeight: 600, background: style.bg, color: style.color }}>
      {s}
    </span>
  );
}

export default function JournalPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiBase, setApiBase] = useState("http://localhost:8000/api/v1");

  const [ticker, setTicker] = useState("");
  const [action, setAction] = useState("watch");
  const [reasoning, setReasoning] = useState("");
  const [entryPrice, setEntryPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  useEffect(() => {
    const base = getApiBase();
    setApiBase(base);
    fetch(`${base}/journal`)
      .then(r => r.json())
      .then(data => { setEntries(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  async function submit() {
    if (!ticker.trim() || !reasoning.trim()) {
      setFormError("Ticker and reasoning are required.");
      return;
    }
    setFormError("");
    setSubmitting(true);
    try {
      await fetch(`${apiBase}/journal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: ticker.trim().toUpperCase(),
          action,
          reasoning: reasoning.trim(),
          entry_price: entryPrice ? parseFloat(entryPrice) : null,
        }),
      });
      const updated = await fetch(`${apiBase}/journal`).then(r => r.json());
      setEntries(updated);
      setTicker("");
      setReasoning("");
      setEntryPrice("");
      setAction("watch");
    } catch (e: any) {
      setFormError(e.message ?? "Failed to save.");
    } finally {
      setSubmitting(false);
    }
  }

  async function deleteEntry(id: number) {
    await fetch(`${apiBase}/journal/${id}`, { method: "DELETE" });
    setEntries(e => e.filter(x => x.id !== id));
  }

  return (
    <main style={{ padding: 24, maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Decision Journal</h1>
      <p style={{ color: "#666", marginTop: 0, marginBottom: 20, fontSize: 13 }}>
        Log your reasoning. Outcomes are filled automatically from price data after 1 day, 1 week, and 1 month.
      </p>

      <section style={{ padding: 20, border: "1px solid #eee", borderRadius: 12, marginBottom: 28 }}>
        <h2 style={h2}>New Entry</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div>
            <label style={label}>Ticker</label>
            <input value={ticker} onChange={e => setTicker(e.target.value)} placeholder="AAPL" style={input} />
          </div>
          <div>
            <label style={label}>Action</label>
            <select value={action} onChange={e => setAction(e.target.value)} style={input}>
              {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <label style={label}>Entry Price (optional)</label>
            <input value={entryPrice} onChange={e => setEntryPrice(e.target.value)} placeholder="182.50" type="number" style={input} />
          </div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label style={label}>Reasoning</label>
          <textarea
            value={reasoning}
            onChange={e => setReasoning(e.target.value)}
            placeholder="Why are you considering this? What does the chart show? What's your thesis?"
            style={{ ...input, width: "100%", height: 80, resize: "vertical", boxSizing: "border-box" }}
          />
        </div>
        {formError && <p style={{ color: "#dc2626", fontSize: 13, margin: "0 0 8px" }}>{formError}</p>}
        <button onClick={submit} disabled={submitting} style={{ ...btn, background: "#000", color: "#fff", borderColor: "#000" }}>
          {submitting ? "Saving..." : "Save Entry"}
        </button>
      </section>

      {loading ? (
        <p style={{ color: "#666" }}>Loading entries...</p>
      ) : entries.length === 0 ? (
        <p style={{ color: "#666" }}>No entries yet. Log your first decision above.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {entries.map(e => (
            <div key={e.id} style={{ padding: 16, border: "1px solid #eee", borderRadius: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{ fontWeight: 700, fontSize: 16 }}>{e.ticker}</span>
                  <span style={{ padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 600, background: "#f3f4f6", color: "#374151" }}>{e.action}</span>
                  {signalBadge(e.signal_strength)}
                  <span style={{ fontSize: 12, color: "#9ca3af" }}>{new Date(e.created_at).toLocaleDateString()}</span>
                </div>
                <button onClick={() => deleteEntry(e.id)} style={{ background: "none", border: "none", cursor: "pointer", color: "#9ca3af", fontSize: 16 }}>✕</button>
              </div>

              <p style={{ margin: "0 0 12px", fontSize: 13, color: "#374151", lineHeight: 1.5 }}>{e.reasoning}</p>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 8, fontSize: 12 }}>
                {e.entry_price != null && (
                  <div style={statBox}>
                    <div style={statLabel}>Entry Price</div>
                    <div style={statVal}>${fmt(e.entry_price)}</div>
                  </div>
                )}
                {e.pred_return != null && (
                  <div style={statBox}>
                    <div style={statLabel}>Predicted Return</div>
                    <div style={statVal}>{e.pred_return > 0 ? "+" : ""}{fmt(e.pred_return)}%</div>
                  </div>
                )}
                <div style={statBox}>
                  <div style={statLabel}>1-Day Outcome</div>
                  <div style={statVal}>{outcomeCell(e.outcome_1d)}</div>
                </div>
                <div style={statBox}>
                  <div style={statLabel}>1-Week Outcome</div>
                  <div style={statVal}>{outcomeCell(e.outcome_1w)}</div>
                </div>
                <div style={statBox}>
                  <div style={statLabel}>1-Month Outcome</div>
                  <div style={statVal}>{outcomeCell(e.outcome_1m)}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}

const h2: React.CSSProperties = { marginTop: 0, fontSize: 16, marginBottom: 12 };
const label: React.CSSProperties = { display: "block", fontSize: 12, fontWeight: 600, color: "#555", marginBottom: 4 };
const input: React.CSSProperties = { width: "100%", padding: "8px 10px", border: "1px solid #ddd", borderRadius: 8, fontSize: 13, boxSizing: "border-box" };
const btn: React.CSSProperties = { padding: "8px 16px", border: "1px solid #ddd", borderRadius: 8, cursor: "pointer", fontSize: 13 };
const statBox: React.CSSProperties = { padding: "8px 10px", background: "#f9fafb", borderRadius: 8 };
const statLabel: React.CSSProperties = { color: "#9ca3af", fontSize: 11, marginBottom: 2 };
const statVal: React.CSSProperties = { fontWeight: 600, fontSize: 13 };
