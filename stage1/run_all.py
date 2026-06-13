"""
Stage 1 一鍵執行：依序產出 Ch.1-Ch.5 全部圖表與表格

執行方式：
    python -m stage1.run_all
"""

import time
from stage1 import (
    ch1_global_trade,
    ch2_rose_positioning,
    ch3_french_supply_demand,
    ch4_premium_strategy,
    ch5_conclusion,
)


def main():
    print('=' * 60)
    print('🍷 Stage 1 — Provence Rosé Premiumization 策略分析')
    print('=' * 60)

    timings = []
    chapters = [
        ('Ch.1 全球貿易與 Premiumization', ch1_global_trade.run),
        ('Ch.2 Rosé 與 Provence 定位', ch2_rose_positioning.run),
        ('Ch.3 法國產區供需', ch3_french_supply_demand.run),
        ('Ch.4 策略整合', ch4_premium_strategy.run),
        ('Ch.5 結論彙整', ch5_conclusion.run),
    ]

    total_start = time.time()
    for name, fn in chapters:
        print()
        t0 = time.time()
        fn()
        elapsed = time.time() - t0
        timings.append((name, elapsed))

    total_elapsed = time.time() - total_start

    print()
    print('=' * 60)
    print('⏱️  時間統計')
    print('=' * 60)
    for name, t in timings:
        print(f'  {name:30s} {t:6.2f} 秒')
    print(f'  {"總計":30s} {total_elapsed:6.2f} 秒')
    print()
    print('🎉 Stage 1 全部完成！')
    print('   📂 圖表 → figures/')
    print('   📂 表格 → tables/')


if __name__ == '__main__':
    main()
