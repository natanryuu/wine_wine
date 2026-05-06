# wine_wine

Mac 沒裝 pip 指令名稱很常見，用 python3 -m pip 即可：


python3 -m pip install requests pandas
如果出現 externally-managed-environment 錯誤（macOS 較新版 Python 會擋），有兩個選擇：

選項 1（推薦）：用 venv 虛擬環境


cd /Users/danniryu/Desktop/proj/wine_wine
python3 -m venv .venv
source .venv/bin/activate
pip install requests pandas
之後每次開新 terminal 要先 source .venv/bin/activate。


Pipeline 總覽

raw_data/UN/UNdata_Export_*.csv (3 檔, 978 筆)
        ↓ python un_comtrade_clean.py
data/un_comtrade_wine_clean.csv (含 4 個衍生欄位)
        ↓
                 ↘
data/rose_wines_dataset.csv (6,356 筆)
        ↓
        ↓ python wine_competitive_analysis.py
        ↓
output/
  ├── a1_export_market_share.png       (主要出口國市占率)
  ├── a2_export_unit_price.png         (出口單價趨勢)
  ├── a3_export_category_structure_2024.png  (品類結構)
  ├── a4_import_market_2024.png        (進口市場氣泡圖)
  ├── b1_rose_competitive_position.png (粉紅酒競爭定位)
  ├── b2_rose_price_tier.png           (價格帶分布)
  ├── b3_france_provinces.png          (法國各產區)
  ├── b4_rose_rating_distribution.png  (評分箱形圖)
  └── analysis_summary.csv             (報告引用用的彙總表)