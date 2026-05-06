"""
🍷 Vivino Rosé Wine Scraper — 期末報告專用
============================================
針對全球粉紅酒市場競爭分析，爬取 Vivino API 的公開資料

資料來源：Vivino 內部 API (https://www.vivino.com/api/)
爬蟲原始參考：https://github.com/gugarosa/viviner
本腳本由原始 viviner 改寫，新增國家迴圈、CSV 輸出、粉紅酒篩選

使用方式：
    pip install requests pandas
    python vivino_rose_scraper.py

輸出檔案：
    vivino_rose_raw.csv          — 所有爬取的粉紅酒原始資料
    vivino_rose_with_reviews.csv — 含評論文字（NLP 分析用）

注意事項：
    - Vivino 可能會限制請求頻率，腳本已內建延遲
    - 建議使用 VPN 或在不同時段分批爬取
    - 此資料僅供學術研究使用

作者：[你的名字]
日期：2025/05
"""

import requests
import pandas as pd
import json
import time
import random
import os
from datetime import datetime

# ============================================================
# 設定區 — 你可以修改這些參數
# ============================================================

# 要爬取的國家代碼和對應名稱
# Vivino 使用 ISO 2字母國碼
COUNTRIES = {
    "fr": "France",
    "es": "Spain",
    "it": "Italy",
    "us": "United States",
}

# Vivino 的 wine_type_id：
# 1 = Red, 2 = White, 3 = Sparkling, 4 = Rosé, 7 = Dessert, 24 = Fortified
ROSE_TYPE_ID = 4

# 每頁筆數（Vivino API 預設 25）
RECORDS_PER_PAGE = 25

# 每個國家最多爬幾頁（25筆/頁，20頁 = 500筆/國家）
MAX_PAGES_PER_COUNTRY = 20

# 價格切片（單位：TWD，因 Vivino 依 IP 回本地幣別）
# Vivino 未登入 API 對單次 query 回 records_matched 有 ~10 筆上限，
# 用價格區間切片可繞過：每個 band 各回最多 10 筆 → 累計可拿到上百筆/國家
# 若你的 IP 不在台灣，請改為對應幣別（USD / EUR）的合理區間
PRICE_BANDS = [
    (0, 300),
    (300, 500),
    (500, 800),
    (800, 1200),
    (1200, 2000),
    (2000, 3500),
    (3500, 6000),
    (6000, 100000),
]

# 請求間隔（秒），避免被封鎖
MIN_DELAY = 1.5
MAX_DELAY = 3.0

# 是否爬取評論（會大幅增加時間，但對 NLP 分析有價值）
SCRAPE_REVIEWS = False
MAX_REVIEWS_PER_WINE = 10

# 輸出資料夾
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data", "vivino")

# ============================================================
# API 設定
# ============================================================

BASE_URL = "https://www.vivino.com/api/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}


