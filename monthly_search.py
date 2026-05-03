#!/usr/bin/env python3
"""
monthly_search.py
─────────────────
GitHub Actions 每月自動執行此腳本，做兩件事：

  ① 移除過期競賽（截止日超過 EXPIRE_AFTER_DAYS 的「已截止」競賽）
  ② 搜尋新競賽（呼叫 Claude API，過濾重複，更新所有檔案）

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
from datetime import datetime, timedelta
from pathlib import Path


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  ⚙️  CONFIG — 所有可調整的設定都在這裡，不需要動其他地方               ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║                                                                          ║
# ║  修改後執行 python3 monthly_search.py 即可套用新設定                    ║
# ║                                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── 移除設定 ──────────────────────────────────────────────────────────────────

# 「已截止」的競賽，截止後幾天才從網站上移除
# 90 天 = 約 3 個月（讓老師還有時間參考剛截止的競賽）
# 設成 0 = 截止後立即移除
# 設成 30 = 截止後 1 個月移除
EXPIRE_AFTER_DAYS = 90

# ── 搜尋設定 ──────────────────────────────────────────────────────────────────

# 每次搜尋目標新競賽筆數
SEARCH_TARGET_COUNT = 10

# 搜尋涵蓋的領域（告訴 Claude 要找哪類競賽）
SEARCH_DOMAINS = [
    "科技",
    "AI工具應用",
    "數學",
    "語文/文學",
    "視覺藝術",
    "科學研究",
    "STEM",
    "跨域創新",
    "社會議題",
    "教育科技",
]

# 搜尋對象的學段
SEARCH_LEVELS = ["國中（7–9年級）", "高中"]

# ── Claude API 設定 ────────────────────────────────────────────────────────────

# 使用的 Claude 模型
CLAUDE_MODEL = "claude-sonnet-4-6"

# API 回應最大 token 數（影響搜尋結果的詳細程度，建議 3000–6000）
CLAUDE_MAX_TOKENS = 4000

# ── GitHub 設定 ────────────────────────────────────────────────────────────────

# Pull Request 自動加上的標籤
PR_LABELS = ["auto-update", "needs-review"]

# 無變更時建立的 Issue 標籤
NO_UPDATE_LABEL = "monthly-report"

# ══════════════════════════════════════════════════════════════════════════════
#  以下為程式本體，通常不需要修改
# ══════════════════════════════════════════════════════════════════════════════

BASE          = Path(__file__).parent
JSON_FILE     = BASE / "competitions.json"
TRACKED_FILE  = BASE / "tracked.md"
SYNC_SCRIPT   = BASE / "sync.py"

TODAY         = datetime.now().strftime("%Y-%m")
TODAY_DT      = datetime.now()
SEARCH_YEAR   = datetime.now().year
EXPIRE_CUTOFF = TODAY_DT - timedelta(days=EXPIRE_AFTER_DAYS)


# ─────────────────────────────────────────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────────────────────────────────────────

def load_competitions() -> list[dict]:
    with open(JSON_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_competitions(data: list[dict]) -> None:
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


def parse_deadline(deadline_str: str) -> datetime | None:
    """
    從 deadline 字串解析日期。
    支援：2026/5/10、2026-05-10、含備註的字串（取第一組日期）
    無法解析時回傳 None → 該競賽會被保留，不自動移除
    """
    if not deadline_str:
        return None
    m = re.search(r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})", deadline_str)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# ① 移除過期競賽
# ─────────────────────────────────────────────────────────────────────────────

def remove_expired(competitions: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    掃描所有 status = '已截止' 的競賽。
    截止日超過 EXPIRE_AFTER_DAYS 天 → 移除。
    回傳 (保留清單, 移除清單)
    """
    kept, removed = [], []

    for comp in competitions:
        # 只處理「已截止」，其他狀態一律保留
        if comp.get("status") != "已截止":
            kept.append(comp)
            continue

        deadline_dt = parse_deadline(comp.get("deadline", ""))

        if deadline_dt is None:
            # 日期無法解析 → 保留，避免誤刪
            print(f"   ⚠️  日期無法解析，保留：{comp['name']}")
            kept.append(comp)
        elif deadline_dt < EXPIRE_CUTOFF:
            days_ago = (TODAY_DT - deadline_dt).days
            print(f"   🗑️  移除（截止 {days_ago} 天前）：{comp['name']}")
            removed.append(comp)
        else:
            # 在緩衝期內 → 保留
            remaining = (deadline_dt + timedelta(days=EXPIRE_AFTER_DAYS) - TODAY_DT).days
            print(f"   ⏳ 緩衝期內，保留（還有 {remaining} 天到期）：{comp['name']}")
            kept.append(comp)

    return kept, removed


