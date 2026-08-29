"""
Run Manager & Timestamped Audit Directory Engine.
Creates isolated, timestamped folders for every execution run (runs/YYYY-MM-DD_HH-MM-SS_<prefix>/)
to store ground-truth screenshots, HTML dumps, and JSON datasets locally.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional


def create_run_directory(prefix: str = "run") -> str:
    """
    Creates and returns a dedicated timestamped directory for the current run:
    e.g. runs/2026-08-29_11-15-30_seat_analysis/
    """
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join("runs", f"{timestamp_str}_{prefix}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"📁 Saved run artifacts to folder: {run_dir}")
    return run_dir


def save_run_artifact(run_dir: str, filename: str, data: Any) -> str:
    """
    Saves text, HTML, or JSON data cleanly inside the run directory.
    """
    filepath = os.path.join(run_dir, filename)
    if isinstance(data, (dict, list)):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif isinstance(data, str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
    elif isinstance(data, bytes):
        with open(filepath, "wb") as f:
            f.write(data)
    return filepath
