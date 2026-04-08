#!/usr/bin/env python3
"""
monthly_search.py
─────────────────
GitHub Actions 每月自動執行此腳本：
1. 讀取 tracked.md 取得已收錄清單
2. 呼叫 Claude API 搜尋新競賽
3. 解析回傳的 JSON，過濾重複
4. 更新 competitions.json 與 tracked.md
5. 執行 sync.py 同步進 index.html

執行方式：
    python3 monthly_search.py

環境變數需求：
    ANTHROPIC_API_KEY  ← 從 GitHub Secrets 注入
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent
JSON_FILE   = BASE / "competitions.json"
TRACKED_FILE = BASE / "tracked.md"
SYNC_SCRIPT = BASE / "sync.py"

TODAY       = datetime.now().strftime("%Y-%m")
SEARCH_YEAR = datetime.now().year


# ── 讀取已收錄清單 ────────────────────────────────────────────────────────────
def get_tracked_names() -> list[str]:
    """從 tracked.md 取得所有已收錄的競賽名稱（用於去重）"""
    if not TRACKED_FILE.exists():
        return []
    content = TRACKED_FILE.read_text(encoding="utf-8")
    # 擷取表格中的競賽名稱（第二欄）
    names = re.findall(r"\|\s*\d+\s*\|\s*(.+?)\s*\|", content)
    return [n.strip() for n in names if n.strip() and n.strip() != "競賽名稱"]


def get_next_ids() -> tuple[int, int]:
    """從 tracked.md 取得下一個可用的國內/國際 ID"""
    if not TRACKED_FILE.exists():
        return 110, 211
    content = TRACKED_FILE.read_text(encoding="utf-8")
    domestic_match = re.search(r"國內新競賽：從\s*\*\*(\d+)\*\*\s*開始", content)
    intl_match     = re.search(r"國際新競賽：從\s*\*\*(\d+)\*\*\s*開始", content)
    domestic_id = int(domestic_match.group(1)) if domestic_match else 110
    intl_id     = int(intl_match.group(1))     if intl_match     else 211
    return domestic_id, intl_id


# ── 呼叫 Claude API ───────────────────────────────────────────────────────────
def search_competitions(tracked_names: list[str],
                        next_domestic: int,
                        next_intl: int) -> list[dict]:
    """呼叫 Claude API 搜尋新競賽，回傳 list of dict"""

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ 找不到 ANTHROPIC_API_KEY，請確認 GitHub Secrets 設定。")
        sys.exit(1)

    try:
        import anthropic
    except ImportError:
        print("❌ 找不到 anthropic 套件，請執行：pip install anthropic")
        sys.exit(1)

    tracked_list = "\n".join(f"- {n}" for n in tracked_names) or "（目前無已收錄競賽）"

    prompt = f"""你是一位台灣教育資源研究員，專門整理適合國中（7–9年級）和高中學生參加的競賽。

今天是 {datetime.now().strftime("%Y年%m月")}。

## 已收錄競賽（請排除這些，不要重複回傳）
{tracked_list}

## 你的任務
搜尋 {SEARCH_YEAR} 年下半年到 {SEARCH_YEAR + 1} 年，適合台灣國中、高中學生參加的「新競賽」。

涵蓋領域：科技、AI工具應用、數學、語文/文學、視覺藝術、科學研究、STEM、跨域創新、社會議題、教育科技。

## 輸出規則
- 只回傳 JSON 陣列，不要任何說明文字、不要 markdown 代碼區塊
- 排除已收錄清單中的所有競賽
- 每筆必須有明確的官方網址（不可捏造）
- 國內競賽 ID 從 {next_domestic} 開始，國際競賽 ID 從 {next_intl} 開始
- 目標：找 5–10 筆真實存在的新競賽

