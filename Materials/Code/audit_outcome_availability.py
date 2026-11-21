"""Kiểm tra thời điểm outcome của cohort vận hành quanh mốc kết thúc train.

Kết quả chỉ là thống kê tổng hợp. Payment time là proxy cần kiểm chứng,
không chứng minh chính xác thời điểm mọi trường thanh toán có sẵn.
"""
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "28182251/Dataset/Charging_Data.csv"
OUTPUT = Path(__file__).resolve().parent / "pilot_results/outcome_availability_audit.json"


def main():
    """Đếm phiên train có outcome ghi nhận tại hoặc sau mốc 01/07/2021."""
    cols = ["Start Time", "End Time", "Payment time", "Transaction power/kwh"]
    df = pd.read_csv(DATA, encoding="gb18030", usecols=cols)
    for col in cols[:3]:
        df[col] = pd.to_datetime(df[col].str.strip(), errors="raise")
    cutoff = pd.Timestamp("2021-07-01")
    train = df[df["Start Time"] < cutoff]
    eligible = train[(train["Transaction power/kwh"] > 0) & (train["End Time"] > train["Start Time"])]
    late_end = eligible["End Time"] >= cutoff
    late_payment = eligible["Payment time"] >= cutoff
    summary = {
        "cutoff": cutoff.isoformat(),
        "train_events": len(train),
        "train_ending_at_or_after_cutoff": int((train["End Time"] >= cutoff).sum()),
        "operational_train_events": len(eligible),
        "operational_ending_at_or_after_cutoff": int(late_end.sum()),
        "operational_payment_at_or_after_cutoff": int(late_payment.sum()),
        "operational_end_or_payment_at_or_after_cutoff": int((late_end | late_payment).sum()),
        "caveat": "Payment timestamp is a proxy, not verified feature availability.",
    }
    OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
