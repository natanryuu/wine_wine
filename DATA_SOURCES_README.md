# 期末報告資料來源與說明

## ✅ 已下載完成的資料

### 資料集 1：Wine Enthusiast 130K Reviews

- **來源**：Wine Enthusiast Magazine 專業品酒師評鑑
- **GitHub 原始倉庫**：https://github.com/lju-lazarevic/wine
- **原始來源**：Wine Enthusiast 雜誌線上評鑑（經第三方爬取整理）
- **Kaggle 頁面**：https://www.kaggle.com/zynicide/wine-reviews
- **授權**：公開學術使用
- **檔案**：`winemag_full_130k.csv`
- **筆數**：119,988 筆
- **欄位**：country, description, designation, points, price, province, region_1, region_2, taster_name, taster_twitter_handle, title, variety, winery

#### 已處理的衍生資料集

| 檔案名 | 說明 | 筆數 |
|--------|------|------|
| `rose_wines_dataset.csv` | 篩選出的粉紅酒資料（含 price_tier, is_provence 欄位） | 6,356 筆 |
| `rose_country_summary.csv` | 各國粉紅酒統計摘要（均價/均分/筆數） | 30 國 |
| `rose_price_tier_by_country.csv` | 價格帶 × 國家交叉表 | 7 tier × 12 country |
| `france_rose_by_region.csv` | 法國各產區粉紅酒統計 | 11 產區 |

#### 粉紅酒篩選邏輯
```
variety 包含 'Rosé', 'Rose', 'Rosato', 'Rosado'
OR title 包含上述關鍵詞
```

#### 關鍵發現摘要

| 國家 | 筆數 | 均價(USD) | 中位價(USD) | 均分 |
|------|------|----------|-----------|------|
| France | 2,384 | $30.64 | $18.0 | 87.6 |
| US | 1,640 | $26.22 | $20.0 | 87.8 |
| Italy | 1,243 | $21.68 | $18.0 | 87.1 |
| Spain | 331 | $13.79 | $12.0 | 85.1 |
| Portugal | 284 | $12.57 | $11.0 | 84.6 |
| Austria | 134 | $23.98 | $19.0 | 88.9 |

普羅旺斯粉紅酒：954 筆，均價 $22.09，中位價 $19.0，均分 88.1

---

## ⬇️ 需要你手動下載的資料

### 資料集 2：UN Comtrade 國際貿易資料

UN Comtrade API 需要註冊帳號（免費），本環境無法直接存取，請按以下步驟操作：

#### 步驟一：註冊帳號
1. 前往 https://comtradeplus.un.org/
2. 點擊右上角 Sign In → 用 Google 或 email 註冊（免費）

#### 步驟二：手動查詢下載
1. 登入後進入 Data Preview 頁面
2. 設定以下參數：

| 參數 | 設定值 |
|------|--------|
| **Type** | Goods (Commodities) |
| **Frequency** | Annual |
| **Classification** | HS (as reported) |
| **Commodity Code** | `2204` (Wine of fresh grapes) |
| **Reporter** | 分批查：France, Italy, Spain, Chile, Australia, United States |
| **Partner** | World (或指定：USA, UK, Germany, China, Japan, Canada) |
| **Trade Flow** | Export |
| **Period** | 2019, 2020, 2021, 2022, 2023 |

3. 點擊 "Download" → CSV 格式

#### 建議的子分類碼（更細緻分析）
- `220410` — 氣泡酒（含香檳）
- `220421` — 靜態葡萄酒，容量 ≤ 2L（主要瓶裝酒）
- `220422` — 靜態葡萄酒，2L < 容量 ≤ 10L
- `220429` — 靜態葡萄酒，容量 > 10L（散裝酒）

⚠️ 注意：HS 2204 不區分紅/白/粉紅，粉紅酒沒有獨立的 HS 碼。但可以透過「均價」推斷市場定位。

#### 替代方案（如果 UN Comtrade 太慢）
- **ITC Trade Map**：https://www.trademap.org/ （免費註冊，介面更友善）
- **UN Data**：http://data.un.org/Data.aspx?d=ComTrade&f=_l1Code:23
- **World's Top Exports**：https://www.worldstopexports.com/wine-exports-country/ （已整理好的摘要）

#### 步驟三：Python API 下載（進階，有 API key 後）
```python
pip install comtradeapicall

import comtradeapicall

# 免費 preview API（無需 key，每次最多 500 筆）
df = comtradeapicall.previewFinalData(
    typeCode='C', freqCode='A', clCode='HS',
    period='2023',
    reporterCode='251',  # France
    cmdCode='2204',
    flowCode='X',  # Export
    partnerCode=None,
    partner2Code=None, customsCode=None, motCode=None,
    maxRecords=500, format_output='JSON',
    aggregateBy=None, breakdownMode='classic',
    countOnly=None, includeDesc=True
)
```

---

### 資料集 3：Vivino 消費者資料（補充用）

#### 選項 A：Kaggle Vivino Datasets
- **Vivino Wine Data**：https://www.kaggle.com/datasets/joshuakalobbowles/vivino-wine-data
- **Vivino Red Wine**：https://www.kaggle.com/datasets/nikitatkachenko/vivinoredwine
- **Wine Rating and Price**：https://www.kaggle.com/budnyak/wine-rating-and-price
- **Wine Dataset (Elvin Rustam)**：https://www.kaggle.com/datasets/elvinrustam/wine-dataset

需要 Kaggle 帳號登入下載。

#### 選項 B：自行爬取（加分項 — 資料原創性）
GitHub 爬蟲工具：https://github.com/gugarosa/viviner
可以針對 Provence rosé 爬取最新資料，展現資料收集的獨立性。

#### 選項 C：Learning to Taste 學術資料集
- **論文**：Bender et al. (2023) "Learning to Taste: A Multimodal Wine Dataset"
- **來源**：https://thoranna.github.io/learning_to_taste/
- **內容**：897k 張酒標圖片 + 824k 條 Vivino 評論，350k+ 年份酒款
- **欄位**：year, region, rating, alcohol%, price, grape composition

---

### 資料集 4：OIV 產業報告（背景文獻用）

| 報告 | 連結 | 用途 |
|------|------|------|
| OIV 2024 年度報告 | https://www.oiv.int/sites/default/files/2025-04/EN_OIV_Press_release_State_of_the_World_Vine_and_Wine_Sector_in_2024.pdf | 全球產消結構 |
| OIV 簡報 PPT | https://www.oiv.int/sites/default/files/2025-04/OIV_State_of_the_World_Vine_and_Wine_Sector_in_2024_PPT.pdf | 圖表引用 |
| OIV 顏色別分析 | https://www.oiv.int/press/focus-evolution-world-wine-production-and-consumption-colour | 紅/白/粉紅趨勢 |
| Rosé World Tracking (CIVP) | https://www.rosewinesworldtracking.com/ | 粉紅酒專項數據 |

---

## 引用格式建議

```
Wine Enthusiast Reviews Dataset. (n.d.). Retrieved from Kaggle: 
https://www.kaggle.com/zynicide/wine-reviews. Original data from 
Wine Enthusiast Magazine (winemag.com).

UN Comtrade Database. (2025). United Nations International Trade 
Statistics. HS Code 2204 - Wine of fresh grapes. Retrieved from 
https://comtradeplus.un.org/

International Organisation of Vine and Wine (OIV). (2025). State 
of the World Vine and Wine Sector in 2024. Paris: OIV.

Conseil Interprofessionnel des Vins de Provence (CIVP) & OIV. 
Rosé Wines World Tracking. Retrieved from 
https://www.rosewinesworldtracking.com/
```