## JSON 格式（嚴格遵守）
[
  {{
    "id": {next_domestic},
    "name": "競賽完整名稱",
    "scope": "國內",
    "domains": ["AI工具應用"],
    "level": ["國中", "高中"],
    "organizer": "主辦單位",
    "description": "競賽說明（50–150字）",
    "schedule": "時程說明",
    "deadline": "報名截止日期",
    "url": "https://官方網站（必須真實存在）",
    "tags": ["標籤1", "標籤2"],
    "highlight": false,
    "status": "即將開放",
    "updated": "{TODAY}"
  }}
]

scope 只能填：「國內」/「國內（接軌國際）」/「國際」
domains 只能從以下選：AI工具應用/數學/語文/文學/視覺藝術/科學研究/STEM/跨域創新/社會議題/教育科技/科技
level 只能填：「國中」/「高中」
status 只能填：「報名中」/「開放中」/「即將開放」/「已截止」

只輸出 JSON 陣列，從 [ 開始，到 ] 結束。"""

    print("🔍 正在呼叫 Claude API 搜尋新競賽...")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }],
        messages=[{"role": "user", "content": prompt}]
    )

    # 取出純文字回應
    raw = ""
    for block in message.content:
        if block.type == "text":
            raw += block.text

    print(f"   API 回應長度：{len(raw)} 字元")

    # 解析 JSON
    # 嘗試直接解析
    try:
        data = json.loads(raw.strip())
        return data
    except json.JSONDecodeError:
        pass

    # 嘗試從回應中擷取 JSON 陣列
    match = re.search(r"\[[\s\S]*\]", raw)
    if match:
        try:
            data = json.loads(match.group())
            return data
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失敗：{e}")
            print(f"   原始內容（前 500 字）：{raw[:500]}")
            return []

    print("❌ 無法從回應中找到 JSON 陣列")
    return []


# ── 去重過濾 ──────────────────────────────────────────────────────────────────
def deduplicate(new_items: list[dict], tracked_names: list[str]) -> list[dict]:
    """過濾掉已收錄的競賽"""
    filtered = []
    for item in new_items:
        name = item.get("name", "").strip()
        # 完全比對 + 部分比對（防止標題略有不同）
        is_dup = any(
            name == t or
            name in t or
            t in name
            for t in tracked_names
        )
        if is_dup:
            print(f"   ⏭️  跳過重複：{name}")
        else:
            filtered.append(item)
    return filtered


# ── 更新 competitions.json ────────────────────────────────────────────────────
def update_competitions_json(new_items: list[dict]) -> None:
    with open(JSON_FILE, encoding="utf-8") as f:
        existing = json.load(f)

    merged = existing + new_items

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"   ✅ competitions.json 更新完成（新增 {len(new_items)} 筆，共 {len(merged)} 筆）")


# ── 更新 tracked.md ───────────────────────────────────────────────────────────
def update_tracked_md(new_items: list[dict],
                      next_domestic: int,
                      next_intl: int) -> None:
    content = TRACKED_FILE.read_text(encoding="utf-8")

    domestic_new = [i for i in new_items if i.get("scope") != "國際"]
    intl_new     = [i for i in new_items if i.get("scope") == "國際"]

    # 計算下一個 ID
    new_next_domestic = next_domestic + len(domestic_new)
    new_next_intl     = next_intl     + len(intl_new)

    # 在國內表格末尾加新行
    for item in domestic_new:
        row = f"| {item['id']} | {item['name']} | {item['url']} |"
        # 找國內表格的結尾（在「## 國際競賽」之前）
        content = content.replace(
            "\n## 國際競賽",
            f"\n{row}\n\n## 國際競賽"
        )

    # 在國際表格末尾加新行
    for item in intl_new:
        row = f"| {item['id']} | {item['name']} | {item['url']} |"
        content = content.replace(
            "\n---\n\n## 下一個可用 ID",
            f"\n{row}\n\n---\n\n## 下一個可用 ID"
        )

    # 更新下一個可用 ID
    content = re.sub(
        r"國內新競賽：從 \*\*\d+\*\* 開始",
        f"國內新競賽：從 **{new_next_domestic}** 開始",
        content
    )
    content = re.sub(
        r"國際新競賽：從 \*\*\d+\*\* 開始",
        f"國際新競賽：從 **{new_next_intl}** 開始",
        content
    )

    # 在搜尋紀錄加一行
    search_row = f"| {TODAY} | {SEARCH_YEAR} 下半年–{SEARCH_YEAR+1} 跨領域競賽 | {len(new_items)} 筆 |"
    content = content.rstrip() + f"\n{search_row}\n"

    TRACKED_FILE.write_text(content, encoding="utf-8")
    print(f"   ✅ tracked.md 更新完成")


# ── 執行 sync.py ──────────────────────────────────────────────────────────────
def run_sync() -> None:
    result = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT)],
        capture_output=True, text=True, cwd=BASE
    )
    if result.returncode == 0:
        print("   ✅ sync.py 執行成功")
    else:
        print(f"   ❌ sync.py 執行失敗：{result.stderr}")
        sys.exit(1)


# ── 產生 PR 說明 ──────────────────────────────────────────────────────────────
def generate_pr_body(new_items: list[dict]) -> str:
    if not new_items:
        return "本月搜尋未發現新競賽。"

    lines = [
        f"## 🔍 {TODAY} 每月自動更新",
        f"",
        f"本次新增 **{len(new_items)}** 筆競賽，請確認內容後按 Merge。",
        f"",
        f"### 新增競賽清單",
        f"",
    ]
    for item in new_items:
        scope_icon = "🇹🇼" if item.get("scope") == "國內" else "🌍"
        lines.append(f"- {scope_icon} **{item['name']}**")
        lines.append(f"  - 主辦：{item.get('organizer', '—')}")
        lines.append(f"  - 截止：{item.get('deadline', '—')}")
        lines.append(f"  - 網址：{item.get('url', '—')}")
        lines.append("")

    lines += [
        "---",
        "> ⚠️ 請檢查每筆資料的官方網址是否正確後再 Merge。",
        "> 如有錯誤，可直接在這個 PR 上修改 `competitions.json`。",
    ]
    return "\n".join(lines)


# ── 主程式 ────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*50}")
    print(f"  台灣 K12 競賽資料庫 — 每月自動更新")
    print(f"  執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # 1. 讀取已收錄清單
    tracked_names = get_tracked_names()
    next_domestic, next_intl = get_next_ids()
    print(f"📋 已收錄競賽：{len(tracked_names)} 筆")
    print(f"📋 下一個可用 ID — 國內：{next_domestic}，國際：{next_intl}\n")

    # 2. 搜尋新競賽
    raw_items = search_competitions(tracked_names, next_domestic, next_intl)
    print(f"\n🔍 API 回傳：{len(raw_items)} 筆")

    if not raw_items:
        print("⚠️  本月未找到新競賽，結束執行。")
        # 寫入空結果供 GitHub Actions 判斷
        Path("pr_body.txt").write_text("本月搜尋未發現新競賽。", encoding="utf-8")
        Path("new_count.txt").write_text("0", encoding="utf-8")
        return

    # 3. 去重過濾
    new_items = deduplicate(raw_items, tracked_names)
    print(f"✅ 過濾後剩餘：{len(new_items)} 筆新競賽\n")

    if not new_items:
        print("⚠️  所有搜尋結果均已收錄，無需更新。")
        Path("pr_body.txt").write_text("本月搜尋結果均已收錄，無需更新。", encoding="utf-8")
        Path("new_count.txt").write_text("0", encoding="utf-8")
        return

    # 4. 更新檔案
    print("📝 更新檔案中...")
    update_competitions_json(new_items)
    update_tracked_md(new_items, next_domestic, next_intl)
    run_sync()

    # 5. 產生 PR 說明
    pr_body = generate_pr_body(new_items)
    Path("pr_body.txt").write_text(pr_body, encoding="utf-8")
    Path("new_count.txt").write_text(str(len(new_items)), encoding="utf-8")

    print(f"\n🎉 完成！新增 {len(new_items)} 筆競賽")
    print("   GitHub Actions 將自動建立 Pull Request 供你審核。\n")


if __name__ == "__main__":
    main()
