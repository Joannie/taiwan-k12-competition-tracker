# 台灣 K12 競賽資料庫 — Claude Code 工作說明書

## 專案資訊

- **GitHub Repo：** 請至 GitHub repo 的 Settings → Pages 確認網址
- **線上網站：** 請至 GitHub repo 的 Settings → Pages 確認網址

> 本檔案（CLAUDE.md）已加入 .gitignore，不會上傳到 GitHub。

---

## 專案結構

```
[專案根目錄]\
├── competitions.json    ← 所有競賽資料（唯一需要維護的資料檔）
├── tracked.md           ← 已收錄清單（防止重複，自動維護）
├── index.html           ← 網站主體（資料透過 sync.py 內嵌，不要手動改）
├── sync.py              ← 同步工具（改完 JSON 後必須執行）
├── monthly_search.py    ← 每月自動搜尋腳本
├── CLAUDE.md            ← 本說明文件
└── .github/workflows/   ← GitHub Actions 自動部署設定
```

---

## 重要規則（每次執行前必讀）

1. **永遠不要**在未經使用者確認的情況下執行 `git push`
2. **永遠**在執行前列出確認清單
3. **永遠**在修改 `competitions.json` 後執行 `python sync.py`
4. **同步更新** `tracked.md`，不要讓它與 `competitions.json` 脫節
5. 修改任何檔案前，先讀取該檔案確認目前內容與格式

---

## competitions.json 欄位規則

```json
{
  "id": 999,
  "name": "競賽完整名稱",
  "scope": "國內",
  "domains": ["AI工具應用"],
  "level": ["國中", "高中"],
  "organizer": "主辦單位",
  "description": "說明文字（50–150字）",
  "schedule": "時程說明",
  "deadline": "YYYY/MM/DD 格式（讓系統可判斷是否過期）",
  "url": "https://官方網站",
  "tags": ["標籤1", "標籤2"],
  "highlight": false,
  "status": "即將開放",
  "updated": "YYYY-MM"
}
```

**scope** 只能填：`"國內"` / `"國內（接軌國際）"` / `"國際"`

**domains** 只能從以下選：
`AI工具應用` / `數學` / `語文/文學` / `視覺藝術` / `科學研究` /
`STEM` / `跨域創新` / `社會議題` / `教育科技` / `科技`

**level** 只能填：`"國中"` / `"高中"`

**status** 只能填：`"報名中"` / `"開放中"` / `"即將開放"` / `"已截止"`

---

## tracked.md 維護規則

- 國內競賽新 ID 從「下一個可用 ID」欄位讀取（目前：**110**）
- 國際競賽新 ID 從「下一個可用 ID」欄位讀取（目前：**222**）
- 每次新增競賽後：
  1. 在對應表格末尾加入新列：`| ID | 競賽名稱 | 官方網址 |`
  2. 更新「下一個可用 ID」的數字
  3. 在「搜尋紀錄」加一列

---

## 自動更新流程（收到新競賽資料時）

### 步驟一：執行前，先列出確認清單

格式如下，讓使用者確認後才繼續：

```
━━━ 請確認以下變更 ━━━

📝 competitions.json 新增：
  - [ID] 競賽名稱（scope，學段）
  - [ID] 競賽名稱（scope，學段）
  ...共 N 筆

📋 tracked.md 更新：
  - 新增 N 列到國際/國內競賽表格
  - 下一個可用 ID：國內 110 → 110 / 國際 222 → 223

💬 commit message：
  「新增：XXX 等 N 筆競賽」

確認後輸入「執行」繼續，或說明需要修改的地方。
━━━━━━━━━━━━━━━━━━━━━
```

### 步驟二：使用者說「執行」後，依序完成

```bash
# 1. 修改 competitions.json（新增競賽到陣列末尾）
# 2. 修改 tracked.md（新增列、更新 ID、加搜尋紀錄）
# 3. 同步資料到 index.html
python sync.py

# 4. 加入暫存區
git add competitions.json index.html tracked.md

# 5. commit
git commit -m "新增：XXX 等 N 筆競賽"

# 6. push（最後一步，再次確認才執行）
git push
```

### 步驟三：完成後回報結果

```
✅ 完成！
   新增：N 筆競賽
   目前總數：XX 筆
   網站更新：約 1 分鐘後生效
   網址：請至 GitHub Pages 確認（Settings → Pages）
```

---

## 狀態更新流程（修改現有競賽的狀態）

當競賽狀態改變時（例如「即將開放」→「報名中」，或「報名中」→「已截止」）：

```bash
# 讀取 competitions.json，找到對應競賽，修改 status 和 updated 欄位
# 執行同步
python sync.py
# commit
git add competitions.json index.html
git commit -m "更新：XXX 狀態改為「已截止」"
git push
```

---

## 移除過期競賽流程

手動移除時：
1. 從 `competitions.json` 刪除該筆資料
2. 在 `tracked.md` 對應列加上刪除線：`~~競賽名稱~~`
3. 執行 `python sync.py`
4. commit 並 push

---

## 常用指令速查

```bash
# 查看目前競賽總數
python -c "import json; d=json.load(open('competitions.json',encoding='utf-8')); print(f'共 {len(d)} 筆競賽')"

# 查看所有已截止的競賽
python -c "import json; d=json.load(open('competitions.json',encoding='utf-8')); [print(c['name']) for c in d if c['status']=='已截止']"

# 手動執行同步
python sync.py

# 手動執行每月搜尋（需要 ANTHROPIC_API_KEY 環境變數）
python monthly_search.py

# 查看 git 狀態
git status

# 查看最近的 commit 紀錄
git log --oneline -10
```

---

## 注意事項

- Windows 路徑使用反斜線 `\`，但 Python 和 git 指令中用正斜線 `/` 或雙反斜線 `\\` 均可
- 確保 Python 已加入 PATH（執行 `python --version` 確認）
- 確保 git 已設定帳號（`git config user.name` 確認）
- 每次 push 前確認 git remote 指向正確的 repo：`git remote -v`
