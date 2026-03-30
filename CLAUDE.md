# 專案說明：台灣 K12 競賽資料庫

## 專案結構
- `competitions.json` — 所有競賽資料，**唯一需要維護的資料檔**
- `index.html` — 網站主體，資料透過 sync.py 內嵌，不要手動改
- `sync.py` — 同步工具，每次更新資料後必須執行

## 新增或更新競賽的標準流程

每次收到新增或修改競賽的指令，請依序執行：

1. 修改 `competitions.json`（新增或編輯資料）
2. 執行 `python3 sync.py` 確認同步成功
3. 執行 `git add competitions.json index.html`
4. 執行 `git commit -m "更新：[說明]"`
5. 執行 `git push`

## competitions.json 欄位規則
```json
{
  "id": 999,              // 唯一整數，國內 100–199，國際 200–299
  "name": "競賽名稱",
  "scope": "國內",        // "國內" / "國內（接軌國際）" / "國際"
  "domains": ["AI工具應用"],  // 見下方可用清單
  "level": ["國中", "高中"],
  "organizer": "主辦單位",
  "description": "說明文字（50–150字）",
  "schedule": "時程說明",
  "deadline": "截止日期",
  "url": "https://官方網站",
  "tags": ["標籤1", "標籤2"],
  "highlight": false,     // true = 顯示重點推薦
  "status": "即將開放",   // "報名中"/"開放中"/"即將開放"/"已截止"
  "updated": "2026-03"    // 今天的年月
}
```

## 可用 domains 清單
AI工具應用 / 數學 / 語文/文學 / 視覺藝術 / 科學研究 /
STEM / 跨域創新 / 社會議題 / 教育科技 / 科技

## 注意事項
- 每次修改完 competitions.json，一定要執行 sync.py 才能更新網站
- push 之前先確認 sync.py 顯示「🎉 同步完成！」
- commit message 請用中文，格式：`新增：XXX` 或 `更新：XXX 截止日`

## 防止重複收錄

每次執行搜尋或新增競賽後，必須同步更新 `tracked.md`：
1. 在對應的表格裡加一行（ID、名稱、網址）
2. 更新「下一個可用 ID」的數字
3. 在「搜尋紀錄」加一行（日期、關鍵字、新增筆數）

這樣下次搜尋時，Claude.ai 可以對照清單避免重複。
```

---

### 日後搜尋新競賽的固定句型

每次來找我搜尋，就用這個句型：
```
以下是我目前已收錄的競賽清單（tracked.md 內容）：
[貼上 tracked.md 的表格部分]

請幫我搜尋 2026 下半年到 2027 年，
台灣國中高中可以參加的新競賽（科技/AI/數學/語文/藝術），
排除以上已收錄的項目，
只回傳真正新的競賽，整理成 competitions.json 格式。
國內新競賽 ID 從 110 開始，國際從 211 開始。
```

我收到這個訊息後，會：
1. 讀取你的已收錄清單
2. 搜尋時自動跳過這些競賽
3. 只輸出新的 JSON 片段給你貼上

---

### 完整更新流程（加入防重複機制後）
```
【在 Claude.ai】
貼上 tracked.md → 請我搜尋新競賽
→ 我回傳新的 JSON 片段

【複製貼上到 competitions.json 尾端】

【在 VS Code 終端機】
python3 sync.py
git add competitions.json index.html tracked.md
git commit -m "新增：XXX 等 N 筆競賽"
git push

【更新 tracked.md】
把新競賽加進表格，更新 ID 編號