# 使用範例

本文件提供各種使用場景的範例，幫助你更好地使用 RAG 智慧查詢系統。

## 場景 1: 單一模組索引

### 適用情況
- 你只想查詢特定模組的程式碼
- 專案很大，不想索引全部

### 操作步驟

1. 執行建置工具：
   ```bash
   python rag_builder.py
   ```

2. 選擇單一資料夾：
   ```
   選擇要建立索引的資料夾

   可用的資料夾:
     1. backend (352 個檔案)
     2. frontend (198 個檔案)
     3. docs (45 個檔案)

     0. 全部資料夾

   請選擇: 1
   ```

3. 系統會建立 `chroma_db_backend/` 資料庫

4. 查詢時會自動使用這個資料庫

## 場景 2: 多模組組合索引

### 適用情況
- 你想同時查詢多個相關模組
- 例如：前端 + 後端，或是核心功能 + 工具

### 操作步驟

1. 執行建置工具：
   ```bash
   python rag_builder.py
   ```

2. 選擇多個資料夾（用逗號分隔）：
   ```
   請選擇: 1,2
   ```

3. 系統會建立 `chroma_db_backend_frontend/` 資料庫

4. 查詢時可以跨模組搜尋

### 範例問題
```
前端如何呼叫後端的 API？
登入功能的前後端實作流程是什麼？
```

## 場景 3: 建立多個知識庫

### 適用情況
- 你想針對不同需求建立不同的知識庫
- 例如：開發用 vs 測試用

### 操作步驟

1. 第一次執行，建立開發知識庫：
   ```bash
   python rag_builder.py
   # 選擇 1,2 (backend, frontend)
   ```

2. 第二次執行，建立測試知識庫：
   ```bash
   python rag_builder.py
   # 選擇 3 (tests)
   ```

3. 第三次執行，建立文件知識庫：
   ```bash
   python rag_builder.py
   # 選擇 4 (docs)
   ```

4. 查詢時選擇要使用的知識庫：
   ```
   選擇要查詢的知識庫
     1. chroma_db_backend_frontend (backend, frontend)
     2. chroma_db_tests (tests)
     3. chroma_db_docs (docs)

   請選擇: 1
   ```

## 場景 4: 不同專案使用

### 適用情況
- 你有多個專案，想為每個專案建立知識庫

### 操作步驟

1. 修改 `config.yaml`：
   ```yaml
   project:
     root_path: "/path/to/project1"
   ```

2. 建立第一個專案的知識庫：
   ```bash
   python rag_builder.py
   # 選擇要索引的資料夾
   ```

3. 再次修改 `config.yaml`：
   ```yaml
   project:
     root_path: "/path/to/project2"
   ```

4. 建立第二個專案的知識庫：
   ```bash
   python rag_builder.py
   # 選擇要索引的資料夾
   ```

5. 查詢時會看到兩個專案的知識庫，選擇要查詢的即可

## 場景 5: Web UI 多人使用

### 適用情況
- 你想讓團隊成員都能使用
- 在區網內提供查詢服務

### 操作步驟

1. 修改 `config.yaml`：
   ```yaml
   web_ui:
     host: "0.0.0.0"  # 允許區網訪問
     port: 7860
     share: false
   ```

2. 啟動 Web UI：
   ```bash
   python rag_web_ui.py
   ```

3. 取得你的 IP 位址：
   ```bash
   # Windows
   ipconfig

   # Linux/Mac
   ifconfig
   ```

4. 告訴團隊成員訪問位址：
   ```
   http://你的IP:7860
   ```

5. 團隊成員就可以在瀏覽器中使用了！

## 場景 6: 使用遠端 LLM

### 適用情況
- 你有遠端的 LLM 伺服器
- 或使用雲端 API

### 操作步驟

1. 修改 `config.yaml`：
   ```yaml
   llm:
     # 遠端 Ollama
     base_url: "http://192.168.1.100:11434/v1"
     model: "qwen2.5:14b"

     # 或其他 OpenAI 相容 API
     # base_url: "https://api.your-service.com/v1"
     # api_key: "your-api-key"
     # model: "gpt-4"
   ```

2. 正常使用即可

## 進階技巧

### 自訂檔案類型

在 `config.yaml` 中新增：
```yaml
project:
  file_extensions:
    - ".java"
    - ".py"
    - ".go"
    - ".vue"    # 新增 Vue 檔案
    - ".dart"   # 新增 Dart 檔案
```

### 排除特定目錄

```yaml
project:
  exclude_dirs:
    - ".git"
    - "node_modules"
    - "vendor"
    - "generated"  # 新增排除自動產生的程式碼
```

### 調整搜尋精準度

```yaml
vectorstore:
  # 增加片段數量 = 更多上下文，但回答較慢
  search_top_k: 10

chunking:
  # 較小的片段 = 更精準，但可能遺失上下文
  chunk_size: 1000
```

### 針對特定語言優化

**Java 專案：**
```yaml
project:
  file_extensions:
    - ".java"
    - ".xml"
    - ".properties"

chunking:
  chunk_size: 2000  # Java 類別通常較大
```

**Python 專案：**
```yaml
project:
  file_extensions:
    - ".py"
    - ".ipynb"
    - ".yaml"

chunking:
  chunk_size: 1200  # Python 函數通常較小
```

**Web 專案：**
```yaml
project:
  file_extensions:
    - ".js"
    - ".jsx"
    - ".ts"
    - ".tsx"
    - ".vue"
    - ".css"
    - ".scss"
    - ".html"
```

## 疑難排解

### 問題：索引很慢

**解決方案：**
1. 使用更快的 Embedding 模型：
   ```yaml
   embedding:
     model: "nomic-embed-text"  # 比 qwen3-embedding 快
   ```

2. 減少索引的檔案類型
3. 只索引必要的資料夾

### 問題：回答不精確

**解決方案：**
1. 增加搜尋片段數：
   ```yaml
   vectorstore:
     search_top_k: 10
   ```

2. 減少片段大小：
   ```yaml
   chunking:
     chunk_size: 1000
   ```

3. 重新建立知識庫

### 問題：記憶體不足

**解決方案：**
1. 減少片段大小
2. 分批索引（每次只索引一個資料夾）
3. 關閉其他應用程式

## 最佳實踐

1. **定期更新知識庫**：程式碼有大幅修改時，重新建立知識庫
2. **使用多個知識庫**：針對不同需求建立專用知識庫
3. **調整參數**：根據你的硬體和需求調整 config.yaml
4. **清晰的問題**：提出具體、明確的問題能得到更好的答案
5. **備份設定**：上傳到 Git 前確認 config.yaml 沒有敏感資訊
