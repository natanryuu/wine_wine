"""
============================================================================
Step 2b: 價格預測模型 (Ridge vs Random Forest vs XGBoost)
============================================================================
目標 Y: log(price)
特徵 X:
    - points (評分,主驅動)
    - is_provence (品牌溢價 dummy)
    - country / province / variety (label encoded)
    - sans_ig_ratio (從法國海關資料 merge 進來,僅法國酒適用)
    - campagne_start (年份趨勢)
    - log_grand_total (該年該部門出莊規模)

評估: time-based split + RMSE / MAE / R²
============================================================================
"""
import numpy as np
import pandas as pd
import json, os, joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model  import Ridge
from sklearn.ensemble      import RandomForestRegressor
from sklearn.metrics       import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

OUT_DIR = "/home/claude/wine_final/outputs"
MODEL_DIR = "/home/claude/wine_final/models"
os.makedirs(MODEL_DIR, exist_ok=True)

# ---------- 1. 載入資料 ----------
wine = pd.read_csv(f"{OUT_DIR}/wine_enthusiast_simulated.csv")
feat = pd.read_csv(f"{OUT_DIR}/feature_table.csv")

# ---------- 2. 把 sans_ig_ratio 等海關特徵 merge 給法國酒 ----------
# 把每個 campagne 的 Provence 結構比 ready
prov_struct = feat[feat["is_provence"] == 1].copy()
prov_struct["dept_label"] = prov_struct["dept_code"].map({"13": "Bouches-du-Rhône", "83": "Var"})

# 取 Provence 兩個部門的「加權平均」結構 (用 grand_total 加權)
prov_agg = (prov_struct
            .groupby("campagne_start")
            .apply(lambda g: pd.Series({
                "sans_ig_ratio_prov": np.average(g["sans_ig_ratio"], weights=g["grand_total"]),
                "log_grand_total_prov": np.log1p(g["grand_total"].sum()),
                "aop_ratio_prov":     np.average(g["aop_ratio"],     weights=g["grand_total"]),
            }))
            .reset_index())

# 取法國非 Provence 部門的平均結構作為「對照」
non_prov_agg = (feat[feat["is_provence"] == 0]
                .groupby("campagne_start")
                .apply(lambda g: pd.Series({
                    "sans_ig_ratio_nonprov": np.average(g["sans_ig_ratio"], weights=g["grand_total"]),
                    "log_grand_total_nonprov": np.log1p(g["grand_total"].sum()),
                }))
                .reset_index())

# ---------- 3. 給每筆酒款分配一個 campagne_start (年份) ----------
# 模擬資料沒有年份,我們隨機分配 2019-2024
RNG = np.random.default_rng(42)
wine["campagne_start"] = RNG.choice([2019, 2020, 2021, 2022, 2023, 2024], size=len(wine))

# Merge 海關特徵: 法國 Provence 用 prov_agg, 其他法國用 non_prov_agg
wine = wine.merge(prov_agg,     on="campagne_start", how="left")
wine = wine.merge(non_prov_agg, on="campagne_start", how="left")

# 對非 Provence 的法國酒和非法國酒, sans_ig_ratio_prov 填 0 (不適用)
wine["sans_ig_ratio_applied"] = np.where(
    wine["is_provence_flag"] == 1,
    wine["sans_ig_ratio_prov"],
    wine["sans_ig_ratio_nonprov"].fillna(0)
)
wine["log_supply"] = np.where(
    wine["is_provence_flag"] == 1,
    wine["log_grand_total_prov"],
    wine["log_grand_total_nonprov"].fillna(0)
)

# ---------- 4. Label encode 類別變數 ----------
for col in ["country", "province", "variety"]:
    wine[f"{col}_enc"] = LabelEncoder().fit_transform(wine[col].astype(str))

# ---------- 5. 特徵 & 目標 ----------
features = ["points", "is_provence_flag",
            "country_enc", "province_enc", "variety_enc",
            "sans_ig_ratio_applied", "log_supply",
            "campagne_start"]
