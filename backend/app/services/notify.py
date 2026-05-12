"""
Daily email notification service.
Fill in SMTP_HOST, SMTP_USER, SMTP_PASSWORD, NOTIFY_EMAIL_TO in .env to activate.
Sends a morning summary: top signals, open positions, P&L.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _enabled() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.notify_email_to)


def send_daily_summary(signals: list[dict], positions: list[dict], pnl: dict) -> bool:
    if not _enabled():
        logger.info("Email not configured — skipping daily summary")
        _log_summary(signals, positions, pnl)
        return False

    subject = f"📈 Daily Trading Summary — {len([s for s in signals if s.get('criteria_met')])} signals"
    body = _build_body(signals, positions, pnl)

    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = settings.notify_email_from or settings.smtp_user
        msg["To"] = settings.notify_email_to

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info("Daily summary email sent to %s", settings.notify_email_to)
        return True
    except Exception as e:
        logger.warning("Failed to send daily summary email: %s", e)
        return False


def _build_body(signals: list[dict], positions: list[dict], pnl: dict) -> str:
    lines = ["=== DAILY TRADING SUMMARY ===\n"]

    actionable = [s for s in signals if s.get("criteria_met")]
    lines.append(f"TOP SIGNALS ({len(actionable)} meet buy criteria):")
    for s in signals[:5]:
        mark = "✅" if s.get("criteria_met") else "  "
        pred = s.get("pred_return")
        rmse = s.get("rmse")
        pred_str = f"+{pred:.2f}%" if pred and pred > 0 else f"{pred:.2f}%" if pred else "—"
        rmse_str = f"±{rmse:.2f}%" if rmse else "—"
        lines.append(f"  {mark} {s['ticker']:6} | pred: {pred_str:8} | error: {rmse_str:8} | signal: {s.get('signal_strength', '—')}")
        if s.get("criteria_met"):
            lines.append(f"       → {s.get('suggested_shares', 0):.2f} shares @ ${s.get('price', 0):.2f} | SL: ${s.get('suggested_stop_loss', 0):.2f} | TP: ${s.get('suggested_take_profit', 0):.2f}")

    lines.append(f"\nOPEN POSITIONS ({len(positions)}):")
    if positions:
        for p in positions:
            pnl_pct = p.get("unrealized_pnl_pct", 0)
            sign = "+" if pnl_pct >= 0 else ""
            lines.append(f"  {p['ticker']:6} | {p.get('shares', 0):.2f} shares @ ${p.get('entry_price', 0):.2f} | P&L: {sign}{pnl_pct:.2f}%")
    else:
        lines.append("  No open positions.")

    lines.append(f"\nPORTFOLIO:")
    lines.append(f"  Capital:        ${pnl.get('capital', 0):,.2f}")
    lines.append(f"  Unrealized P&L: ${pnl.get('unrealized_pnl', 0):+,.2f}")
    lines.append(f"  Realized P&L:   ${pnl.get('realized_pnl', 0):+,.2f}")
    lines.append(f"  Win rate:       {pnl.get('win_rate_pct', 0):.1f}%")

    return "\n".join(lines)


def _log_summary(signals: list[dict], positions: list[dict], pnl: dict) -> None:
    """Fallback: just log the summary when email is not configured."""
    logger.info("=== DAILY SUMMARY (email not configured) ===")
    for s in signals[:5]:
        logger.info("Signal: %s | pred: %s%% | criteria_met: %s",
                    s.get("ticker"), s.get("pred_return"), s.get("criteria_met"))
    logger.info("Open positions: %d | Realized P&L: $%s", len(positions), pnl.get("realized_pnl", 0))
