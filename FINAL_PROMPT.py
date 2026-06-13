"""
================================================================================
全球粉紅酒競爭版圖下的 Premiumization 策略分析
以公開貿易資料與消費者評鑑數據探索法國普羅旺斯 Rosé 的市場定位
================================================================================

📋 本文件分兩個階段：
   Stage 1 (期中作業)：策略分析報告 — 描述性統計 + 推論統計 + 視覺化
   Stage 2 (期末報告)：ML 建模 — 預測模型 + 方法比較 + 出口優先排序矩陣

================================================================================
STAGE 1 PROMPT — 期中作業（直接貼到 Claude Code）
================================================================================

## 專案名稱
全球粉紅酒競爭版圖下的 Premiumization 策略分析
——以公開貿易資料與消費者評鑑數據探索法國普羅旺斯 Rosé 的市場定位

## 資料清單（14 個 CSV，已在專案目錄下）

A 層 — 全球貿易（UN Comtrade）:
  un_comtrade_wine_clean.csv (978 筆, 18 國 × 6 年 × 4 品類 × 進出口)
  欄位: country, year, commodity_short, flow, trade_usd, volume_litres,
        price_per_litre, price_per_bottle_750ml

B 層 — Rosé 品質/價格（Wine Enthusiast / Vivino）:
  rose_wines_dataset.csv (6,356 筆, 30 國 rosé, 含 description 文字)
  rose_country_summary.csv (30 國彙總)
  rose_price_tier_by_country.csv (7 價格帶 × 12 國)
  france_rose_by_region.csv (法國 11 產區比較)

C 層 — 法國海關（DGDDI）:
  wine_data_all_raw.csv (13,536 筆, 94 dept × 6 campagne × 12 月 × 161A/B)
  wine_annual_summary.csv, wine_provence_monthly.csv, wine_stock_commerce.csv
  wine_supply_demand_panel.csv, wine_provence_supply_demand.csv
  wine_region_comparison.csv, wine_production_all.csv, wine_stock_production_all.csv

## 報告結構（5 章）

請依以下結構產出完整的 Python 分析程式碼 + 圖表。
所有圖表使用繁體中文標題，200 dpi PNG。

────────────────────────────────────
第 1 章：全球葡萄酒貿易與 Premiumization 趨勢
────────────────────────────────────

📂 資料：un_comtrade_wine_clean.csv

1.1 全球出口國定位圖
- 篩選 2024, Still_Bottled, Export
- 氣泡圖：x=出口量(百萬公升), y=每瓶均價(USD), bubble=出口值
- 標注法國 ($6.35), 義大利 ($3.60), 西班牙 ($2.27)
- 標注法國溢價：法國均價 / 全球加權均價 = ?x

1.2 法國出口的「量跌值穩」趨勢
- 篩選 France, Export, Still_Bottled, 2019-2024
- 雙軸圖：柱=trade_usd(十億), 折線=volume_litres(百萬L)
- 計算：volume CAGR = -3.4%, value CAGR = +2.5%, price CAGR = +6.1%
- 第二折線：price_per_bottle 趨勢 ($4.72 → $6.35)

1.3 主要出口國 6 年趨勢比較
- 篩選 France/Italy/Spain/Australia/Chile, Export, Still_Bottled
- 折線圖：各國 price_per_bottle 趨勢
- 突出法國的溢價趨勢是否在擴大

統計量：
- 法國 vs 其他國家均價的 Welch's t-test
- 各國出口量的 CAGR 排名


────────────────────────────────────
第 2 章：Rosé 市場結構與 Provence 品質定位
────────────────────────────────────

📂 資料：rose_wines_dataset.csv, rose_country_summary.csv,
       rose_price_tier_by_country.csv, france_rose_by_region.csv

2.1 全球 Rosé 價格帶分佈
- rose_price_tier_by_country.csv
- 100% 堆疊長條圖：France vs US vs Italy vs Spain
- 計算法國在 30€+ 高端帶的佔比 vs 其他國家
- 統計：卡方檢定（法國 vs 非法國的價格帶分佈是否顯著不同）

2.2 法國 Rosé 產區定位圖
- france_rose_by_region.csv
- 氣泡圖：x=avg_price, y=avg_rating, bubble=wine_count
- 11 個產區一次呈現
- 標注 Provence（954 支, 22€, 88.06 分）
  → 數量 #1、評分高、價格中高 = 性價比王者

2.3 Provence 溢價效果
- rose_wines_dataset.csv
- 分組：is_provence=1 (N=954) vs is_provence=0 (N=5402)
- 比較 price 和 points
- 箱形圖 + 統計檢定：
  - Mann-Whitney U（price 非常態，用無母數）
  - 計算效果量 (rank-biserial correlation)
  - Cohen's d（points 近似常態）

2.4 Provence Rosé 的風味語彙特徵
- rose_wines_dataset.csv 的 description 欄位
- Provence vs Non-Provence 的高頻詞比較
- 用 TF-IDF 提取 Provence 的特徵詞
- 文字雲 or 水平長條圖（top 15 特徵詞）
- → 這個分析同時為期末的 NLP 模型做準備

統計量：
- Provence vs 全球：price 中位數差異、points 均值差異
- 效果量：Cohen's d, rank-biserial r


────────────────────────────────────
第 3 章：法國產區供需結構分析
────────────────────────────────────

📂 資料：wine_supply_demand_panel.csv, wine_region_comparison.csv,
       wine_provence_monthly.csv, wine_annual_summary.csv

3.1 產區四象限定位圖 ⭐（全報告最重要）
- wine_supply_demand_panel.csv
- 計算 CAGR（6年）和 CV（波動性）per département
- 篩選：83, 13, 33, 34, 84, 11, 30, 66, 51, 21
- 散佈圖：x=CV, y=CAGR, 十字線=中位數
- 四象限標注：
  ⭐ 右下：高成長低波動 → Var (83), BdR (13)
  ⚠️ 左下：低成長高波動 → 風險區
  🔹 左上：穩定但無成長 → Bordeaux, Languedoc
- 加上中文象限名稱

3.2 庫存周轉率跨產區比較
- wine_region_comparison.csv
- 折線圖 5 產區 × 6 年
- 標注 Var 最新值 vs Bordeaux 最新值
- 統計：配對 t 檢定 (Var vs Bordeaux, p<0.001)

3.3 Var (83) 供需平衡圖
- wine_provence_supply_demand.csv, dept_code='83'
- 柱=產量 vs 出莊量, 折線=庫存
- 標注「出莊 > 產量 → 需求拉動型市場」

3.4 出莊結構變遷：AOP vs Sans IG
- wine_data_all_raw.csv, dept=83, month=7, 161A
- 堆疊面積圖：IG% vs Sans IG% (2019-2025)
- AOP 從 97.9% → 93.8%, Sans IG 從 2.1% → 6.2%
- 統計：線性趨勢 slope + R² + p-value

3.5 月度季節性 + COVID 韌性
- wine_provence_monthly.csv
- 長條圖：12 月平均出莊量，標注旺季/淡季
- COVID 前後 Mann-Whitney U (p=0.37)

3.6 描述性統計彙整表
- 常態性 4 項檢定
- Kruskal-Wallis 季節性
- Pearson 相關矩陣（產量↔出莊↔庫存↔周轉率）
- 表格呈現，附 *, **, *** 顯著標記


────────────────────────────────────
第 4 章：Premiumization 策略含義
────────────────────────────────────

整合 A+B+C 三層資料的交叉分析

4.1 三層論證整合圖
- 漏斗圖 or 金字塔圖（視覺化呈現三層論證）：
  底層：全球 premiumization（法國每瓶 $6.35, CAGR +6.1%）
  中層：Provence rosé 品質標竿（88.06 分, 22€, N=954）
  頂層：海關數據驗證（庫存周轉 4.6 月, CAGR +4.6%）

4.2 出口市場初步排序（為期末矩陣做準備）
- un_comtrade_wine_clean.csv
- 各國 import Still_Bottled 的 price_per_bottle 排名
- 市場規模 (trade_usd) × 單價 (price_per_bottle) 矩陣
- 初步分類：高價高量（美國）、高價低量（日本）、低價高量（英國）

4.3 Sans IG 擴張的策略風險
- 結合海關 Sans IG 趨勢 + rosé price_tier 分佈
- 問題：如果低端酒擴張，會不會侵蝕 Provence 的 premium 定位？

4.4 季節性的商業意涵
- 出莊旺季 (1-6月) vs rosé 消費旺季 (夏季)
- 出口商備貨節奏 → 對應訂單頻率問題


────────────────────────────────────
第 5 章：結論、限制與期末展望
────────────────────────────────────

5.1 核心結論（3 點）
1. Provence rosé 的 premiumization 有三層數據支撐
2. 供需結構健康（庫存周轉 4.6 月），問題在通路效率而非市場需求
3. Sans IG 擴張 (2.1→6.2%) 是需要關注的結構轉變

5.2 研究限制
- 海關粒度限於 département，無法區分 rosé/rouge/blanc 的出莊量
- UN Comtrade 無法拆分 rosé vs 其他靜態酒
- 消費者評鑑資料可能有選擇偏誤（高評分酒更容易被收錄）

5.3 期末報告預告
- 將建構 ML 預測模型（詳見 Stage 2）
- 將產出「出口市場優先排序矩陣」
- 將比較 Random Forest / XGBoost / Ridge 的準確度


================================================================================
技術規格
================================================================================

Python 3.10+, pandas, numpy, scipy, matplotlib, seaborn, sklearn (ch.2 TF-IDF)
字體：Noto Sans CJK TC（或 PingFang TC / Microsoft JhengHei）
圖表：200 dpi, 中文標題, 統一配色如下：
  法國/Var = #1B7A5A    BdR = #5B4EB5      Bordeaux = #C43E3E
  Languedoc = #B07316   Vaucluse = #73726C  Rosé/重點 = #D85A30
  全球/出口 = #2C5F8A

全部圖表輸出到 ./figures/ 目錄
全部統計表輸出到 ./tables/ 目錄



================================================================================
STAGE 2 PROMPT — 期末報告（ML 建模）
================================================================================

## 期末目標
1. 建構預測模型或消費者偏好分析模型
2. 比較多種機器學習方法的準確度（R², MAE, RMSE）
3. 產出可操作的「出口市場優先排序矩陣」

## 可行的 ML 方向（3 選 1 或組合）

────────────────────────────────────
方向 A：Rosé 價格預測模型（迴歸）
────────────────────────────────────

目標：預測一支 rosé 的合理價格
Y = price (連續, N=5,795 筆有價格)
X 特徵：
  - points (評分, 連續)
  - country (30 類, one-hot 或 target encoding)
  - province (155 類, 需降維)
  - variety (129 類, 需降維)
  - is_provence (二元)
  - price_tier (序數, 可做 label 也可做 feature)
  - description → TF-IDF 或 word embedding 提取特徵
  - description_length (字元數)

模型比較：
  1. Ridge Regression (baseline)
  2. Random Forest
  3. XGBoost / LightGBM
  4. (選配) Neural Network

評估：5-fold CV, R², MAE, RMSE
分析重點：
  - is_provence 的係數/特徵重要性 → Provence 溢價有多少？
  - 控制評分後，Provence 的淨溢價效果
  - SHAP 值解釋哪些特徵推高價格

📊 產出：
  - 模型比較表 (R², MAE, RMSE × 4 模型)
  - 特徵重要性圖 (top 15)
  - SHAP summary plot
  - Provence vs Non-Provence 的預測價格分佈


────────────────────────────────────
方向 B：消費者偏好分析（分類 + NLP）
────────────────────────────────────

目標：預測一支 rosé 是否為 Provence 產區
Y = is_provence (二元分類, 954 vs 5402)
X 特徵：
  - price, points
  - description → TF-IDF (top 1000 features)
  - variety, country

模型比較：
  1. Logistic Regression (baseline)
  2. Random Forest
  3. XGBoost
  4. (選配) 用 description 做 NLP 分類

評估：5-fold CV, Accuracy, Precision, Recall, F1, AUC-ROC
注意：類別不平衡 (954:5402)，需要 SMOTE 或 class_weight

分析重點：
  - TF-IDF 中哪些詞最能區分 Provence vs Non-Provence
  - → 這些詞就是 Provence rosé 的「品牌 DNA」
  - 哪些 Non-Provence 酒被模型誤判為 Provence？→ 潛在競爭者

📊 產出：
  - ROC 曲線 (4 模型疊加)
  - Confusion Matrix
  - 特徵重要性 / 係數圖（哪些詞最 Provence）
  - 誤判分析表（被誤認為 Provence 的酒 → 競爭者識別）


────────────────────────────────────
方向 C：出口市場優先排序矩陣
────────────────────────────────────

目標：為 Provence rosé 酒莊排序出口目標市場
使用 UN Comtrade + Rosé dataset 交叉分析

Step 1 — 市場吸引力評分 (UN Comtrade)
  每個進口國計算：
  - market_size = import Still_Bottled trade_usd (2024)
  - growth = import CAGR 2019-2024
  - price_acceptance = import price_per_bottle (越高越好)
  - france_penetration = France 佔該國進口的比例

Step 2 — 消費者接受度評分 (Rosé dataset)
  每個國家的 rosé 消費者：
  - avg_rating = 該國 rosé 平均評分
  - premium_ratio = 30€+ 佔比
  - provence_awareness = 該國中 is_provence=1 的比例

Step 3 — 綜合矩陣
  X = 市場吸引力 (加權 composite score)
  Y = 消費者接受度 (加權 composite score)
  bubble size = market_size
  四象限：
    ⭐ 優先進入（高吸引力 + 高接受度）
    🔸 培育型（高吸引力 + 低接受度）
    🔹 利基型（低吸引力 + 高接受度）
    ⚪ 觀望（低吸引力 + 低接受度）

Step 4 — 排名表
  加權總分排名，附各維度明細

📊 產出：
  - 出口市場優先排序矩陣（四象限氣泡圖）
  - 排名表 (top 10 市場)
  - 各市場的 radar chart（多維度比較）


────────────────────────────────────
建議組合：A + C
────────────────────────────────────

方向 A（價格預測）回答：「Provence 的 premium 到底值多少錢？」
方向 C（市場矩陣）回答：「這個 premium 應該賣去哪裡？」

兩者串起來就是完整的 premiumization 策略：
  定價策略（A 的 SHAP 分析） + 市場策略（C 的優先排序）

方向 B 也可以加入做為補充：
  用 NLP 找出 Provence rosé 的「品牌 DNA」→ 行銷策略


================================================================================
兩階段時程建議
================================================================================

Stage 1（期中，本週）:
  Day 1-2: Ch.1-2（UN Comtrade + Rosé 定位）
  Day 3-4: Ch.3（海關供需分析 + 統計檢定）
  Day 5:   Ch.4-5（策略整合 + 結論）
  Day 6:   簡報製作
  Day 7:   練講 + 調整

Stage 2（期末，2-3 週）:
  Week 1: 方向 A — 價格預測模型 + 方法比較
  Week 2: 方向 C — 出口市場矩陣
  Week 3: 整合報告 + 期末簡報

================================================================================
"""
