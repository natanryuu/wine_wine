"""
🧪 快速測試腳本 — 先跑這個確認 Vivino API 可用
================================================
只爬法國粉紅酒第一頁（25筆），大約1分鐘完成

使用方式：
    pip install requests pandas
    python vivino_test.py
"""

import os
import requests
import pandas as pd
import json

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data", "vivino")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = "https://www.vivino.com/api/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}

print("🧪 測試 Vivino API 連線...")

# 測試1: 基本連線
try:
    res = requests.get(
        f"{BASE_URL}explore/explore",
        headers=HEADERS,
        params={
            "country_codes[]": "fr",
            "wine_type_ids[]": 4,  # Rosé
            "min_rating": 1,
            "order_by": "ratings_count",
            "order": "desc",
            "page": 1,
        },
        timeout=10
    )
    print(f"✅ HTTP 狀態碼: {res.status_code}")
except Exception as e:
    print(f"❌ 連線失敗: {e}")
    print("請確認：")
    print("  1. 你的網路連線正常")
    print("  2. 沒有被防火牆擋住")
    print("  3. 試試看用 VPN")
    exit(1)

if res.status_code != 200:
    print(f"❌ API 回傳錯誤，狀態碼: {res.status_code}")
    print(f"回應內容: {res.text[:500]}")
    exit(1)

# 測試2: 解析資料
data = res.json()
matches = data.get('explore_vintage', {}).get('matches', [])
n_total = data.get('explore_vintage', {}).get('records_matched', 0)

print(f"✅ 法國粉紅酒總數: {n_total}")
print(f"✅ 本頁回傳: {len(matches)} 筆")

# 測試3: 提取欄位
wines = []
for m in matches:
    vintage = m.get('vintage', {})
    wine = vintage.get('wine', {})
    price = m.get('price', {})
    
    winery = wine.get('winery') or {}
    region = wine.get('region') or {}
    stats = wine.get('statistics') or vintage.get('statistics') or {}
    currency = (price or {}).get('currency') or {}

    wines.append({
        'name': wine.get('name'),
        'winery': winery.get('name'),
        'region': region.get('name'),
        'rating': stats.get('ratings_average') or stats.get('wine_ratings_average'),
        'reviews': stats.get('ratings_count') or stats.get('wine_ratings_count'),
        'price': (price or {}).get('amount'),
        'currency': currency.get('code'),
    })

df = pd.DataFrame(wines)
print(f"\n📊 測試結果預覽（前10筆）:")
print(df.head(10).to_string(index=False))

# 儲存測試結果
test_csv = os.path.join(OUTPUT_DIR, 'vivino_test_result.csv')
df.to_csv(test_csv, index=False, encoding='utf-8-sig')
print(f"\n✅ 測試資料已存為 {test_csv}")
print(f"\n🎉 一切正常！你可以放心執行 vivino_rose_scraper.py 了")

# 額外：印出原始 JSON 結構（方便你了解有哪些欄位可用）
print(f"\n{'='*50}")
print("📋 Vivino API 回傳的完整欄位結構（第一筆）:")
print(f"{'='*50}")
if matches:
    first = matches[0]
    print(json.dumps(first, indent=2, ensure_ascii=False)[:3000])
    print("... (截斷)")