X = wine[features].copy()
y = np.log1p(wine["price"])

# ---------- 6. Time-based split ----------
train_mask = wine["campagne_start"] <= 2022
test_mask  = wine["campagne_start"] >= 2023
X_train, X_test = X[train_mask], X[test_mask]
y_train, y_test = y[train_mask], y[test_mask]
print(f"Train: {len(X_train)}, Test: {len(X_test)}")

# ---------- 7. 三模型訓練 ----------
results = {}

# Ridge
ridge = Ridge(alpha=1.0, random_state=42)
ridge.fit(X_train, y_train)
pred_r = ridge.predict(X_test)

# Random Forest
rf = RandomForestRegressor(n_estimators=300, max_depth=12,
                           min_samples_leaf=5, n_jobs=-1, random_state=42)
rf.fit(X_train, y_train)
pred_rf = rf.predict(X_test)

# XGBoost
xgb_m = xgb.XGBRegressor(n_estimators=400, max_depth=6, learning_rate=0.07,
                        subsample=0.9, colsample_bytree=0.9,
                        random_state=42, tree_method="hist")
xgb_m.fit(X_train, y_train)
pred_x = xgb_m.predict(X_test)

# ---------- 8. 評估 ----------
def metrics(y_true, y_pred):
    return {
        "RMSE_log": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAE_log":  float(mean_absolute_error(y_true, y_pred)),
        "R2":       float(r2_score(y_true, y_pred)),
        "RMSE_USD": float(np.sqrt(mean_squared_error(np.expm1(y_true), np.expm1(y_pred)))),
        "MAE_USD":  float(mean_absolute_error(np.expm1(y_true), np.expm1(y_pred))),
    }

results = {
    "Ridge":          metrics(y_test, pred_r),
    "Random Forest":  metrics(y_test, pred_rf),
    "XGBoost":        metrics(y_test, pred_x),
}

print("\n=== 三模型表現 (Test set: campagne 2023-2024) ===")
rdf = pd.DataFrame(results).T.round(4)
print(rdf.to_string())

rdf.to_csv(f"{OUT_DIR}/model_comparison.csv")

# ---------- 9. Ridge 係數表 ----------
coef_df = pd.DataFrame({
    "feature": features,
    "coef":    ridge.coef_,
}).sort_values("coef", key=abs, ascending=False)
print("\n=== Ridge 係數 (log price 的邊際效應) ===")
print(coef_df.round(4).to_string(index=False))
coef_df.to_csv(f"{OUT_DIR}/ridge_coefficients.csv", index=False)

# ---------- 10. Feature importance ----------
fi = pd.DataFrame({
    "feature": features,
    "RF_imp":  rf.feature_importances_,
    "XGB_imp": xgb_m.feature_importances_,
}).sort_values("XGB_imp", ascending=False)
print("\n=== Feature importance ===")
print(fi.round(4).to_string(index=False))
fi.to_csv(f"{OUT_DIR}/feature_importance.csv", index=False)

# ---------- 11. 儲存模型 + 預測結果 (給 Step 3 SHAP) ----------
joblib.dump(xgb_m,  f"{MODEL_DIR}/xgb.pkl")
joblib.dump(rf,     f"{MODEL_DIR}/rf.pkl")
joblib.dump(ridge,  f"{MODEL_DIR}/ridge.pkl")
X_test.to_csv(f"{OUT_DIR}/X_test.csv", index=False)
y_test.to_csv(f"{OUT_DIR}/y_test.csv", index=False)
pd.DataFrame({"y_test": y_test.values, "ridge": pred_r,
              "rf": pred_rf, "xgb": pred_x}).to_csv(
    f"{OUT_DIR}/predictions.csv", index=False)

with open(f"{OUT_DIR}/model_metrics.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n[Step 2b done]")
