from fastapi import APIRouter, HTTPException
from pathlib import Path
import joblib

router = APIRouter()

ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "ml_artifacts"

@router.get("/model/{ticker}")
def model_status(ticker: str):
    t = ticker.upper().strip()
    path = ARTIFACT_DIR / f"{t}.joblib"
    if not path.exists():
        raise HTTPException(status_code=404, detail="model not found")

    artifact = joblib.load(path)
    return {
        "ticker": artifact.get("ticker"),
        "window": artifact.get("window"),
        "trained_at": artifact.get("trained_at"),
        "rmse_return": artifact.get("rmse_return"),
        "last_ts": artifact.get("last_ts"),
        "last_close": artifact.get("last_close"),
        "resid_std": artifact.get("resid_std"),
        "artifact_path": str(path),
    }
