# 期末報告_第二組 — Provence Rosé Premiumization 策略分析

普羅旺斯粉紅酒高端化（Premiumization）策略分析。本資料夾為**期末完整內容**，可獨立執行。

## 資料夾結構

```
期末_第二組/
├── stage1/          分析程式（Ch.1–Ch.5）
│   ├── run_all.py        一鍵執行全部章節
│   ├── _common.py        共用工具（畫圖樣式、統計函式、存檔）
│   ├── ch1_global_trade.py        Ch.1 全球貿易與 Premiumization
│   ├── ch2_rose_positioning.py    Ch.2 Rosé 與 Provence 定位
│   ├── ch3_french_supply_demand.py Ch.3 法國產區供需結構
│   ├── ch4_premium_strategy.py    Ch.4 高端化策略整合
│   ├── ch5_conclusion.py          Ch.5 結論彙整
│   └── generate_pptx.py           產出簡報
├── data/            分析輸入資料（9 個 csv）
├── figures/         產出圖表（fig1–fig4，共 15 張 png）
└── tables/          產出統計表格（ch1–ch5，共 12 個 csv）
```

## 執行方式

在 `期末_第二組/` 資料夾下執行：

```bash
python -m stage1.run_all
```

會依序產出 figures/ 與 tables/ 全部內容。
（需要套件：pandas、numpy、scipy、matplotlib）

## 章節 ↔ 產出對照

| 章節 | 圖表 | 表格 |
|------|------|------|
| Ch.1 全球貿易 | fig1_0 ~ fig1_3 | ch1_cagr_ranking, ch1_welch_test |
| Ch.2 Rosé/Provence 定位 | fig2_1 ~ fig2_4 | ch2_chi2, ch2_chi2_contingency, ch2_provence_terms, ch2_provence_test |
| Ch.3 法國產區供需 | fig3_1 ~ fig3_5 | ch3_descriptive_stats, ch3_paired_t, ch3_pearson_corr, ch3_sans_ig_trend |
| Ch.4 高端化策略 | fig4_1 ~ fig4_2 | ch4_market_segments |
| Ch.5 結論 | — | ch5_key_findings |