def mark_removed_in_tracked(removed_items: list[dict]) -> None:
    """在 tracked.md 中對已移除競賽加上刪除線標記"""
    if not removed_items or not TRACKED_FILE.exists():
        return

    content       = TRACKED_FILE.read_text(encoding="utf-8")
    removed_names = {item["name"] for item in removed_items}

    lines     = content.split("\n")
    new_lines = []
    for line in lines:
        if re.match(r"\|\s*\d+\s*\|", line):
            parts = line.split("|")
            if len(parts) >= 3:
                name_cell = parts[2].strip()
                # 排除已有刪除線的行
                if name_cell in removed_names and "~~" not in name_cell:
                    line = line.replace(
                        f"| {name_cell} |",
                        f"| ~~{name_cell}~~ *(移除於 {TODAY})* |"
                    )
        new_lines.append(line)

    TRACKED_FILE.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"   ✅ tracked.md 已標記 {len(removed_items)} 筆移除記錄")


# ─────────────────────────────────────────────────────────────────────────────
# ② 搜尋新競賽
# ─────────────────────────────────────────────────────────────────────────────

def get_tracked_names() -> list[str]:
    """從 tracked.md 取得所有已收錄的競賽名稱（含已移除的，都排除以防重新加入）"""
    if not TRACKED_FILE.exists():
        return []
    content = TRACKED_FILE.read_text(encoding="utf-8")
    names   = re.findall(r"\|\s*\d+\s*\|\s*(.+?)\s*\|", content)
    cleaned = []
    for n in names:
        n = n.strip()
        if not n or n == "競賽名稱":
            continue
        # 去掉刪除線 markdown（~~名稱~~）
        n = re.sub(r"~~(.+?)~~.*", r"\1", n).strip()
        if n:
            cleaned.append(n)
    return cleaned


def get_next_ids() -> tuple[int, int]:
    """從 tracked.md 取得下一個可用的國內/國際 ID"""
    if not TRACKED_FILE.exists():
        return 110, 211
    content = TRACKED_FILE.read_text(encoding="utf-8")
    d = re.search(r"國內新競賽：從\s*\*\*(\d+)\*\*\s*開始", content)
    i = re.search(r"國際新競賽：從\s*\*\*(\d+)\*\*\s*開始", content)
    return int(d.group(1)) if d else 110, int(i.group(1)) if i else 211


