# Git Sync 失敗診斷

## 🔍 問題識別

### 分支狀態
```
本地分支: feat_search
遠程分支: origin/feat_search
狀態: 已發散 (diverged)
```

### 提交歷史對比

**本地 (HEAD -> feat_search)**
```
c4a6b8f - feat(search): improve modal interaction and keyboard handling  ← 新增 (本地)
cae4f33 - feat(search): improve search functionality and UI interactions
4c8ae6c - feat(search): parallelize fetching Taiwan and US ETF lists
444b9bf - feat(search): enhance search scoring for symbols and names
4ea1229 - refactor(search): improve search scoring logic for symbols
```

**遠程 (origin/feat_search)**
```
14a307c - feat(search): improve search functionality and UI interactions  ← 不同 commit
4c8ae6c - feat(search): parallelize fetching Taiwan and US ETF lists
444b9bf - feat(search): enhance search scoring for symbols and names
4ea1229 - refactor(search): improve search scoring logic for symbols
4cd71b8 - feat: integrate dynamic Taiwan ETF data into search and update UI
```

---

## 📊 發散原因分析

### 情況 1: 本地修訂歷史 (Amend)

```
遠程端:
  14a307c - 舊提交 (改進搜尋功能)
  
本地端:
  cae4f33 - 新提交 (改進搜尋功能，SHA1 不同)
  
原因:
  • 使用了 git commit --amend
  • 導致 commit 訊息改變或內容變動
  • 新舊 commit SHA1 不同，Git 認為是不同的提交
```

### 情況 2: 本地新增提交

```
本地新增:
  c4a6b8f - feat(search): improve modal interaction and keyboard handling
  
這個提交遠程沒有，但遠程有：
  14a307c - 不在本地的提交
  
結果: 分支發散
```

---

## 🛠️ 解決方案

### 方案 A: 使用 Rebase (推薦) ⭐⭐⭐

```bash
git pull --rebase origin feat_search
```

**流程**:
1. 取得遠程最新提交 (14a307c)
2. 將本地特有提交 (c4a6b8f, cae4f33) 重新應用在遠程之上
3. 結果: 線性歷史，無發散

**優勢**:
- 歷史乾淨
- 便於 code review
- 遵循線性提交慣例

**風險**:
- 如果有衝突，需要手動解決
- 修改了本地提交的時間戳

---

### 方案 B: 使用 Merge (保守)

```bash
git merge origin/feat_search
```

**流程**:
1. 創建合併提交
2. 將遠程分支合併到本地
3. 結果: 發散歷史保留，但已連接

**優勢**:
- 保留完整歷史
- 衝突處理簡單

**劣勢**:
- 歷史樹變複雜
- 多個 merge 提交會污染歷史

---

### 方案 C: 強制推送本地 (危險) ❌

```bash
git push --force-with-lease origin feat_search
```

**不推薦理由**:
- 會覆蓋遠程的 14a307c 提交
- 如果有其他協作者已 pull，會導致他們的分支損壞
- 難以追蹤變更

---

## 📋 立即執行步驟

### Step 1: 檢查是否有未提交的變更

```bash
git status
# 預期輸出: working tree clean ✅
```

### Step 2: 查看可能的衝突

```bash
git rebase origin/feat_search --dry-run
```

如果沒有輸出，表示可以安全 rebase。

### Step 3: 執行 Rebase

```bash
git pull --rebase origin feat_search
```

**如果有衝突**:
```bash
# 1. 解決衝突 (編輯有 <<<<<<< 標記的檔案)
# 2. git add <resolved-file>
# 3. git rebase --continue
```

### Step 4: 驗證結果

```bash
git log --oneline -5
# 應該看到線性歷史
```

### Step 5: 推送到遠程

```bash
git push origin feat_search
```

---

## 🔬 為什麼會發散?

**最可能的原因**: 使用 `git commit --amend` 修改上一個提交

我在之前的操作中看到:
```
git commit --amend --no-edit
```

這會:
1. 修改最新提交的 SHA1
2. 導致本地和遠程的同一提交變成不同的 SHA1
3. Git 認為是不同的提交，導致分支發散

---

## ✅ 建議的最佳實踐

### 未來避免發散的方法

1. **避免在已 push 的提交上使用 amend**
   ```bash
   # ❌ 不要這樣做
   git commit
   git push
   git commit --amend
   git push --force
   
   # ✅ 應該這樣做
   git commit
   git push
   # 如需修改，創建新的修復提交
   git commit -m "fix: ..."
   git push
   ```

2. **使用 rebase -i 進行本地提交整理** (未 push 時)
   ```bash
   git rebase -i HEAD~3
   # 在本地調整提交，再統一 push
   ```

3. **團隊協作約定**
   - 一人一分支
   - 定期同步遠程
   - PR 合併使用 Squash 或 Rebase

---

## 🎯 立即解決方案

運行以下命令:

```bash
# 1. 檢查是否安全
git rebase origin/feat_search --dry-run

# 2. 執行 rebase
git pull --rebase origin feat_search

# 3. 驗證成功
git log --oneline -3
git status

# 4. 推送
git push origin feat_search
```

