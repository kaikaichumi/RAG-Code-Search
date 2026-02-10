# 快速開始指南

## 🚀 5 分鐘快速上手

### Windows 使用者

1. **安裝環境**
   ```cmd
   雙擊執行 setup.bat
   ```

2. **安裝 Ollama**
   - 下載並安裝：https://ollama.com
   - 下載模型：
     ```cmd
     ollama pull qwen3-embedding:0.6b
     ollama pull qwen2.5:14b
     ```

3. **設定專案路徑**
   - 編輯 `config.yaml`
   - 修改 `project.root_path` 為你的專案路徑

4. **建立知識庫**
   ```cmd
   雙擊執行 build.bat
   ```
   - 選擇要索引的資料夾（輸入數字）
   - 等待索引完成（約 10-40 分鐘，視專案大小而定）

5. **開始查詢**
   ```cmd
   雙擊執行 web_ui.bat
   ```
   - 瀏覽器會自動開啟 http://localhost:7860
   - 開始提問！

### Linux/Mac 使用者

1. **安裝環境**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **安裝 Ollama**
   - 下載並安裝：https://ollama.com
   - 下載模型：
     ```bash
     ollama pull qwen3-embedding:0.6b
     ollama pull qwen2.5:14b
     ```

3. **設定專案路徑**
   - 編輯 `config.yaml`
   - 修改 `project.root_path` 為你的專案路徑

4. **建立知識庫**
   ```bash
   ./build.sh
   ```
   - 選擇要索引的資料夾（輸入數字）
   - 等待索引完成

5. **開始查詢**
   ```bash
   ./web_ui.sh
   ```
   - 瀏覽器開啟 http://localhost:7860
   - 開始提問！

## 💡 使用技巧

### 選擇資料夾

執行 `build.bat` 或 `build.sh` 時會顯示：

```
選擇要建立索引的資料夾

專案根目錄: D:/code/my_project

可用的資料夾:
  1. src (145 個檔案)
  2. docs (23 個檔案)
  3. tests (67 個檔案)

  0. 全部資料夾

請選擇 (輸入數字，多個用逗號分隔，如 1,2,3 或 0 表示全部):
```

**選項：**
- 輸入 `1` - 只索引 src 資料夾
- 輸入 `1,2` - 索引 src 和 docs 資料夾
- 輸入 `0` - 索引全部資料夾

### 多個知識庫

你可以為不同的資料夾組合建立多個知識庫：

1. 第一次執行 `build.bat`，選擇 `1,2`（src + docs）
2. 第二次執行 `build.bat`，選擇 `3`（tests）

系統會建立兩個獨立的知識庫：
- `chroma_db_docs_src/`
- `chroma_db_tests/`

查詢時會讓你選擇要使用哪個知識庫。

### 提問技巧

**好的問題：**
- ✅ "認證系統的實作在哪裡？"
- ✅ "如何新增一個 API 端點？"
- ✅ "資料庫連線的設定方式是什麼？"
- ✅ "錯誤處理的邏輯在哪個檔案？"

**不好的問題：**
- ❌ "這是什麼？"（太籠統）
- ❌ "幫我寫程式碼"（系統是查詢工具，不是程式碼產生器）

## 🔧 常見問題

### Q: 向量資料庫很大，要上傳到 Git 嗎？

A: 不用！`.gitignore` 已經設定好排除 `chroma_db_*` 目錄。

### Q: 可以修改 Embedding 模型嗎？

A: 可以！編輯 `config.yaml` 的 `embedding.model`，支援所有 Ollama 的 embedding 模型。

### Q: 可以使用遠端的 Ollama 服務嗎？

A: 可以！編輯 `config.yaml` 的 `embedding.base_url` 和 `llm.base_url`。

### Q: 支援其他語言嗎？

A: 支援！只要在 `config.yaml` 的 `file_extensions` 中新增副檔名即可。

## 📚 更多資訊

詳細說明請參閱 [README.md](README.md)
