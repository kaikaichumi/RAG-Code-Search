#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HMRV RAG 知識庫建置腳本
用途：掃描專案原始碼、文件，建立向量資料庫供 RAG 查詢使用
"""

import os
import sys
import yaml
from pathlib import Path
from typing import List
import chardet
from tqdm import tqdm
from langchain_community.document_loaders import TextLoader
from langchain_ollama import OllamaEmbeddings

# 新版 LangChain 的模組位置
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.docstore.document import Document

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

# 載入設定檔
def load_config(config_path: str = "config.yaml") -> dict:
    """載入 YAML 設定檔"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 自動偵測檔案編碼
def detect_encoding(file_path: str) -> str:
    """自動偵測檔案編碼"""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
        return result['encoding'] or 'utf-8'

# 掃描專案檔案
def scan_project_files(config: dict) -> List[str]:
    """
    掃描專案目錄，回傳符合條件的檔案清單
    """
    root_path = Path(config['project']['root_path'])
    include_dirs = config['project'].get('include_dirs', [])
    exclude_dirs = set(config['project'].get('exclude_dirs', []))
    extensions = set(config['project']['file_extensions'])

    print(f"[1/4] 掃描專案目錄：{root_path}")
    print(f"      包含模組：{', '.join(include_dirs) if include_dirs else '全部'}")
    print(f"      檔案類型：{', '.join(extensions)}")

    file_list = []

    # 如果指定了 include_dirs，只掃描這些子目錄
    if include_dirs:
        search_paths = [root_path / dir_name for dir_name in include_dirs]
    else:
        search_paths = [root_path]

    for search_path in search_paths:
        if not search_path.exists():
            print(f"      警告：目錄不存在 {search_path}")
            continue

        for file_path in search_path.rglob('*'):
            # 檢查是否在排除目錄中
            if any(excl in file_path.parts for excl in exclude_dirs):
                continue

            # 檢查副檔名
            if file_path.suffix in extensions:
                file_list.append(str(file_path))

    # 統計各類型檔案數量
    ext_counts = {}
    for fp in file_list:
        ext = Path(fp).suffix
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    print(f"      ✓ 找到 {len(file_list)} 個檔案")
    for ext, count in sorted(ext_counts.items()):
        print(f"        {ext}: {count} 個")

    return file_list

# 載入文件
def load_documents(file_list: List[str]) -> List[Document]:
    """
    載入所有檔案內容，自動偵測編碼
    """
    print(f"\n[2/4] 載入文件內容...")
    documents = []
    failed_files = []

    for file_path in tqdm(file_list, desc="      載入中"):
        try:
            # 偵測編碼
            encoding = detect_encoding(file_path)

            # 讀取檔案
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()

            # 跳過空檔案
            if not content.strip():
                continue

            # 建立 Document 物件，附加 metadata
            doc = Document(
                page_content=content,
                metadata={
                    "source": file_path,
                    "filename": os.path.basename(file_path),
                    "extension": Path(file_path).suffix,
                    "encoding": encoding,
                    "module": _get_module_name(file_path)
                }
            )
            documents.append(doc)

        except Exception as e:
            failed_files.append((file_path, str(e)))

    print(f"      ✓ 成功載入 {len(documents)} 個文件")
    if failed_files:
        print(f"      ⚠ 失敗 {len(failed_files)} 個文件")
        for fp, err in failed_files[:5]:  # 只顯示前 5 個錯誤
            print(f"        - {fp}: {err}")

    return documents

def _get_module_name(file_path: str) -> str:
    """從檔案路徑提取模組名稱"""
    parts = Path(file_path).parts
    modules = ['HMRV', 'HMRVBatch', 'HMRVStatements', 'SharedCodes']
    for module in modules:
        if module in parts:
            return module
    return "Unknown"

