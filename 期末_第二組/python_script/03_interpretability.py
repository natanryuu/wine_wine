"""
============================================================================
Step 3: 模型可解釋性 (SHAP + PDP)
- SHAP summary plot: 每個特徵對 log(price) 的影響方向 + 強度
- SHAP bar plot:  全域特徵重要性 (mean |SHAP|)
- PDP: points -> price 的非線性曲線
- 把 is_provence 的 SHAP 平均值 (溢價量化) 算出來
============================================================================
"""
import numpy as np
import pandas as pd
import joblib, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap
from sklearn.inspection import PartialDependenceDisplay

plt.rcParams["font.sans-serif"]    = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "/home/claude/wine_final/outputs"
FIG_DIR = "/home/claude/wine_final/figures"
MODEL_DIR = "/home/claude/wine_final/models"
os.makedirs(FIG_DIR, exist_ok=True)

# ---------- 1. 載入 ----------
xgb_m   = joblib.load(f"{MODEL_DIR}/xgb.pkl")
X_test  = pd.read_csv(f"{OUT_DIR}/X_test.csv")

# ---------- 2. SHAP ----------
explainer = shap.TreeExplainer(xgb_m)
shap_vals = explainer.shap_values(X_test)
print(f"SHAP shape: {shap_vals.shape}")

# 2a. Summary plot (beeswarm)
plt.figure(figsize=(9, 5))
shap.summary_plot(shap_vals, X_test, show=False, plot_size=(9, 5))
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/shap_beeswarm.png", dpi=140, bbox_inches="tight")
plt.close()
print("Saved figures/shap_beeswarm.png")

# 2b. Bar plot (global importance)
plt.figure(figsize=(8, 4.5))
shap.summary_plot(shap_vals, X_test, plot_type="bar", show=False, plot_size=(8, 4.5))
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/shap_bar.png", dpi=140, bbox_inches="tight")
plt.close()
print("Saved figures/shap_bar.png")

# ---------- 3. 量化 Provence 溢價 ----------
# SHAP 是相對於 base value 的貢獻; 取 is_provence_flag=1 的酒款 SHAP 平均
prov_col_idx = list(X_test.columns).index("is_provence_flag")
shap_provence = shap_vals[:, prov_col_idx]
prov_mask    = X_test["is_provence_flag"] == 1
nonprov_mask = X_test["is_provence_flag"] == 0

mean_shap_prov_rows    = shap_provence[prov_mask].mean()    if prov_mask.sum()    else 0
mean_shap_nonprov_rows = shap_provence[nonprov_mask].mean() if nonprov_mask.sum() else 0

# 把 log 域的 shap 轉成價格倍數
premium_multiplier = float(np.exp(mean_shap_prov_rows - mean_shap_nonprov_rows))
print(f"\nProvence 的 SHAP 溢價 (log domain): "
      f"prov_rows={mean_shap_prov_rows:.4f}, nonprov_rows={mean_shap_nonprov_rows:.4f}")
print(f"等價於價格倍數: {premium_multiplier:.3f}x  "
      f"(即 +{(premium_multiplier - 1) * 100:.1f}% 品牌溢價)")

# ---------- 4. PDP for points ----------
fig, ax = plt.subplots(figsize=(7, 4.2))
PartialDependenceDisplay.from_estimator(
    xgb_m, X_test, ["points"], ax=ax, line_kw={"color": "#6D2E46", "linewidth": 2.5}
)
ax.set_title("Partial Dependence: Wine Score → log(Price)", fontsize=13, pad=10)
ax.set_xlabel("Wine Enthusiast Score", fontsize=11)
ax.set_ylabel("Partial dependence on log(price)", fontsize=11)
ax.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/pdp_points.png", dpi=140, bbox_inches="tight")
plt.close()
print("Saved figures/pdp_points.png")

# ---------- 5. 雙特徵 PDP: points × is_provence ----------
fig, ax = plt.subplots(figsize=(7, 4.2))
PartialDependenceDisplay.from_estimator(
    xgb_m, X_test, [("points", "is_provence_flag")],
    ax=ax, contour_kw={"cmap": "RdPu"}
)
ax.set_title("PDP 2D: Score × Provence dummy", fontsize=13, pad=10)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/pdp_2d.png", dpi=140, bbox_inches="tight")
plt.close()
print("Saved figures/pdp_2d.png")

# ---------- 6. SHAP dependence: sans_ig_ratio (品質稀釋) ----------
plt.figure(figsize=(7, 4.2))
shap.dependence_plot(
    "sans_ig_ratio_applied", shap_vals, X_test,
    interaction_index="is_provence_flag", show=False
)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/shap_dep_sansig.png", dpi=140, bbox_inches="tight")
plt.close()
print("Saved figures/shap_dep_sansig.png")

# ---------- 7. 儲存量化結果 ----------
interp = {
    "mean_shap_provence_rows":    float(mean_shap_prov_rows),
    "mean_shap_nonprovence_rows": float(mean_shap_nonprov_rows),
    "provence_premium_multiplier": premium_multiplier,
    "provence_premium_pct":       float((premium_multiplier - 1) * 100),
    "top_features_by_mean_abs_shap": (
        pd.Series(np.abs(shap_vals).mean(axis=0), index=X_test.columns)
          .sort_values(ascending=False).head(8).to_dict()
    ),
}
with open(f"{OUT_DIR}/interpretability.json", "w") as f:
    json.dump(interp, f, indent=2)

print("\n=== Interpretability summary ===")
print(json.dumps(interp, indent=2))
print("\n[Step 3 done]")
