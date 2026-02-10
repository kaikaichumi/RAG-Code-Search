# GitHub 上傳檢查清單

在上傳到 GitHub 之前，請確認以下事項：

## ✅ 必須檢查的項目

### 1. 敏感資訊檢查

- [ ] **config.yaml** - 確認沒有包含私密的 IP 位址或 API Key
  ```yaml
  # 將具體的 IP 改為範例
  llm:
    base_url: "http://localhost:11434/v1"  # ✅ 好
    # base_url: "http://192.168.1.100:8000/v1"  # ❌ 不好（私密IP）

  project:
    root_path: "/path/to/your/project"  # ✅ 好（範例路徑）
    # root_path: "D:/company/secret_project"  # ❌ 不好（真實路徑）
  ```

### 2. .gitignore 檢查

- [ ] 確認 `.gitignore` 已經包含：
  - ✅ `chroma_db_*/` - 向量資料庫（檔案太大）
  - ✅ `venv/` - 虛擬環境
  - ✅ `__pycache__/` - Python 快取
  - ✅ `*.pyc` - Python 編譯檔案

### 3. 文件完整性

- [ ] README.md - 清楚說明專案用途和安裝步驟
- [ ] QUICKSTART.md - 快速開始指南
- [ ] EXAMPLES.md - 使用範例
- [ ] CHANGELOG.md - 更新日誌
- [ ] LICENSE - 授權檔案（MIT）

### 4. 程式碼檢查

- [ ] 移除所有 `print()` 除錯訊息
- [ ] 移除註解掉的舊程式碼
- [ ] 確認所有檔案都有適當的文件字串

### 5. 依賴套件

- [ ] requirements.txt 包含所有必要套件
- [ ] 版本號碼明確指定（避免相容性問題）

## 📋 建議檢查的項目

### 1. 建立 GitHub Repository

```bash
# 在 RAG_search 目錄中
cd RAG_search

# 初始化 Git（如果還沒有）
git init

# 新增所有檔案
git add .

# 建立第一次提交
git commit -m "Initial commit: RAG智慧查詢系統 v2.0"

# 連結到 GitHub repository
git remote add origin https://github.com/your-username/rag-search.git

# 推送到 GitHub
git push -u origin main
```

### 2. GitHub Repository 設定

建議的 Repository 設定：

- **Repository name**: `rag-search` 或 `rag-code-search`
- **Description**: "智慧程式碼查詢系統 - 使用 RAG 技術進行自然語言程式碼搜尋"
- **Public/Private**: 根據需求選擇
- **Add .gitignore**: 不需要（已經有了）
- **Add license**: 不需要（已經有 MIT license）

### 3. README.md 首頁優化

在 README.md 頂部新增徽章（可選）：

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3.13-orange.svg)
```

### 4. 建立 GitHub Topics

建議的 Topics：
- `rag`
- `retrieval-augmented-generation`
- `code-search`
- `langchain`
- `ollama`
- `chromadb`
- `nlp`
- `python`

### 5. 建立 Release

建立第一個 Release：

1. 到 GitHub Repository 頁面
2. 點擊 "Releases" → "Create a new release"
3. Tag: `v2.0`
4. Title: `RAG 智慧查詢系統 v2.0`
5. Description: 複製 CHANGELOG.md 中的 v2.0 內容

## 🔒 安全性檢查

### 檢查是否洩漏敏感資訊

```bash
# 搜尋可能的密碼或金鑰
grep -r "password" .
grep -r "secret" .
grep -r "api_key" .

# 檢查是否有真實的 IP 位址
grep -rE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" .
```

### 確認 config.yaml 使用範例值

應該使用：
```yaml
llm:
  base_url: "http://localhost:11434/v1"
  api_key: "not-needed"

project:
  root_path: "D:/code/claude_test/eclipse/HM_original"  # 改為範例路徑
```

## 📝 上傳後的工作

### 1. 更新 README.md

將 clone 指令更新為實際的 GitHub URL：

```markdown
git clone https://github.com/your-username/rag-search.git
```

### 2. 建立 GitHub Pages（可選）

如果想提供線上文件，可以啟用 GitHub Pages。

### 3. 新增 Issues 模板（可選）

建立 `.github/ISSUE_TEMPLATE/` 目錄，提供 bug 報告和功能請求模板。

### 4. 新增 Pull Request 模板（可選）

建立 `.github/pull_request_template.md`。

## ✨ 最終檢查清單

上傳前最後確認：

- [ ] 所有敏感資訊已移除或改為範例值
- [ ] .gitignore 正確設定
- [ ] 所有文件檔案完整且更新
- [ ] 程式碼可以正常執行
- [ ] requirements.txt 包含所有依賴
- [ ] LICENSE 檔案存在
- [ ] README.md 清楚易懂
- [ ] 已經測試過基本功能

## 🚀 開始上傳！

確認所有檢查項目都完成後，就可以上傳到 GitHub 了！

```bash
git status
git add .
git commit -m "Ready for GitHub upload"
git push
```

---

## 📞 需要協助？

如果在上傳過程中遇到問題，可以參考：
- [GitHub 文件](https://docs.github.com)
- [Git 基礎教學](https://git-scm.com/book/zh-tw/v2)
