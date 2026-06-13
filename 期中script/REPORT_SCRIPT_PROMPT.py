"""
================================================================================
🍷 PROVENCE ROSÉ 產業分析報告 — 完整劇本 & PROMPT
================================================================================

📋 報告結構：5 幕制，從全球 → 法國 → 產區 → 酒莊 → 結論
⏱  預估時長：17-20 分鐘（含 Q&A 約 25 分鐘）
📊 資料來源：UN Comtrade + Vivino/WineEnthusiast + 法國海關 DGDDI + Vignelaure 論文

================================================================================
你的完整資料清單 (14 個 CSV):
================================================================================

【A 層 — 全球貿易】UN Comtrade (978 筆)
  un_comtrade_wine_clean.csv
  → 18 國 × 6 年 (2019-2024) × 4 品類 × 進出口
  → 欄位: country, year, commodity_short, flow, trade_usd, volume_litres, 
           price_per_litre, price_per_bottle_750ml

【B 層 — Rosé 品質/價格定位】Vivino/WineEnthusiast (6,356 筆)
  rose_wines_dataset.csv      — 30 國 rosé 品項，含評分、價格、產區、is_provence 標記
  rose_country_summary.csv    — 30 國彙總統計
  rose_price_tier_by_country.csv — 價格帶 × 國家交叉表
  france_rose_by_region.csv   — 法國 11 產區 rosé 比較

【C 層 — 法國海關供需】DGDDI (13,536 筆)
  wine_data_all_raw.csv           — 完整原始 (dept × month × 161A/B)
  wine_annual_summary.csv         — 年度出莊量彙總
  wine_provence_monthly.csv       — Provence 月度出莊量
  wine_stock_commerce.csv         — Provence 商業庫存
  wine_supply_demand_panel.csv    — 供需 panel (含庫存周轉率)
  wine_provence_supply_demand.csv — Provence 供需詳細
  wine_region_comparison.csv      — 5 產區比較
  wine_production_all.csv         — 產量申報
  wine_stock_production_all.csv   — 生產庫存

【D 層 — 酒莊微觀】Vignelaure 論文
  → 你自己的多元迴歸分析結果（B2B 通路、訂單頻率、價格敏感度）


================================================================================
PROMPT — 直接貼到 Claude Code 使用
================================================================================

## 角色與目標

你是一位葡萄酒產業分析師，要幫我製作一份完整的分析報告。
報告主題：「Provence Rosé 產業供需分析：從全球貿易到酒莊通路」

## 手上的資料

我有 14 個 CSV 檔案（見下方清單），涵蓋四個分析層次：
- A 層：UN Comtrade 全球葡萄酒貿易 (978 筆, 2019-2024)
- B 層：Rosé 品質/價格數據 (6,356 筆, 30 國)
- C 層：法國海關出莊量/庫存/產量 (13,536 筆, 2019-2025)
- D 層：Château Vignelaure B2B 通路分析 (我的論文)

## 報告劇本（5 幕制）

請依照以下劇本順序，產出分析程式碼和視覺化圖表。
每一幕都標記了要用哪個 CSV、要算什麼、要畫什麼圖。

────────────────────────────────────
第 1 幕：全球葡萄酒貿易格局 (3 min)
────────────────────────────────────

目的：建立「全球市場在縮，但法國出口值仍然第一」的大背景

📂 使用資料：un_comtrade_wine_clean.csv

分析 1.1 — 法國出口領先地位
- 篩選 2024 年 Still_Bottled Export
- 按 trade_usd 排名前 10 國
- 計算法國 price_per_bottle_750ml vs 全球平均 → 法國溢價倍數
- 📊 圖表：水平長條圖，x=出口值(十億美元)，標注每瓶均價

分析 1.2 — 法國出口趨勢 (量跌值穩)
- 篩選 France + Export + Still_Bottled，2019-2024
- 畫 trade_usd 和 volume_litres 雙軸圖
- 計算 price_per_bottle 趨勢 (4.72€ → 6.35€)
- 📊 圖表：柱狀圖(值) + 折線(量) + 折線(均價)

分析 1.3 — 主要出口國價格定位
- 篩選 2024 Still_Bottled Export
- 散佈圖：x=出口量, y=每瓶均價, bubble size=出口值
- 標注法國位置（高價低量 vs 義大利低價高量）
- 📊 圖表：氣泡圖

🎤 講稿重點：
「法國每瓶酒出口均價 6.35 美元，是西班牙的 2.8 倍、義大利的 1.8 倍。
 量在縮，但價在升——這就是 premiumization。」


────────────────────────────────────
第 2 幕：Rosé 的全球地位 (3 min)
────────────────────────────────────

目的：聚焦到 rosé 這個品類，說明 Provence 為什麼是標準

📂 使用資料：rose_wines_dataset.csv, rose_country_summary.csv,
           rose_price_tier_by_country.csv, france_rose_by_region.csv

分析 2.1 — Rosé 價格帶分佈
- 用 rose_price_tier_by_country.csv
- 畫堆疊長條圖：法國 vs 美國 vs 義大利 的價格帶分佈
- 突出法國在 50-100€ 和 100+€ 的壓倒性佔比
- 📊 圖表：100% 堆疊長條圖

分析 2.2 — Provence vs 法國其他產區
- 用 france_rose_by_region.csv
- 散佈圖：x=avg_price, y=avg_rating, bubble size=wine_count
- 標注 Provence（數量最多 954 支、評分 88.06、均價 22€）
- 對比 Champagne（高價但是氣泡酒）、Bordeaux（低分低價）
- 📊 圖表：氣泡圖

分析 2.3 — Provence rosé 的價格溢價
- 用 rose_wines_dataset.csv
- 比較 is_provence=1 vs is_provence=0 的 price 和 points
- Mann-Whitney U 檢定（因為 price 非常態）
- 📊 圖表：箱形圖 (Provence vs Non-Provence)

🎤 講稿重點：
「在全球 6,356 支 rosé 中，Provence 佔 954 支（15%），
 均價 22€ 高於全球中位數 18€，評分 88.06 高於平均 87.3。
 它不只是法國最大的 rosé 產區，也是全球 rosé 的品質標竿。」


────────────────────────────────────
第 3 幕：Provence 供需健檢 (4 min)
────────────────────────────────────

目的：用海關數據證明 Provence 供需健康，是唯一的「反例」

📂 使用資料：wine_supply_demand_panel.csv, wine_region_comparison.csv,
           wine_provence_monthly.csv, wine_annual_summary.csv

分析 3.1 — 四象限定位圖
- 用 wine_supply_demand_panel.csv
- 計算每個 département 的 6 年 CAGR 和 CV
- 篩選主要產區 (83, 13, 33, 34, 84, 11, 30, 66, 51, 21)
- 散佈圖：x=CV(波動性), y=CAGR(成長性)
- 畫十字線（中位數分隔四象限）
- 標注 Var → ⭐高成長低波動，Bordeaux → ⚠️衰退
- 📊 圖表：四象限散佈圖（這是全簡報最重要的一張圖）

分析 3.2 — 庫存周轉率比較
- 用 wine_region_comparison.csv
- 折線圖：5 產區 × 6 年周轉率
- 標注 Var 3.8 月 vs Bordeaux 23.8 月
- 📊 圖表：折線圖 + 標注

分析 3.3 — Var 供需等式
- 用 wine_provence_supply_demand.csv (dept=83)
- 柱狀圖：產量 vs 出莊量，折線：庫存
- 標注「出莊 > 產量 = 需求拉動」
- 📊 圖表：雙軸柱狀+折線

分析 3.4 — 季節性 & COVID 韌性
- 用 wine_provence_monthly.csv (dept=83)
- 月度季節性長條圖（標注旺季/淡季）
- COVID 前後比較（Mann-Whitney U, p=0.37 → 無顯著衝擊）
- 📊 圖表：季節性長條圖

分析 3.5 — 描述性統計表
- 呈現關鍵統計量：
  - 常態性檢定（Shapiro-Wilk → 非常態，因季節性）
  - Kruskal-Wallis（季節性 p<0.001）
  - 配對 t 檢定（Var vs Bordeaux 周轉率 p<0.001）
  - Pearson 相關（產量↔出莊 r=0.915***）
- 📊 表格：統計檢定摘要表

🎤 講稿重點：
「全法 91 個省，只有 Provence 落在四象限圖的最佳位置。
 庫存 4.6 個月清空，Bordeaux 要 21.2 個月——差 4.6 倍。
 連 COVID 都沒有顯著衝擊（p=0.37）。
 數據告訴我們：Provence 產區很健康。那問題在哪裡？」


────────────────────────────────────
第 4 幕：鏡頭拉近 — Vignelaure (4 min)
────────────────────────────────────

目的：話鋒一轉，從宏觀健康的產區拉近到個別酒莊的結構性矛盾

📂 使用資料：你的 Vignelaure 論文數據 + 海關資料做對照

分析 4.1 — 通路結構矛盾
- 呈現你的論文核心發現：
  - 出口商訂單頻率最低（但出口是最大成長來源）
  - 出口對價格敏感度最高（但產區在走 premiumization）
  - 訂單頻率是銷售績效最強預測因子
- 📊 圖表：用你論文裡的迴歸係數表 or 通路比較表

分析 4.2 — 微觀 vs 宏觀對照
- 建立對照表：
  | 宏觀 (海關) | 微觀 (Vignelaure) | 解讀 |
  |---|---|---|
  | 季節性 p<0.001 | 出口商低頻 | 產業結構決定 |
  | AOP 93.8% | 出口價格敏感 | 溢價被中間商截走 |
  | 周轉率 4.6 月 | 訂單頻率最重要 | 不是需求問題，是效率問題 |
- 📊 圖表：對照表 or 流程圖

分析 4.3 — Sans IG 擴張的警訊
- 用 wine_data_all_raw.csv (dept=83, July 161A)
- 畫 AOP% vs Sans IG% 趨勢：2.1% → 6.2%
- 📊 圖表：面積圖（AOP/IGP/Sans IG 結構變遷）

🎤 講稿重點：
「產區沒問題，問題在酒莊的通路效率。
 出口商是最大的成長引擎，但他們一年只來 1-2 次，而且最會砍價。
 這就是結構性矛盾——你最需要的客戶，恰好最難伺候。」


────────────────────────────────────
第 5 幕：結論與策略建議 (3 min)
────────────────────────────────────

目的：把四層分析合在一起，提出可行的策略建議

分析 5.1 — 三層論證金字塔
- 📊 圖表：金字塔圖 or 漏斗圖
  - 底層：全球 premiumization（UN Comtrade：法國每瓶 6.35$）
  - 中層：Provence rosé 品質標竿（6,356 支中評分最高群）
  - 上層：海關數據驗證供需健康（庫存周轉 4.6 月）
  - 頂端：酒莊策略 = 提高出口訂單頻率 + 抓住 premiumization

分析 5.2 — 策略建議
1. 不需要降價搶市場（庫存周轉率證明需求充足）
2. 提高出口商訂單頻率（從年度大單 → 季度補貨）
3. 關注 Sans IG 擴張（2.1% → 6.2%，低端化風險）
4. 利用季節性（春季提前備貨 → 夏季 rosé 旺季）

分析 5.3 — 研究限制 & 未來方向
- 海關數據粒度限於 département，無法區分個別酒莊
- 出莊量 ≠ 銷售量（含調撥）
- 未來可加入 OIV 全球消費數據、氣候數據、匯率數據做預測模型

🎤 收尾金句：
「法國葡萄酒市場在縮，但 Provence 在長。
 Provence 在長，但個別酒莊的通路結構讓它沒有完全吃到紅利。
 我的分析就是在找那個漏洞——然後告訴你怎麼補上。」


================================================================================
技術需求
================================================================================

- 語言：Python 3.10+
- 套件：pandas, numpy, scipy, matplotlib, seaborn
- 字體：Noto Sans CJK TC（繁中）或 PingFang TC (macOS)
- 圖表：200 dpi PNG，中文標題與標注
- 配色：
  Var (83) = #1B7A5A (綠)
  BdR (13) = #5B4EB5 (紫)
  Bordeaux (33) = #C43E3E (紅)
  Languedoc (34) = #B07316 (橙)
  Rosé / 庫存 = #D85A30 (橘)
  法國出口 = #2C5F8A (深藍)

================================================================================
"""
