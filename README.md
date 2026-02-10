# RAG 智慧查詢系統

基於 RAG (Retrieval-Augmented Generation) 技術的智慧程式碼查詢系統，讓你可以用自然語言快速查詢專案中的程式碼和文件。

## ✨ 新版特色

- **🎯 靈活的資料夾選擇**：建立知識庫時可以選擇特定資料夾或全部資料夾
- **📦 多知識庫支援**：可以為不同的資料夾組合建立多個知識庫
- **🔍 智慧查詢**：自動選擇合適的知識庫進行查詢
- **🌐 雙介面**：Web UI（友善）+ 命令列（極客）
- **⚡ 高效能**：支援本機或遠端 Ollama 服務

---

## 📋 目錄

- [系統架構](#系統架構)
- [功能特色](#功能特色)
- [環境需求](#環境需求)
- [快速開始](#快速開始)
- [使用教學](#使用教學)
- [進階設定](#進階設定)
- [常見問題](#常見問題)

---

## 🏗️ 系統架構

```
┌─────────────────────────────┐
│  你的電腦 (本機)              │
│                               │
│  ┌─────────────────────┐    │
│  │ Ollama              │    │       ┌──────────────────┐
│  │ Embedding 模型       │    │       │ 區網 LLM 伺服器   │
│  │ (qwen3-embedding)   │    │       │                  │
│  └─────────────────────┘    │  ──→  │ Qwen3 30B API    │
│                               │  ←──  │                  │
│  ┌─────────────────────┐    │       └──────────────────┘
│  │ ChromaDB            │    │
│  │ 向量資料庫           │    │
│  └─────────────────────┘    │
│                               │
│  ┌─────────────────────┐    │
│  │ RAG 查詢介面         │    │
│  │ - Web UI (Gradio)   │    │
│  │ - 命令列介面         │    │
│  └─────────────────────┘    │
└─────────────────────────────┘
```

**運作流程：**
1. 你輸入問題（自然語言）
2. 本機 Embedding 模型將問題向量化
3. 從 ChromaDB 搜尋最相關的程式碼片段
4. 將片段 + 問題送到區網 Qwen3 30B
5. 回傳精準的答案和檔案路徑

---

## ✨ 功能特色

- ✅ **自然語言查詢**：用自然語言詢問程式碼相關問題
- ✅ **精準定位**：自動找到相關的檔案和程式碼位置
- ✅ **多檔案類型**：支援 Java、Python、JavaScript、TypeScript、C++、Go、Rust 等多種語言
- ✅ **靈活的索引**：可選擇特定資料夾或全部資料夾建立索引
- ✅ **雙介面**：Web UI（友善）+ 命令列（極客）
- ✅ **本地 Embedding**：CPU 即可運行，不需 GPU
- ✅ **LLM API 支援**：支援 OpenAI 相容的 API（Ollama、vLLM 等）

---

## 💻 環境需求

### 必須
- **作業系統**：Windows 10/11、Linux、macOS
- **Python**：3.8 或以上
- **記憶體**：8GB RAM（最低）/ 16GB RAM（建議）
- **磁碟空間**：5GB（含模型和資料庫）
- **處理器**：Intel i5 或以上（CPU 即可，不需 GPU）

### 軟體依賴
- [Python](https://www.python.org/downloads/)
- [Ollama](https://ollama.com)（用於 Embedding 和 LLM）

---

## 🚀 快速開始

### 步驟 1：Clone 專案

```bash
git clone <your-repo-url>
cd RAG_search
```

### 步驟 2：安裝 Python 依賴

```bash
# 建立虛擬環境（建議）
python -m venv venv

# 啟動虛擬環境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 步驟 3：安裝 Ollama 和模型

1. 前往 [https://ollama.com](https://ollama.com) 下載並安裝 Ollama

2. 下載 Embedding 模型：
   ```bash
   # 推薦：中文+程式碼雙強
   ollama pull qwen3-embedding:0.6b

   # 或選擇輕量版本
   ollama pull nomic-embed-text
   ```

3. 下載 LLM 模型：
   ```bash
   # 推薦：Qwen2.5 14B
   ollama pull qwen2.5:14b

   # 或其他模型
   ollama pull llama3.1:8b
   ```

### 步驟 4：設定 config.yaml

編輯 `config.yaml`，修改以下部分：

```yaml
project:
  # 改成你的專案根目錄
  root_path: "/path/to/your/project"

embedding:
  # Ollama 服務位址（本機或遠端）
  base_url: "http://localhost:11434"

llm:
  # LLM API 位址（Ollama 或其他 OpenAI 相容 API）
  base_url: "http://localhost:11434/v1"
  model: "qwen2.5:14b"
```

### 步驟 5：建立知識庫

```bash
python rag_builder.py
```

程式會顯示專案中的所有資料夾，讓你選擇要索引的資料夾：
- 輸入數字選擇單一或多個資料夾（用逗號分隔）
- 輸入 `0` 選擇全部資料夾

### 步驟 6：開始查詢

**選項 A：Web UI（推薦）**

```bash
python rag_web_ui.py
```

瀏覽器會自動開啟 `http://localhost:7860`

**選項 B：命令列**

```bash
python rag_query.py
```

---

## 📖 使用教學

### Web UI 介面

![Web UI 示意圖]

1. **輸入問題**：在文字框輸入你的問題
2. **點擊查詢**：按「🔍 查詢」按鈕
3. **查看結果**：
   - 上方顯示 AI 回答（Markdown 格式）
   - 下方顯示相關的檔案來源

### 範例問題

```
這個專案的主要功能是什麼？
API 認證的流程是什麼？
資料庫連線設定在哪個檔案？
Controller 在哪裡？
如何新增一個新功能？
錯誤處理的邏輯在哪裡？
測試檔案在哪裡？
配置文件的結構是什麼？
```

### 命令列介面

```bash
# 啟動命令列查詢
python rag_query.py

# 選擇知識庫（如果有多個）
選擇要查詢的知識庫
  1. chroma_db_Module1_Module2 (Module1, Module2)
請選擇 (輸入數字): 1

# 輸入問題
🤔 你的問題: 這個專案的主要功能是什麼？

# 查看回答
🔍 搜尋中...
======================================================================
這個專案主要實現了以下功能：

1. src/main.py:15 - 主程式入口
   - 初始化系統配置
   - 啟動服務
   ...

📁 相關檔案來源：
  1. [Module1] src/main.py
  2. [Module1] README.md
```

---

## ⚙️ 進階設定

### 調整搜尋精準度

編輯 `config.yaml`：

```yaml
vectorstore:
  # 搜尋時回傳的片段數量
  # 越多：上下文越豐富，但回答越慢
  # 越少：回答更快，但可能不夠精準
  search_top_k: 6  # 預設 6，可調整為 3-10
```

### 調整文件切割大小

```yaml
chunking:
  # 每個片段的字元數
  chunk_size: 1500  # 預設 1500，可調整為 1000-3000

  # 片段間重疊的字元數
  chunk_overlap: 300  # 預設 300，建議為 chunk_size 的 20%
```

### 更換 Embedding 模型

```yaml
embedding:
  # 可選模型：
  # - qwen3-embedding（推薦：中文+程式碼）
  # - nomic-embed-text（輕量快速）
  # - bge-m3（中文強）
  model: "qwen3-embedding"
```

### 更換不同的專案

```yaml
project:
  # 修改專案根目錄即可
  root_path: "/path/to/another/project"
```

執行 `python rag_builder.py` 時，會自動掃描新專案中的資料夾供你選擇。

### 區網內其他人使用

編輯 `config.yaml`：

```yaml
web_ui:
  host: "0.0.0.0"     # 監聽所有網路介面
  port: 7860          # 可改成其他 port
  share: false        # 改成 true 可分享到外網（慎用）
```

然後其他人可以透過你的 IP 訪問：`http://你的IP:7860`

---

## 🔧 常見問題

### Q1：建立知識庫時顯示 "找不到 Ollama"

**解決方法：**
1. 確認 Ollama 已安裝：`ollama --version`
2. 確認 Ollama 服務正在執行（安裝後會自動啟動）
3. Windows 防火牆可能需要允許 Ollama

### Q2：查詢時顯示 "連接 LLM API 失敗"

**解決方法：**
1. 確認區網 LLM API 正在運行
2. 確認 `config.yaml` 中的 `base_url` 正確
3. 測試 API 是否可達：
   ```bash
   curl http://你的API位址/v1/models
   ```
4. 檢查防火牆設定

### Q3：建立知識庫很慢（超過 1 小時）

**原因：** CPU 效能較低，Embedding 運算較慢

**解決方法：**
1. 更換為更輕量的模型：`nomic-embed-text`
2. 減少索引的檔案類型（編輯 `config.yaml`）
3. 只索引特定模組（編輯 `include_dirs`）

### Q4：記憶體不足

**解決方法：**
1. 關閉其他應用程式
2. 減少 `search_top_k` 數量
3. 減少 `chunk_size` 大小

### Q5：回答不夠精準

**解決方法：**
1. 增加 `search_top_k`（找更多相關片段）
2. 減少 `chunk_size`（片段更細緻）
3. 問更具體的問題（例如加上模組名稱或檔案類型）
4. 重新建立知識庫（`3_build_db.bat`）

### Q6：如何更新知識庫（程式碼有修改）

**方法：** 重新執行建立知識庫
```bash
python rag_builder.py
```

選擇相同的資料夾組合時，會詢問是否覆蓋舊資料庫。

### Q7：Web UI 無法開啟

**解決方法：**
1. 確認 Port 7860 沒有被佔用
2. 更改 `config.yaml` 中的 `port` 設定
3. 檢查防火牆設定

---

## 📂 檔案結構

```
RAG_search/
├── config.yaml                    # 主設定檔
├── requirements.txt               # Python 套件清單
├── rag_builder.py                 # 建立知識庫腳本（互動式選擇資料夾）
├── rag_query.py                   # 命令列查詢腳本
├── rag_web_ui.py                  # Web UI 腳本
├── README.md                      # 本檔案
├── .gitignore                     # Git 忽略檔案
├── venv/                          # Python 虛擬環境（執行後自動建立）
└── chroma_db_*/                   # 向量資料庫（執行後自動建立，一個資料夾組合一個）
```

---

## 🛠️ 維護與更新

### 更新 Python 套件

```bash
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install --upgrade -r requirements.txt
```

### 更新 Embedding 模型

```bash
ollama pull qwen3-embedding:0.6b
```

### 清理向量資料庫

```bash
# 刪除所有向量資料庫
rm -rf chroma_db_*

# 或刪除特定資料庫
rm -rf chroma_db_Module1_Module2

# 然後重新建立
python rag_builder.py
```

---

## 📝 技術細節

### 使用的套件

| 套件 | 版本 | 用途 |
|------|------|------|
| langchain | 0.3.13 | RAG 框架 |
| langchain-ollama | 0.2.3 | Ollama 整合 |
| langchain-openai | 0.2.14 | OpenAI API 相容介面 |
| chromadb | 0.5.25 | 向量資料庫 |
| gradio | 5.12.0 | Web UI 框架 |
| unstructured | 0.16.16 | 文件載入 |

### Embedding 模型比較

| 模型 | 參數量 | 磁碟大小 | CPU 速度 | 中文能力 | 程式碼能力 |
|------|--------|---------|---------|---------|-----------|
| **qwen3-embedding** | 0.6B | ~1.2GB | 中等 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| nomic-embed-text | 0.14B | ~270MB | 快 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| bge-m3 | 0.57B | ~1.1GB | 中等 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 效能數據（參考）

- **建立知識庫**：20-40 分鐘（722 個 Java 檔案，Intel i7 CPU）
- **單次查詢時間**：5-15 秒（含 API 往返）
- **向量資料庫大小**：約 500MB
- **記憶體使用**：2-4GB（執行期間）

---

## 🤝 支援

如有問題，請檢查：
1. 本 README 的常見問題章節
2. `config.yaml` 設定是否正確
3. Ollama 和區網 LLM API 是否正常運作

---

## 📄 授權

本專案為開源工具，歡迎自由使用和修改。

---

## 🙏 致謝

- [LangChain](https://github.com/langchain-ai/langchain) - RAG 框架
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量資料庫
- [Ollama](https://ollama.com) - 本地 LLM 服務
- [Gradio](https://gradio.app) - Web UI 框架

---

**版本：** 2.0
**更新日期：** 2026-02-10
