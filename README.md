# 🏆 台灣 K12 科技 × 跨領域競賽資料庫

> 適合**國中 7–9 年級、高中生**參加的科技、AI、數學、語文、藝術跨領域競賽整理  
> 符合 108 課綱素養導向精神 · 2026 年起持續更新

**🌐 線上查詢網址：**  
`https://[你的GitHub帳號].github.io/taiwan-k12-competition-tracker/`

---

## 📖 目錄

- [這是什麼](#這是什麼)
- [如何使用（給老師和學生）](#如何使用給老師和學生)
- [如何新增競賽（只需改一個檔案）](#如何新增競賽只需改一個檔案)
- [如何部署到 GitHub Pages](#如何部署到-github-pages)
- [專案結構說明](#專案結構說明)
- [競賽分類說明](#競賽分類說明)
- [回報問題 / 建議新競賽](#回報問題--建議新競賽)
- [版本紀錄](#版本紀錄)

---

## 這是什麼

本資料庫整理了國內外適合台灣國中、高中學生參加的跨領域競賽，涵蓋：

| 領域 | 代表競賽 |
|------|---------|
| 🤖 AI 工具應用 | WAICY、IOAI、USAII Hackathon |
| 📐 數學 | WMI 世界數學邀請賽、數感盃 |
| ✍️ 語文/文學 | 數感盃 AI 共創詩、全國高中生成式 AI 創意競賽 |
| 🎨 視覺藝術 | WAICY AI 藝術組、Wix Creators of Tomorrow |
| 🔬 科學研究 | 全國科展、TISF、Regeneron ISEF |
| 🌐 跨域創新 | ISTE AI Innovator、QS AI for ImpACT |
| 🌱 社會議題 | Presidential AI Challenge、FLL |

**設計原則：**
- 資料與程式碼分離 → 更新競賽只需修改 `competitions.json`
- 純 HTML + JavaScript，**不需任何安裝或 build**，GitHub Pages 直接可用
- 支援多條件篩選（範圍、學段、狀態、領域、關鍵字搜尋）

---

## 如何使用（給老師和學生）

直接開啟瀏覽器，前往網址即可查詢：

- **依領域篩選**：點擊上方的領域標籤（🤖 AI、📐 數學、✍️ 語文…）
- **依學段篩選**：點擊「國中」或「高中」
- **依狀態篩選**：可篩選「報名中」「即將開放」「已截止」
- **關鍵字搜尋**：輸入競賽名稱、組織或關鍵字
- **點開卡片**：展開後可看到詳細時程、截止日、官方連結

> ⚠️ 各競賽日程每年都會異動，請務必點擊「前往官方網站」確認最新報名資訊。

---

## 如何新增競賽（只需改一個檔案）

**只需要編輯 `competitions.json`，完全不需要碰程式碼。**

### 步驟

1. 打開 `competitions.json`，在陣列最後新增一筆競賽（參考下方範本）
2. 存檔後，執行同步指令：
   ```bash
   python3 sync.py
   ```
3. 確認終端機顯示 `🎉 同步完成！` 即可 Push：

```bash
git add competitions.json index.html
git commit -m "新增：XXX競賽 2026"
git push
```

4. 約 1 分鐘後，網站自動更新 ✅

> 💡 **為什麼需要 sync.py？**  
> GitHub Pages 是靜態網頁，`fetch()` 讀取本地 JSON 時會遇到瀏覽器安全限制（CORS）。  
> 因此資料需要直接內嵌在 `index.html` 裡。`sync.py` 幫你自動完成這個步驟，  
> 你只需要維護 `competitions.json`，不需要手動改 HTML。

---

### 複製以下範本，填入新競賽資料：

```json
{
  "id": 999,
  "name": "競賽名稱（必填）",
  "scope": "國內",
  "domains": ["AI工具應用", "跨域創新"],
  "level": ["國中", "高中"],
  "organizer": "主辦單位名稱",
  "description": "競賽說明，建議 50–150 字，包含：競賽目的、適合什麼能力的學生、有什麼特色。",
  "schedule": "時程說明，例如：報名：每年 3 月；決賽：每年 5 月",
  "deadline": "報名截止日期，例如：2026/5/31",
  "url": "https://官方網站網址",
  "tags": ["關鍵字1", "關鍵字2"],
  "highlight": false,
  "status": "報名中",
  "updated": "2026-03"
}
```

4. 存檔 → `git add . → git commit -m "新增：XXX競賽" → git push`
5. 約 1–2 分鐘後，網站自動更新 ✅

---

### 欄位說明

| 欄位 | 說明 | 可填值 |
|------|------|-------|
| `id` | 唯一編號（不重複即可，建議流水號） | 任意數字 |
| `scope` | 賽事範圍 | `"國內"` / `"國內（接軌國際）"` / `"國際"` |
| `domains` | 領域陣列，可選多個 | 見下方領域清單 |
| `level` | 適合學段陣列 | `"國中"` / `"高中"` |
| `highlight` | 是否顯示「重點推薦」標籤 | `true` / `false` |
| `status` | 當前狀態 | `"報名中"` / `"開放中"` / `"即將開放"` / `"已截止"` |
| `updated` | 資料最後更新月份 | `"YYYY-MM"` |

### 可用領域清單

```
AI工具應用 / 數學 / 語文/文學 / 視覺藝術 / 科學研究 /
STEM / 跨域創新 / 社會議題 / 教育科技 / 科技
```

---

## 如何部署到 GitHub Pages

### 第一次設定（約 5 分鐘）

```bash
# 1. 在 GitHub 建立新的 repository
#    名稱建議：taiwan-k12-competition-tracker
#    設定為 Public（才能免費使用 Pages）

# 2. Clone 到本機
git clone https://github.com/[你的帳號]/taiwan-k12-competition-tracker.git
cd taiwan-k12-competition-tracker

# 3. 把這三個檔案放進去
#    index.html
#    competitions.json
#    README.md

# 4. Push 上去
git add .
git commit -m "初始版本：台灣 K12 競賽資料庫"
git push origin main
```

### 開啟 GitHub Pages

1. 前往 GitHub repo 頁面
2. 點擊 **Settings** → **Pages**
3. Source 選擇 **Deploy from a branch**
4. Branch 選擇 **main** → 目錄選 **/ (root)**
5. 點擊 **Save**
6. 等 1–2 分鐘，網址就會出現：`https://[帳號].github.io/taiwan-k12-competition-tracker/`

### 日後更新競賽資料

```bash
# 1. 修改 competitions.json（新增或編輯競賽）
# 2. 同步資料到 index.html
python3 sync.py

# 3. 提交並推送
git add competitions.json index.html
git commit -m "更新：新增 XXX 競賽 2026"
git push
# GitHub Actions 自動重新部署，約 1 分鐘生效 ✅
```

---

## 專案結構說明

```
taiwan-k12-competition-tracker/
│
├── index.html                      ← 網站主體（含內嵌資料，不需手動修改）
├── competitions.json               ← 所有競賽資料 ✅ 只改這裡
├── sync.py                         ← 同步工具（改完 JSON 後執行）
├── README.md                       ← 本說明文件
├── CONTRIBUTING.md                 ← 協作者新增競賽的詳細說明
└── .github/workflows/deploy.yml   ← 自動部署設定
```

> **設計邏輯：**  
> - 維護只需修改 `competitions.json`（純文字，易讀）  
> - 執行 `python3 sync.py` 將資料同步進 `index.html`  
> - Push 後 GitHub Pages 自動重新部署，無需任何 build 工具

---

## 競賽分類說明

### 狀態（status）定義

| 狀態 | 說明 |
|------|------|
| 🟢 報名中 | 目前正在接受報名 |
| 🟢 開放中 | 正在進行（如常設性競賽） |
| 🟡 即將開放 | 預計近期開放，確切日期待公告 |
| 🔴 已截止 | 本屆已截止，保留參考下屆 |

### 範圍（scope）定義

| 範圍 | 說明 |
|------|------|
| 國內 | 在台灣辦理，主要面向台灣學生 |
| 國內（接軌國際） | 在台灣辦理，但獲獎可代表台灣參加國際賽 |
| 國際 | 直接以個人或團隊身分向國際組織報名 |

---

## 回報問題 / 建議新競賽

歡迎透過以下方式貢獻：

1. **GitHub Issues**（推薦）：[點此開 Issue](../../issues/new)  
   請包含：競賽名稱、官方連結、適合學段、截止日期

2. **Pull Request**：直接修改 `competitions.json`，送出 PR

3. **其他聯絡方式**：可在 Issue 中留言

---

## 版本紀錄

| 版本 | 日期 | 內容 |
|------|------|------|
| v1.0 | 2026-03 | 初始版本，共 19 項競賽，涵蓋科技、AI、數學、語文、藝術跨領域 |

---

## 授權

本專案資料採 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.zh-TW) 授權，歡迎轉載或改作，請附上來源連結。

程式碼部分採 MIT License。

---

*本資料庫由台灣教師社群協作維護，非官方資訊，請以各競賽官方網站公告為準。*
