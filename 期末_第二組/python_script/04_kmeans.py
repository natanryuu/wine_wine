"""
============================================================================
Step 4: K-Means 產區分群 — 法國 90+ 部門依出莊結構自動分群
============================================================================
特徵:
    - log_grand_total       (年產量規模)
    - aop_ratio             (AOP 比例 = 高端定位)
    - igp_ratio             (中價帶比例)
    - sans_ig_ratio         (Sans IG = 低端/工業酒比例)
    - stock_turnover_months (周轉效率)

目標: 找出 4 群「策略上類似的法國產區」,並把 Var/BdR 標出來。
這就是把期中的「描述性矩陣」升級為 ML 分群矩陣。
============================================================================
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster        import KMeans
from sklearn.preprocessing  import StandardScaler
from sklearn.decomposition  import PCA
from sklearn.metrics        import silhouette_score
import json, os

plt.rcParams["font.sans-serif"]    = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = "/home/claude/wine_final/outputs"
FIG_DIR = "/home/claude/wine_final/figures"
os.makedirs(FIG_DIR, exist_ok=True)

# ---------- 1. 載入 + 取 2023-2024 年最近完整資料 ----------
feat = pd.read_csv(f"{OUT_DIR}/feature_table.csv", dtype={"dept_code": str})
feat["dept_code"] = feat["dept_code"].str.zfill(2)
recent = feat[feat["campagne"] == "2023-2024"].copy()
# 只保留有實際出莊的部門
recent = recent[recent["grand_total"] >= 10000].copy()
recent["log_grand_total"] = np.log1p(recent["grand_total"])

X = recent[["log_grand_total", "aop_ratio", "igp_ratio",
            "sans_ig_ratio", "stock_turnover_months"]].copy()
X = X.fillna(X.median())

scaler = StandardScaler()
Xs = scaler.fit_transform(X)

# ---------- 2. 選 K (silhouette + elbow) ----------
sil_scores = []
inertias   = []
ks = list(range(2, 8))
for k in ks:
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(Xs)
    sil_scores.append(silhouette_score(Xs, km.labels_))
    inertias.append(km.inertia_)

best_k = ks[int(np.argmax(sil_scores))]
print(f"Silhouette scores: {dict(zip(ks, [round(s, 3) for s in sil_scores]))}")
print(f"Best K (max silhouette) = {best_k}")

# 視覺化 silhouette + elbow
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
ax[0].plot(ks, sil_scores, marker="o", color="#6D2E46", linewidth=2)
ax[0].set_xlabel("K"); ax[0].set_ylabel("Silhouette")
ax[0].set_title("Silhouette Score by K"); ax[0].grid(alpha=0.3)
ax[1].plot(ks, inertias, marker="s", color="#A26769", linewidth=2)
ax[1].set_xlabel("K"); ax[1].set_ylabel("Inertia")
ax[1].set_title("Elbow Plot"); ax[1].grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/kmeans_diagnostics.png", dpi=140, bbox_inches="tight")
plt.close()

# ---------- 3. 用 best_k 做最終分群 ----------
km = KMeans(n_clusters=best_k, random_state=42, n_init=20).fit(Xs)
recent["cluster"] = km.labels_

# ---------- 4. 用 PCA 投影到 2D 視覺化 ----------
pca = PCA(n_components=2, random_state=42)
proj = pca.fit_transform(Xs)
recent["pc1"], recent["pc2"] = proj[:, 0], proj[:, 1]

# ---------- 5. Cluster 命名 (按 aop_ratio 與 grand_total 中位數命名) ----------
profile = (recent.groupby("cluster")
                 .agg(n=("dept_code", "size"),
                      median_total=("grand_total", "median"),
                      median_aop=("aop_ratio", "median"),
                      median_igp=("igp_ratio", "median"),
                      median_sansig=("sans_ig_ratio", "median"),
                      median_turnover=("stock_turnover_months", "median"))
                 .round(3))
print("\n=== Cluster profile ===")
print(profile.to_string())

# 自動命名邏輯
def name_cluster(row):
    if row["median_aop"] >= 0.5:
        if row["median_total"] >= 500000:
            return "Premium-Scale"
        return "Premium-Niche"
    elif row["median_sansig"] >= 0.5:
        return "Industrial-Bulk"
    elif row["median_igp"] >= 0.4:
        return "IGP-led Mid"
    else:
        return "Mixed Mid-tier"

profile["label"] = profile.apply(name_cluster, axis=1)
print("\n=== Cluster labels ===")
print(profile[["label", "n"]].to_string())

cluster_label_map = profile["label"].to_dict()
recent["cluster_label"] = recent["cluster"].map(cluster_label_map)

# ---------- 6. PCA 散點圖 + 標出 Var/BdR ----------
colors = ["#6D2E46", "#A26769", "#84B59F", "#69A297", "#50808E", "#2F3C7E"]
fig, ax = plt.subplots(figsize=(9, 6))
for c in sorted(recent["cluster"].unique()):
    sub = recent[recent["cluster"] == c]
    ax.scatter(sub["pc1"], sub["pc2"], s=70, alpha=0.65,
               color=colors[c % len(colors)],
               label=f"C{c}: {cluster_label_map[c]} (n={len(sub)})",
               edgecolor="white", linewidth=0.8)

# 標出 Provence 兩個部門
for _, row in recent[recent["dept_code"].isin(["13", "83"])].iterrows():
    ax.annotate(f"{row['dept_code']} ({row['dept_name'][:12]})",
                xy=(row["pc1"], row["pc2"]),
                xytext=(7, 7), textcoords="offset points",
                fontsize=10, fontweight="bold", color="#1A1A1A",
                bbox=dict(boxstyle="round,pad=0.3", fc="#FFF8E1", ec="#C9A227"))

ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} var)", fontsize=11)
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} var)", fontsize=11)
ax.set_title(f"K-Means Clustering of French Wine Departments "
             f"(K={best_k}, 2023-2024)", fontsize=13, pad=12)
ax.legend(loc="best", fontsize=8.5, framealpha=0.95)
ax.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(f"{FIG_DIR}/kmeans_pca_scatter.png", dpi=140, bbox_inches="tight")
plt.close()
print("Saved figures/kmeans_pca_scatter.png")

# ---------- 7. 輸出結果 ----------
recent[["dept_code", "dept_name", "grand_total",
        "aop_ratio", "igp_ratio", "sans_ig_ratio", "stock_turnover_months",
        "cluster", "cluster_label", "pc1", "pc2"]].to_csv(
    f"{OUT_DIR}/dept_clusters.csv", index=False)

# 把 Var 與 BdR 所屬群印出來
print("\n=== Var (83) 與 BdR (13) 落在哪一群? ===")
print(recent[recent["dept_code"].isin(["13", "83"])]
      [["dept_code", "dept_name", "cluster", "cluster_label",
        "grand_total", "aop_ratio", "sans_ig_ratio"]]
      .to_string(index=False))

# 各群的代表性部門 (前 5 大)
print("\n=== 每群的前 5 大部門 ===")
for c, lbl in cluster_label_map.items():
    top = (recent[recent["cluster"] == c]
           .nlargest(5, "grand_total")
           [["dept_code", "dept_name", "grand_total", "aop_ratio", "sans_ig_ratio"]])
    print(f"\n--- Cluster {c}: {lbl} ---")
    print(top.to_string(index=False))

profile["cluster"] = profile.index
profile.reset_index(drop=True).to_csv(
    f"{OUT_DIR}/cluster_profile.csv", index=False)

# 給簡報用的關鍵數字
out = {
    "best_k":  int(best_k),
    "silhouette_at_best_k": float(max(sil_scores)),
    "var_cluster":   int(recent[recent["dept_code"] == "83"]["cluster"].iloc[0]),
    "bdr_cluster":   int(recent[recent["dept_code"] == "13"]["cluster"].iloc[0]),
    "var_cluster_label":   recent[recent["dept_code"] == "83"]["cluster_label"].iloc[0],
    "bdr_cluster_label":   recent[recent["dept_code"] == "13"]["cluster_label"].iloc[0],
    "pca_explained":  [float(v) for v in pca.explained_variance_ratio_],
}
with open(f"{OUT_DIR}/cluster_summary.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\nKey summary: {out}")
print("\n[Step 4 done]")