def search_competitions(tracked_names: list[str],
                        next_domestic: int,
                        next_intl: int) -> list[dict]:
    """呼叫 Claude API 搜尋新競賽，含自動重試機制（Rate Limit 保護）"""

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ 找不到 ANTHROPIC_API_KEY，請確認 GitHub Secrets 設定。")
        sys.exit(1)

    try:
        import anthropic
        import time as time_module
    except ImportError:
        print("❌ 找不到 anthropic 套件，請執行：pip install anthropic")
        sys.exit(1)

    domains_str = "、".join(SEARCH_DOMAINS)
    levels_str  = "、".join(SEARCH_LEVELS)

    # ── 縮短 tracked_list，避免超過 Rate Limit ────────────────────────────
    # 只取每個名稱前 15 字，用逗號分隔，大幅降低 prompt token 數
    short_names  = [n[:15] for n in tracked_names]
    tracked_list = "、".join(short_names) if short_names else "無"

    # ── 精簡版 prompt（token 數比原版少 60%）─────────────────────────────
    prompt = (
        f"搜尋 {SEARCH_YEAR} 年下半年至 {SEARCH_YEAR+1} 年，"
        f"適合台灣國中高中（13–18歲）的新競賽。\n"
        f"領域：{domains_str}\n"
        f"排除已收錄（勿重複）：{tracked_list}\n\n"
        f"找 {SEARCH_TARGET_COUNT} 筆，只回傳 JSON 陣列，格式如下：\n"
        f'''[{{"id":{next_domestic},"name":"名稱","scope":"國內","domains":["AI工具應用"],'''
        f'''"level":["國中","高中"],"organizer":"主辦","description":"說明50-100字",'''
        f'''"schedule":"時程","deadline":"YYYY/MM/DD","url":"https://官方網址",'''
        f'''"tags":["標籤"],"highlight":false,"status":"即將開放","updated":"{TODAY}"}}]\n'''
        f"scope: 國內/國內（接軌國際）/國際  "
        f"status: 報名中/開放中/即將開放/已截止\n"
        f"國內ID從{next_domestic}，國際ID從{next_intl}\n"
        f"只輸出JSON陣列，從[開始到]結束。"
    )

    print(f"   模型：{CLAUDE_MODEL} | 搜尋目標：{SEARCH_TARGET_COUNT} 筆")
    print(f"   Prompt 長度：約 {len(prompt)} 字元")

    client = anthropic.Anthropic(api_key=api_key)

    # ── 先等 65 秒，讓 token bucket 重置，避免 Rate Limit ─────────────────
    # Tier 1 限制：30,000 tokens/分鐘。等待後再送出，確保 bucket 是滿的。
    print("   ⏳ 等待 65 秒讓 API rate limit 重置...")
    time_module.sleep(65)

    # ── 自動重試（遇到 Rate Limit 等待後重試）────────────────────────────
    max_retries = 3
    message = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   第 {attempt} 次呼叫 API（不使用 web_search 工具，節省 token）...")
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                # ⚠️ 不加 web_search 工具：工具 schema 本身就佔用大量 token
                # Claude 會用訓練資料回答，適合找「常設型」競賽
                messages=[{"role": "user", "content": prompt}]
            )
            print("   ✅ API 呼叫成功")
            break

        except anthropic.RateLimitError:
            wait_sec = 65 * attempt  # 65s → 130s → 195s
            if attempt == max_retries:
                print("❌ 達到最大重試次數，本月搜尋略過。")
                return []
            print(f"   ⚠️  Rate Limit，等待 {wait_sec} 秒後重試（{attempt}/{max_retries}）...")
            time_module.sleep(wait_sec)

        except Exception as e:
            print(f"❌ API 呼叫失敗：{type(e).__name__}: {e}")
            return []

    if message is None:
        return []

    raw = "".join(block.text for block in message.content if block.type == "text")
    print(f"   API 回應長度：{len(raw)} 字元")

    # 解析 JSON
    for target in [raw.strip(), None]:
        if target is None:
            m = re.search(r'\['+ r'[\s\S]*' + r'\]', raw)
            target = m.group(0) if m else None
        if not target:
            continue
        try:
            return json.loads(target)
        except (json.JSONDecodeError, TypeError):
            pass

    print("❌ 無法解析 API 回應為 JSON")
    print(f"   原始內容（前 500 字）：{raw[:500]}")
    return []



def deduplicate(new_items: list[dict], tracked_names: list[str]) -> list[dict]:
    """過濾掉已收錄的競賽"""
    filtered = []
    for item in new_items:
        name   = item.get("name", "").strip()
        is_dup = any(name == t or name in t or t in name for t in tracked_names)
        if is_dup:
            print(f"   ⏭️  跳過重複：{name}")
        else:
            filtered.append(item)
    return filtered


def add_to_competitions_json(new_items: list[dict]) -> None:
    existing = load_competitions()
    merged   = existing + new_items
    save_competitions(merged)
    print(f"   ✅ competitions.json：新增 {len(new_items)} 筆，共 {len(merged)} 筆")


def add_to_tracked_md(new_items: list[dict],
                      next_domestic: int,
                      next_intl: int) -> None:
    content      = TRACKED_FILE.read_text(encoding="utf-8")
    domestic_new = [i for i in new_items if i.get("scope") != "國際"]
    intl_new     = [i for i in new_items if i.get("scope") == "國際"]

    for item in domestic_new:
        row     = f"| {item['id']} | {item['name']} | {item['url']} |"
        content = content.replace("\n## 國際競賽", f"\n{row}\n\n## 國際競賽", 1)

    for item in intl_new:
        row     = f"| {item['id']} | {item['name']} | {item['url']} |"
        content = content.replace("\n---\n\n## 下一個可用 ID",
                                  f"\n{row}\n\n---\n\n## 下一個可用 ID", 1)

    content = re.sub(r"國內新競賽：從 \*\*\d+\*\* 開始",
                     f"國內新競賽：從 **{next_domestic + len(domestic_new)}** 開始", content)
    content = re.sub(r"國際新競賽：從 \*\*\d+\*\* 開始",
                     f"國際新競賽：從 **{next_intl + len(intl_new)}** 開始", content)

    row     = f"| {TODAY} | {SEARCH_YEAR} 下半年–{SEARCH_YEAR+1} 跨領域 | {len(new_items)} 筆 |"
    content = content.rstrip() + f"\n{row}\n"

    TRACKED_FILE.write_text(content, encoding="utf-8")
    print(f"   ✅ tracked.md 更新完成")


