#!/usr/bin/env python3
"""Watchdog: check if wechat-oa cron jobs produced expected output files.

Run at noon and 6pm. If the expected JSON file doesn't exist, alert.

Usage:
    python3 scripts/cron_watchdog.py

Silent on success (exit 0, no output). Prints alert on failure (exit 1).
"""
import os
import sys
from datetime import datetime

BASE = os.path.expanduser("~/projects/wechat_publisher")
now = datetime.now()
today = now.strftime("%Y-%m-%d")
weekday = now.weekday()  # 0=Monday, 6=Sunday

alerts = []

# AI briefing: runs daily at 10am, check after noon
expected_ai = os.path.join(BASE, f"ai_frontier_v1_{today}.json")
if not os.path.exists(expected_ai):
    # Also check for older naming patterns
    import glob
    ai_files = glob.glob(os.path.join(BASE, f"ai_frontier*{today}*.json"))
    if not ai_files:
        alerts.append(f"AI前沿简报: 今天({today})未找到产出文件，10am的cron可能失败了")

# US stock review: runs weekday 9am, check after noon (skip weekends)
if weekday < 5:  # Monday-Friday
    expected_us = os.path.join(BASE, f"us_stock_review_{today}.json")
    if not os.path.exists(expected_us):
        import glob
        us_files = glob.glob(os.path.join(BASE, f"us_stock*{today}*.json"))
        if not us_files:
            alerts.append(f"美股复盘: 今天({today})未找到产出文件，9am的cron可能失败了")

if alerts:
    print("⚠️ 公众号 cron 监控告警:")
    for a in alerts:
        print(f"  {a}")
    sys.exit(1)
else:
    # Silent on success
    sys.exit(0)