# 切割文件
def split_documents(documents: List[Document], config: dict) -> List[Document]:
    """
    將大文件切割成小片段 (chunks)
    """
    print(f"\n[3/4] 切割文件片段...")

    chunk_size = config['chunking']['chunk_size']
    chunk_overlap = config['chunking']['chunk_overlap']

    # 針對不同檔案類型使用不同的切割策略
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n\n",           # 多個空行
            "\nclass ",          # Java class 定義
            "\npublic ",         # public 方法
            "\nprivate ",        # private 方法
            "\nprotected ",      # protected 方法
            "\n\n",              # 段落
            "\n",                # 單行
            " ",                 # 空格
            ""
        ],
        length_function=len,
    )

    chunks = splitter.split_documents(documents)

    # 統計各模組的 chunk 數量
    module_counts = {}
    for chunk in chunks:
        module = chunk.metadata.get('module', 'Unknown')
        module_counts[module] = module_counts.get(module, 0) + 1

    print(f"      ✓ 切割成 {len(chunks)} 個片段")
    print(f"      平均每份文件 {len(chunks)/len(documents):.1f} 個片段")
    for module, count in sorted(module_counts.items()):
        print(f"        {module}: {count} 個片段")

    return chunks

# 建立向量資料庫
def build_vectorstore(chunks: List[Document], config: dict):
    """
    使用 Embedding 模型建立向量資料庫
    """
    print(f"\n[4/4] 建立向量資料庫...")

    # 初始化 Embedding 模型（本機 Ollama）
    embedding_model = config['embedding']['model']
    print(f"      使用 Embedding 模型：{embedding_model}")
    print(f"      ⏳ 正在向量化 {len(chunks)} 個片段（CPU 較慢，請耐心等待）...")

    embeddings = OllamaEmbeddings(
        model=embedding_model,
        base_url=config['embedding']['base_url']
    )

    # 建立 ChromaDB（會自動批次處理 embedding）
    persist_dir = config['vectorstore']['persist_directory']

    # 如果資料庫已存在，先刪除
    if os.path.exists(persist_dir):
        print(f"      發現舊的向量資料庫，正在清除...")
        import shutil
        shutil.rmtree(persist_dir)

    # 分批建立向量資料庫（避免記憶體不足）
    batch_size = 100
    vectorstore = None

    for i in tqdm(range(0, len(chunks), batch_size), desc="      建立中"):
        batch = chunks[i:i+batch_size]

        if vectorstore is None:
            # 第一批：建立新資料庫
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=persist_dir,
                collection_name="hmrv_knowledge_base"
            )
        else:
            # 後續批次：新增到現有資料庫
            vectorstore.add_documents(batch)

    print(f"      ✓ 向量資料庫建立完成")
    print(f"      儲存位置：{os.path.abspath(persist_dir)}")
    print(f"      資料庫大小：{_get_dir_size(persist_dir):.2f} MB")

def _get_dir_size(path: str) -> float:
    """計算目錄大小 (MB)"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)

# 主程式
def main():
    print("=" * 60)
    print("HMRV RAG 知識庫建置工具")
    print("=" * 60)
    print()

    # 切換到腳本所在目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    try:
        # 載入設定
        config = load_config()

        # 掃描檔案
        file_list = scan_project_files(config)
        if not file_list:
            print("❌ 沒有找到任何檔案！請檢查 config.yaml 設定")
            return

        # 載入文件
        documents = load_documents(file_list)
        if not documents:
            print("❌ 沒有成功載入任何文件！")
            return

        # 切割文件
        chunks = split_documents(documents, config)

        # 建立向量資料庫
        build_vectorstore(chunks, config)

        print()
        print("=" * 60)
        print("✅ 知識庫建置完成！")
        print("=" * 60)
        print()
        print("下一步：")
        print("  1. 執行 query.py 開始命令列查詢")
        print("  2. 執行 web_ui.py 開啟網頁介面")
        print()

    except FileNotFoundError as e:
        print(f"❌ 錯誤：找不到檔案 - {e}")
        print("   請確認 config.yaml 是否存在")
    except Exception as e:
        print(f"❌ 建置失敗：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
