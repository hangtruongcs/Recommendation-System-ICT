"""Vẽ hình cho luận văn từ kết quả pilot validation đã lưu.

Hình accuracy–diversity dùng trung bình ba seed BPR-MF tám chiều; biểu đồ
estimator dùng một seed vì estimator được xây dựng cố định từ train. Đây là
kết quả thăm dò, không phải hiệu năng test hoặc lợi ích thực tế.
"""

from pathlib import Path
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "pilot_results"
FIGURES = ROOT.parent / "Thesis" / "figures"
SEEDS = (20261120, 20261121, 20261122)
POLICY = os.environ.get("JIAXING_FIGURE_POLICY", "legacy")
if POLICY not in {"legacy", "availability_proxy"}:
    raise ValueError(f"Chính sách biểu đồ không hợp lệ: {POLICY}")
SUFFIX = "_availability_proxy" if POLICY == "availability_proxy" else ""


def load_results():
    """Đọc kết quả tám chiều của ba seed; dừng nếu dữ liệu không phù hợp."""
    records = []
    for seed in SEEDS:
        path = RESULTS / f"results_dim_8_seed_{seed}{SUFFIX}.json"
        with path.open(encoding="utf-8") as stream:
            record = json.load(stream)
        if record["seed"] != seed or record["latent_dimensions"] != 8:
            raise ValueError(f"Cấu hình trong {path.name} không khớp tên tệp")
        if record.get("interaction_cohort", "all") != "all":
            raise ValueError(f"Cohort trong {path.name} không phải all")
        records.append(record)
    return records


def save_figure(fig, name):
    """Lưu ảnh PNG để trình bày và SVG để biên tập hoặc xuất bản."""
    for extension in ("png", "svg"):
        fig.savefig(FIGURES / f"{name}.{extension}", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_accuracy_diversity(records):
    """Vẽ trung bình NDCG@3 và ILD@3 theo ba seed trên warm validation."""
    methods = [
        ("personal_frequency", "Tần suất cá nhân", "#294879"),
        ("bpr_mf", "BPR-MF", "#347f78"),
        ("weighted_sum", "Weighted sum", "#a76435"),
        ("pareto_front_relevance", "Pareto", "#8b4e71"),
        ("diversity_greedy_alpha_0.8", "Greedy α = 0,8", "#8a762b"),
        ("diversity_greedy_alpha_0.5", "Greedy α = 0,5", "#695c9b"),
    ]
    fig, ax = plt.subplots(figsize=(8.6, 6.0), layout="constrained")
    for key, label, color in methods:
        values = [r["methods"][key] for r in records]
        x = np.mean([v["operational_ild_at_3"] for v in values])
        y = np.mean([v["ranking"]["3"]["ndcg"] for v in values])
        ax.scatter(x, y, s=95, color=color, label=label, zorder=3)
    ax.set_xlabel("ILD@3 — đa dạng theo cost và duration ước lượng")
    ax.set_ylabel("NDCG@3 — độ chính xác xếp hạng")
    ax.set_title("Đánh đổi accuracy–diversity trên validation", fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend(loc="best", frameon=False, fontsize=9)
    fig.text(0.02, -0.03, "Thăm dò; 4.851 user có lịch sử train; trung bình 3 seed; chưa đánh giá test.", fontsize=9)
    save_figure(fig, f"accuracy_diversity_validation{SUFFIX}")


def plot_estimator_errors(records):
    """So sánh MAE của estimator theo trạm và median toàn cục trên validation."""
    data = records[0]["estimator_validation"]
    values = [
        ("Khoản thực trả", "CNY", data["actual_payment_mae_cny"], data["global_actual_payment_mae_cny"]),
        ("Thời lượng phiên", "phút", data["duration_mae_min"], data["global_duration_mae_min"]),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.6), layout="constrained")
    for ax, (title, unit, site, global_) in zip(axes, values):
        bars = ax.bar(["Theo địa điểm", "Toàn cục"], [site, global_], color=["#347f78", "#adb9c5"], width=0.62)
        ax.bar_label(bars, fmt="%.2f", padding=3)
        ax.set_title(title)
        ax.set_ylabel(f"MAE ({unit})")
        ax.set_ylim(0, max(site, global_) * 1.23)
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    fig.suptitle("Sai số estimator trên phiên validation đã quan sát", fontweight="bold")
    fig.text(0.02, -0.04, "Dự đoán có điều kiện theo năng lượng thực tế; không đo outcome tại trạm chưa chọn.", fontsize=9)
    save_figure(fig, f"estimator_mae_validation{SUFFIX}")


def main():
    """Tạo các hình từ đầu ra JSON hiện có, không huấn luyện lại mô hình."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    records = load_results()
    plot_accuracy_diversity(records)
    plot_estimator_errors(records)
    print(f"Đã tạo 2 hình PNG và SVG trong {FIGURES}")


if __name__ == "__main__":
    main()
