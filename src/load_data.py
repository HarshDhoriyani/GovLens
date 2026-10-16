"""Load or initialize the immutable-on-rerun synthetic raw input."""

from pathlib import Path

import pandas as pd

from src.generate_data import generate_dataset


def load_or_generate_raw_data(path: Path) -> pd.DataFrame:
    """Load an existing raw CSV, or create it once if it does not exist."""
    if path.exists():
        return pd.read_csv(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = generate_dataset()
    frame.to_csv(path, index=False)
    return frame