def safe_get(url, params=None, max_retries=3):
    """帶重試機制的 GET 請求"""
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited - 等待更久
                wait = 30 * (attempt + 1)
                print(f"  ⚠️  被限速了，等待 {wait} 秒...")
                time.sleep(wait)
            else:
                print(f"  ⚠️  HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
            time.sleep(5)
    return None


def scrape_country_roses(country_code, country_name):
    """爬取指定國家的粉紅酒資料（用價格切片繞過 records_matched ~10 上限）"""

    print(f"\n{'='*50}")
    print(f"🌸 正在爬取: {country_name} ({country_code.upper()})")
    print(f"{'='*50}")

    wines_data = []
    seen_wine_ids = set()  # 跨 band 去重，避免同一支酒被重複收

    base_payload = {
        "country_codes[]": country_code,
        "wine_type_ids[]": ROSE_TYPE_ID,
        "min_rating": 1,
        "order_by": "ratings_count",
        "order": "desc",
    }

    for band_idx, (price_lo, price_hi) in enumerate(PRICE_BANDS, 1):
        payload = {
            **base_payload,
            "price_range_min": price_lo,
            "price_range_max": price_hi,
        }

        result = safe_get(f"{BASE_URL}explore/explore", params=payload)
        if not result:
            print(f"  ⚠️  band {band_idx}/{len(PRICE_BANDS)} ({price_lo}-{price_hi}): 無回應，跳過")
            continue

        n_matches = result.get('explore_vintage', {}).get('records_matched', 0)
        if n_matches == 0:
            print(f"  ◽ band {band_idx}/{len(PRICE_BANDS)} ({price_lo}-{price_hi}): 0 筆")
            continue

        total_pages = min(MAX_PAGES_PER_COUNTRY, max(1, n_matches // RECORDS_PER_PAGE + 1))
        print(f"  💰 band {band_idx}/{len(PRICE_BANDS)} ({price_lo}-{price_hi}): {n_matches} 筆 / {total_pages} 頁")

        added_in_band = 0
        for page in range(1, total_pages + 1):
            payload['page'] = page
            print(f"     📄 頁 {page}/{total_pages}...", end="", flush=True)

            result = safe_get(f"{BASE_URL}explore/explore", params=payload)
            if not result:
                print(" 跳過")
                continue

            matches = result.get('explore_vintage', {}).get('matches', [])
            if not matches:
                print(" 無資料，停止")
                break

            page_added = 0
            for match in matches:
                try:
                    vintage = match.get('vintage') or {}
                    wine = vintage.get('wine') or {}
                    price = match.get('price') or {}
                    winery = wine.get('winery') or {}
                    region = wine.get('region') or {}
                    stats = wine.get('statistics') or vintage.get('statistics') or {}
                    currency = price.get('currency') or {}

                    wine_id = wine.get('id')
                    if wine_id is not None and wine_id in seen_wine_ids:
                        continue  # 跨 band 已收過，跳過

                    wine_info = {
                        'wine_id': wine_id,
                        'wine_name': wine.get('name'),
                        'winery_name': winery.get('name'),
                        'country': country_name,
                        'country_code': country_code,
                        'region': region.get('name'),
                        'vintage_year': vintage.get('year'),
                        'wine_type': 'Rosé',
                        'rating_average': stats.get('ratings_average') or stats.get('wine_ratings_average'),
                        'rating_count': stats.get('ratings_count') or stats.get('wine_ratings_count'),
                        'price_amount': price.get('amount'),
                        'price_currency': currency.get('code'),
                        'acidity': wine.get('acidity'),
                        'intensity': wine.get('intensity'),
                        'sweetness': wine.get('sweetness'),
                        'tannin': wine.get('tannin'),
                    }

                    style = wine.get('style')
                    if style:
                        wine_info['style_name'] = style.get('name')
                        wine_info['style_body'] = style.get('body')
                        wine_info['style_body_description'] = style.get('body_description')
                        wine_info['style_acidity'] = style.get('acidity')
                        wine_info['style_acidity_description'] = style.get('acidity_description')

                        grapes = style.get('grapes') or []
                        if grapes:
                            wine_info['grape_names'] = ', '.join([g.get('name', '') for g in grapes])

                        food = style.get('food') or []
                        if food:
                            wine_info['food_pairing'] = ', '.join([f.get('name', '') for f in food])

                    if SCRAPE_REVIEWS and wine_id:
                        reviews = scrape_wine_reviews(wine_id)
                        wine_info['review_texts'] = ' ||| '.join(reviews)
                        wine_info['review_count_scraped'] = len(reviews)

                    wines_data.append(wine_info)
                    if wine_id is not None:
                        seen_wine_ids.add(wine_id)
                    page_added += 1
                    added_in_band += 1

                except Exception as e:
                    print(f"\n  ⚠️  解析錯誤: {e}")
                    continue

            print(f" ✓ {page_added}/{len(matches)} 新增")

        print(f"     → band 新增 {added_in_band} 筆 (累計 {len(wines_data)})")

    print(f"  ✅ {country_name} 完成: {len(wines_data)} 筆")
    return wines_data


def scrape_wine_reviews(wine_id):
    """爬取指定酒款的評論文字"""
    reviews_text = []
    
    result = safe_get(f"{BASE_URL}wines/{wine_id}/reviews", 
                      params={"per_page": MAX_REVIEWS_PER_WINE})
    if not result:
        return reviews_text
    
    for review in result.get('reviews', []):
        note = review.get('note')
        if note and len(note.strip()) > 10:  # 只保留有實質內容的評論
            reviews_text.append(note.strip())
    
    return reviews_text


def main():
    """主程式"""
    
    print("🍷 Vivino Rosé Wine Scraper")
    print(f"📅 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 目標國家: {len(COUNTRIES)} 個")
    print(f"📝 每國最多: {MAX_PAGES_PER_COUNTRY * RECORDS_PER_PAGE} 筆")
    print(f"💬 爬取評論: {'是' if SCRAPE_REVIEWS else '否'}")
    
    # 建立輸出資料夾
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_wines = []
    
    for country_code, country_name in COUNTRIES.items():
        wines = scrape_country_roses(country_code, country_name)
        all_wines.extend(wines)
        
        # 每爬完一個國家就存一次（避免中途斷掉全部遺失）
        if wines:
            temp_df = pd.DataFrame(all_wines)
            temp_df.to_csv(f"{OUTPUT_DIR}/vivino_rose_checkpoint.csv", index=False)
            print(f"  💾 已儲存 checkpoint ({len(all_wines)} 筆累計)")
    
    # ============================================================
    # 儲存最終結果
    # ============================================================
    
    df = pd.DataFrame(all_wines)
    
    if len(df) == 0:
        print("\n❌ 沒有爬到任何資料，請檢查網路連線或 Vivino API 是否可用")
        return
    
    # 基本清洗
    df['rating_average'] = pd.to_numeric(df['rating_average'], errors='coerce')
    df['price_amount'] = pd.to_numeric(df['price_amount'], errors='coerce')
    df['rating_count'] = pd.to_numeric(df['rating_count'], errors='coerce')
    
    # 儲存完整資料
    output_path = f"{OUTPUT_DIR}/vivino_rose_raw.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ 完整資料: {output_path} ({len(df)} 筆)")
    
    # 儲存不含評論的精簡版（較小檔案）
    cols_no_review = [c for c in df.columns if 'review' not in c]
    df[cols_no_review].to_csv(f"{OUTPUT_DIR}/vivino_rose_compact.csv", 
                              index=False, encoding='utf-8-sig')
    print(f"✅ 精簡版: {OUTPUT_DIR}/vivino_rose_compact.csv")
    
    # 印出摘要統計
    print(f"\n{'='*50}")
    print(f"📊 爬取結果摘要")
    print(f"{'='*50}")
    print(f"總筆數: {len(df)}")
    print(f"\n各國筆數:")
    print(df['country'].value_counts().to_string())
    print(f"\n評分統計:")
    print(df['rating_average'].describe().to_string())
    print(f"\n價格統計 (有價格的筆數: {df['price_amount'].notna().sum()}):")
    print(df['price_amount'].describe().to_string())
    
    print(f"\n📅 結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 完成！")


if __name__ == '__main__':
    main()
"""
============================================================
進階用法：只爬特定產區（如 Provence）
============================================================

如果你只想爬 Provence 的粉紅酒，修改 payload 加入 region_ids：

# Provence 在 Vivino 的 region_id 需要先查詢：
# 方法1: 在 Vivino 網站搜尋 Provence rosé，觀察 URL 中的 region_id
# 方法2: 用以下代碼查詢

import requests
res = requests.get(
    "https://www.vivino.com/api/explore/explore",
    headers=HEADERS,
    params={
        "country_codes[]": "fr",
        "wine_type_ids[]": 4,
        "page": 1,
    }
)
# 從結果中找 region.id 欄位

# 常見的法國粉紅酒產區 region_id（可能需要更新）：
# Provence: 多個子產區，包括 Côtes de Provence, Coteaux d'Aix-en-Provence 等
# 你可以在 payload 中加入：
# payload["region_ids[]"] = [具體的 region_id]

============================================================
進階用法：價格範圍篩選
============================================================

# 只爬 $10-$20 的粉紅酒（對應你 YouTube 影片的 under $20 主題）
payload["price_range_min"] = 10
payload["price_range_max"] = 20

============================================================
如何在報告中引用這份資料
============================================================

建議引用格式：
    "Wine data was scraped from Vivino (www.vivino.com) using a 
    custom Python script adapted from the viviner open-source 
    scraper (https://github.com/gugarosa/viviner). Data collection 
    was performed on [日期], covering [X] rosé wines across [Y] 
    countries. The dataset includes wine ratings, prices, grape 
    varieties, and consumer reviews."

============================================================
"""
