#!/usr/bin/env python3
"""
sync.py — 將 competitions.json 同步進 index.html

使用方式：
    python3 sync.py

效果：讀取 competitions.json 的最新內容，
      自動更新 index.html 裡的 EMBEDDED_DATA，
      讓網站不需要 fetch() 就能讀到資料。

更新競賽的完整流程：
    1. 修改 competitions.json
    2. python3 sync.py
    3. git add competitions.json index.html
    4. git commit -m "更新：新增 XXX 競賽"
    5. git push
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
JSON_FILE = BASE / "competitions.json"
HTML_FILE = BASE / "index.html"


def main():
    # ── 讀取 JSON ──────────────────────────────────────────────────────────
    print(f"📖 讀取 {JSON_FILE.name} ...")
    try:
        with open(JSON_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到 {JSON_FILE}，請確認檔案存在。")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ competitions.json 格式有誤：{e}")
        print("   請用 https://jsonlint.com 檢查 JSON 格式。")
        sys.exit(1)

    print(f"   ✅ 成功讀取 {len(data)} 筆競賽資料")

    # 基本欄位驗證
    required = {"id", "name", "scope", "domains", "level",
                "organizer", "description", "schedule", "deadline",
                "url", "highlight", "status", "updated"}
    errors = []
    for i, item in enumerate(data):
        missing = required - set(item.keys())
        if missing:
            errors.append(f"   第 {i+1} 筆（id={item.get('id','?')}）缺少欄位：{missing}")
    if errors:
        print("⚠️  發現欄位缺漏（仍會繼續同步，請確認是否正確）：")
        for e in errors:
            print(e)

    # ── 讀取 HTML ──────────────────────────────────────────────────────────
    print(f"\n📖 讀取 {HTML_FILE.name} ...")
    try:
        with open(HTML_FILE, encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print(f"❌ 找不到 {HTML_FILE}，請確認檔案存在。")
        sys.exit(1)

    # ── 替換 EMBEDDED_DATA ─────────────────────────────────────────────────
    compact_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    pattern = r"(const EMBEDDED_DATA = )(\[[\s\S]*?\]);"
    replacement = f"\\g<1>{compact_json};"

    new_html, count = re.subn(pattern, replacement, html)

    if count == 0:
        print("❌ 在 index.html 中找不到 EMBEDDED_DATA，請確認 index.html 格式正確。")
        sys.exit(1)

    # ── 寫回 HTML ──────────────────────────────────────────────────────────
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"   ✅ 已更新 index.html 的 EMBEDDED_DATA")
    print(f"\n🎉 同步完成！共 {len(data)} 筆競賽")
    print("\n下一步：")
    print("   git add competitions.json index.html")
    print('   git commit -m "更新：XXX"')
    print("   git push")
    print("\n推送後約 1 分鐘，GitHub Pages 即自動重新部署。")


if __name__ == "__main__":
    main()
