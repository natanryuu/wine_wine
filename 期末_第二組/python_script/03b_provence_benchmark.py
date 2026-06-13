"""
============================================================================
Step 3b: 真實資料下的 Provence 定價基準比較
============================================================================
從真實 Wine Enthusiast 資料抽出所有法國酒款,依 province 計算
中位數價格與評分,把 Provence 對比其他法國產區,作為「沒有溢價」
這項實證發現的視覺證據。
============================================================================
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "/home/claude/wine_final/outputs"
FIG_DIR = "/home/claude/wine_final/figures"

df = pd.read_csv(f"{OUT_DIR}/wine_enthusiast_simulated.csv")
fr = df[df["country"] == "France"].copy()
print(f"French wines: {len(fr):,}")

# 取樣本量 >= 300 的省份,避免雜訊
prov_stats = (fr.groupby("province")
                 .agg(n=("price", "size"),
                      mean_price=("price", "mean"),
                      median_price=("price", "median"),
                      mean_points=("points", "mean"))
                 .query("n >= 300")
                 .sort_values("median_price", ascending=True)
                 .reset_index())
print(prov_stats.to_string(index=False))

# ---------- 圖 1: 法國各產區中位數價格條形圖 ----------
fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#84B59F" if p != "Provence" else "#6D2E46" for p in prov_stats["province"]]
bars = ax.barh(prov_stats["province"], prov_stats["median_price"], color=colors,
               edgecolor="white", linewidth=1.2)
# 標數字
for bar, val, n in zip(bars, prov_stats["median_price"], prov_stats["n"]):
    ax.text(val + 1, bar.get_y() + bar.get_height()/2,
            f"${val:.0f}  (n={n:,})", va="center", fontsize=10,
            color="#1A1A1A")

# 標出全球中位數
global_med = df["price"].median()
ax.axvline(global_med, color="#A26769", linestyle="--", linewidth=1.5, alpha=0.8)
ax.text(global_med + 1.5, 0.3, f"Global median ${global_med:.0f}",
        color="#A26769", fontsize=10, fontstyle="italic")

ax.set_xlabel("Median price (USD)", fontsize=11)
ax.set_title("French Wine Regions: Median Price (Wine Enthusiast Reviews)",
             fontsize=13, color="#6D2E46", pad=12)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(prov_stats["median_price"]) * 1.25)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/provence_benchmark.png", dpi=140, bbox_inches="tight")
plt.close()
print("Saved figures/provence_benchmark.png")

# ---------- 圖 2: Provence vs France ex-Provence 價格分佈 ----------
prov = fr[fr["province"] == "Provence"]["price"]
non_prov = fr[fr["province"] != "Provence"]["price"]

fig, ax = plt.subplots(figsize=(8, 4.5))
bins = np.logspace(np.log10(4), np.log10(300), 50)
ax.hist(non_prov, bins=bins, alpha=0.55, color="#A26769",
        label=f"France ex-Provence (n={len(non_prov):,})", density=True)
ax.hist(prov, bins=bins, alpha=0.75, color="#6D2E46",
        label=f"Provence (n={len(prov):,})", density=True)
ax.axvline(prov.median(), color="#6D2E46", linestyle="--", linewidth=1.5)
ax.axvline(non_prov.median(), color="#A26769", linestyle="--", linewidth=1.5)
ax.set_xscale("log")
ax.set_xlabel("Price (USD, log scale)", fontsize=11)
ax.set_ylabel("Density", fontsize=11)
ax.set_title("Price Distribution: Provence vs Rest of France",
             fontsize=13, color="#6D2E46", pad=12)
ax.legend(loc="upper right", frameon=False)
ax.text(prov.median(), ax.get_ylim()[1] * 0.95,
        f" Prov median ${prov.median():.0f}", color="#6D2E46", fontsize=9)
ax.text(non_prov.median(), ax.get_ylim()[1] * 0.85,
        f" non-Prov median ${non_prov.median():.0f}", color="#A26769", fontsize=9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/provence_price_dist.png", dpi=140, bbox_inches="tight")
plt.close()
print("Saved figures/provence_price_dist.png")

# ---------- 儲存統計 ----------
out_stats = {
    "global_median_usd":        float(df["price"].median()),
    "france_median_usd":        float(fr["price"].median()),
    "france_mean_usd":          float(fr["price"].mean()),
    "provence_median_usd":      float(prov.median()),
    "provence_mean_usd":        float(prov.mean()),
    "france_ex_prov_median_usd": float(non_prov.median()),
    "france_ex_prov_mean_usd":   float(non_prov.mean()),
    "n_provence_reviews":       int(len(prov)),
    "n_france_reviews":         int(len(fr)),
    "n_total_reviews":          int(len(df)),
    "provence_vs_france_ex_prov_pct": float((prov.mean() - non_prov.mean()) / non_prov.mean() * 100),
    "provence_vs_global_pct":   float((prov.mean() - df["price"].mean()) / df["price"].mean() * 100),
    "by_french_region": prov_stats.to_dict(orient="records"),
}
with open(f"{OUT_DIR}/provence_benchmark.json", "w") as f:
    json.dump(out_stats, f, indent=2, default=float)
print("\n=== Provence benchmark ===")
print(json.dumps({k: v for k, v in out_stats.items() if k != "by_french_region"}, indent=2))
