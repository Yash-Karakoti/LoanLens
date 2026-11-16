"""Download authentic observations once; never overwrite raw data."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import pandas as pd

from src.common import ROOT, file_hash, load_data, write_json

SOURCES = [
    "https://datahack-prod.s3.ap-south-1.amazonaws.com/train_file/train_u6lujuX_CVtuZ9i.csv",
    "https://raw.githubusercontent.com/Architectshwet/Loan-prediction-using-Machine-Learning-and-Python/master/data/train_u6lujuX_CVtuZ9i.csv",
    "https://raw.githubusercontent.com/Paliking/ML_examples/master/LoanPrediction/train_u6lujuX_CVtuZ9i.csv",
]


def main() -> None:
    """Try three authentic URLs in order and retain source and checksum."""
    destination = ROOT / "data/raw/train.csv"
    if destination.exists():
        data = load_data()
        print(f"Existing immutable raw file verified: {data.shape}")
        return
    failures: list[str] = []
    for url in SOURCES:
        try:
            request = Request(url, headers={"User-Agent": "College-Loan-Research/1.0"})
            with urlopen(request, timeout=30) as response:
                payload = response.read(2_000_000)
                resolved_url = response.geturl()
            frame = pd.read_csv(io.BytesIO(payload))
            if frame.shape != (614, 13) or "Loan_Status" not in frame:
                raise ValueError(f"Unexpected Dream Housing schema/shape: {frame.shape}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as output:
                output.write(payload)
            write_json(ROOT / "data/raw/source.json", {
                "url": url, "resolved_url": resolved_url,
                "downloaded_utc": datetime.now(timezone.utc).isoformat(),
                "sha256": file_hash(destination), "bytes": len(payload),
                "kaggle": "No CLI or credential file/environment token available; public URL fallback.",
                "license": "Dataset redistribution license unverified; raw CSV excluded from Git.",
                "failed_urls": failures,
            })
            print(f"Downloaded {frame.shape} from {url}")
            print(f"SHA256 {file_hash(destination)}")
            return
        except (OSError, ValueError) as error:
            failures.append(f"{url}: {type(error).__name__}: {error}")
            print(failures[-1])
    blocker = "\n## Dataset download blocked\n\nAll three authentic sources failed. No synthetic replacement created.\n\n" + "\n".join(f"- {item}" for item in failures) + "\n"
    with (ROOT / "docs/BLOCKERS.md").open("a", encoding="utf-8") as output:
        output.write(blocker)
    raise RuntimeError("No authentic dataset available; data-dependent phases must stop.")


if __name__ == "__main__":
    main()