# ─────────────────────────────────────────────────────────────────────────────
# PR 說明產生器
# ─────────────────────────────────────────────────────────────────────────────

def generate_pr_body(removed_items: list[dict], new_items: list[dict]) -> str:
    lines = [f"## 🤖 {TODAY} 每月自動維護", ""]

    if removed_items:
        lines += [
            f"### 🗑️ 移除過期競賽（截止超過 {EXPIRE_AFTER_DAYS} 天，共 {len(removed_items)} 筆）",
            "",
        ]
        for item in removed_items:
            lines.append(f"- ~~{item['name']}~~（截止：{item.get('deadline','—')}）")
        lines.append("")

    if new_items:
        lines += [
            f"### ✨ 新增競賽（{len(new_items)} 筆）",
            "",
        ]
        for item in new_items:
            icon = "🇹🇼" if item.get("scope") == "國內" else "🌍"
            lines += [
                f"- {icon} **{item['name']}**",
                f"  - 主辦：{item.get('organizer','—')}",
                f"  - 截止：{item.get('deadline','—')}",
                f"  - 網址：{item.get('url','—')}",
                "",
            ]

    if not removed_items and not new_items:
        lines.append("本月無任何變更。")

    lines += [
        "---",
        "> ⚠️ 請確認官方網址正確後再按 Merge。",
        "> 如有錯誤，可直接在這個 PR 上修改 `competitions.json`。",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"  台灣 K12 競賽資料庫 — 每月自動維護")
    print(f"  執行時間：{TODAY_DT.strftime('%Y-%m-%d %H:%M')}")
    print(f"  ── 目前設定 ──────────────────────────────")
    print(f"  過期門檻：截止後 {EXPIRE_AFTER_DAYS} 天移除")
    print(f"  搜尋目標：{SEARCH_TARGET_COUNT} 筆新競賽")
    print(f"  Claude 模型：{CLAUDE_MODEL}")
    print(f"{'='*55}\n")

    competitions = load_competitions()
    print(f"📂 目前共 {len(competitions)} 筆競賽\n")

    # ── ① 移除過期競賽 ────────────────────────────────────────────────────────
    print("🗑️  步驟一：掃描過期競賽...")
    kept, removed = remove_expired(competitions)

    if removed:
        print(f"\n   → 移除 {len(removed)} 筆，保留 {len(kept)} 筆")
        save_competitions(kept)
        mark_removed_in_tracked(removed)
    else:
        print(f"   → 無需移除")

    # ── ② 搜尋新競賽 ──────────────────────────────────────────────────────────
    print("\n🔍 步驟二：搜尋新競賽...")
    tracked_names            = get_tracked_names()
    next_domestic, next_intl = get_next_ids()
    print(f"   已收錄：{len(tracked_names)} 筆 | 下一個 ID — 國內：{next_domestic}，國際：{next_intl}")

    raw_items = search_competitions(tracked_names, next_domestic, next_intl)
    new_items = deduplicate(raw_items, tracked_names)
    print(f"   API 回傳 {len(raw_items)} 筆 → 去重後 {len(new_items)} 筆新競賽")

    if new_items:
        print("\n📝 步驟三：更新檔案...")
        add_to_competitions_json(new_items)
        add_to_tracked_md(new_items, next_domestic, next_intl)

    # ── ③ 同步 index.html ─────────────────────────────────────────────────────
    if removed or new_items:
        print("\n🔄 步驟四：同步 index.html...")
        run_sync()

    # ── ④ 輸出供 GitHub Actions 使用 ──────────────────────────────────────────
    total_changes = len(removed) + len(new_items)
    Path("pr_body.txt").write_text(
        generate_pr_body(removed, new_items), encoding="utf-8")
    Path("change_count.txt").write_text(str(total_changes),  encoding="utf-8")
    Path("removed_count.txt").write_text(str(len(removed)),  encoding="utf-8")
    Path("new_count.txt").write_text(str(len(new_items)),    encoding="utf-8")

    # ── 結果摘要 ──────────────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  ✅ 完成！")
    print(f"  🗑️  移除過期：{len(removed)} 筆")
    print(f"  ✨ 新增競賽：{len(new_items)} 筆")
    print(f"  📊 目前總數：{len(kept) + len(new_items)} 筆")
    if total_changes > 0:
        print(f"  📬 GitHub Actions 將自動建立 Pull Request 供你審核")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
