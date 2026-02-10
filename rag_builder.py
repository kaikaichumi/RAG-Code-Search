#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 知識庫建置工具 - 互動式版本
支援選擇特定資料夾或全部資料夾建立知識庫
"""

import os
import sys
import yaml
import shutil
from pathlib import Path
from typing import List, Dict
import chardet
from tqdm import tqdm
from langchain_community.document_loaders import TextLoader
from langchain_ollama import OllamaEmbeddings

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

from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)


class RAGBuilder:
    """RAG 知識庫建置器"""

    def __init__(self, config_path: str = "config.yaml"):
        """初始化建置器"""
        self.config = self.load_config(config_path)
        self.script_dir = Path(__file__).parent

    def load_config(self, config_path: str) -> dict:
        """載入設定檔"""
        config_file = Path(__file__).parent / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def detect_encoding(self, file_path: str) -> str:
        """自動偵測檔案編碼"""
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
            return result['encoding'] or 'utf-8'

    def get_available_directories(self, root_path: Path) -> List[str]:
        """取得專案根目錄下的所有子目錄"""
        if not root_path.exists():
            return []

        exclude_dirs = set(self.config['project'].get('exclude_dirs', []))
        dirs = []

        for item in root_path.iterdir():
            if item.is_dir() and item.name not in exclude_dirs:
                dirs.append(item.name)

        return sorted(dirs)

    def select_directories(self) -> List[str]:
        """互動式選擇要索引的資料夾"""
        root_path = Path(self.config['project']['root_path'])
        available_dirs = self.get_available_directories(root_path)

        if not available_dirs:
            print(Fore.RED + f"❌ 在 {root_path} 中找不到任何子目錄")
            sys.exit(1)

        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.CYAN + "選擇要建立索引的資料夾")
        print(Fore.CYAN + "=" * 70)
        print(f"\n專案根目錄: {root_path}\n")

        # 顯示可用的資料夾
        print(Fore.YELLOW + "可用的資料夾:")
        for i, dir_name in enumerate(available_dirs, 1):
            dir_path = root_path / dir_name
            # 計算檔案數量
            file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
            print(f"  {i}. {Fore.GREEN}{dir_name}{Style.RESET_ALL} ({file_count} 個檔案)")

        print(f"\n  {Fore.GREEN}0. 全部資料夾{Style.RESET_ALL}")
        print()

        # 取得使用者選擇
        while True:
            try:
                choice = input(Fore.YELLOW + "請選擇 (輸入數字，多個用逗號分隔，如 1,2,3 或 0 表示全部): ").strip()

                if not choice:
                    print(Fore.RED + "請輸入選項")
                    continue

                # 解析選擇
                choices = [c.strip() for c in choice.split(',')]
                selected_indices = []

                for c in choices:
                    if not c.isdigit():
                        print(Fore.RED + f"無效的輸入: {c}")
                        selected_indices = None
                        break

                    idx = int(c)
                    if idx < 0 or idx > len(available_dirs):
                        print(Fore.RED + f"數字超出範圍: {idx}")
                        selected_indices = None
                        break

                    selected_indices.append(idx)

                if selected_indices is None:
                    continue

                # 處理選擇
                if 0 in selected_indices:
                    # 選擇全部
                    selected_dirs = available_dirs
                    print(Fore.GREEN + f"\n✓ 已選擇全部 {len(selected_dirs)} 個資料夾")
                else:
                    # 選擇特定資料夾
                    selected_dirs = [available_dirs[i-1] for i in selected_indices]
                    print(Fore.GREEN + f"\n✓ 已選擇 {len(selected_dirs)} 個資料夾:")
                    for d in selected_dirs:
                        print(f"  - {d}")

                return selected_dirs

            except ValueError:
                print(Fore.RED + "請輸入有效的數字")
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n操作已取消")
                sys.exit(0)

    def scan_files(self, selected_dirs: List[str]) -> List[str]:
        """掃描選定資料夾中的檔案"""
        root_path = Path(self.config['project']['root_path'])
        exclude_dirs = set(self.config['project'].get('exclude_dirs', []))
        extensions = set(self.config['project']['file_extensions'])

        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.CYAN + "[1/4] 掃描專案檔案")
        print(Fore.CYAN + "=" * 70)
        print(f"\n專案根目錄: {root_path}")
        print(f"索引資料夾: {', '.join(selected_dirs)}")
        print(f"檔案類型: {', '.join(extensions)}\n")

        file_list = []

        for dir_name in selected_dirs:
            search_path = root_path / dir_name

            if not search_path.exists():
                print(Fore.YELLOW + f"  ⚠ 警告：目錄不存在 {search_path}")
                continue

            print(Fore.YELLOW + f"  掃描 {dir_name}...")

            for file_path in search_path.rglob('*'):
                # 檢查是否在排除目錄中
                if any(excl in file_path.parts for excl in exclude_dirs):
                    continue

                # 檢查副檔名
                if file_path.suffix in extensions:
                    file_list.append(str(file_path))

        # 統計各類型檔案數量
        ext_counts = {}
        dir_counts = {}

        for fp in file_list:
            path = Path(fp)
            ext = path.suffix
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

            # 找出所屬資料夾
            for dir_name in selected_dirs:
                if dir_name in path.parts:
                    dir_counts[dir_name] = dir_counts.get(dir_name, 0) + 1
                    break

        print(Fore.GREEN + f"\n✓ 共找到 {len(file_list)} 個檔案\n")

        # 按資料夾顯示統計
        print(Fore.CYAN + "各資料夾檔案數:")
        for dir_name in sorted(dir_counts.keys()):
            print(f"  {dir_name}: {dir_counts[dir_name]} 個")

        print(Fore.CYAN + "\n各類型檔案數:")
        for ext, count in sorted(ext_counts.items()):
            print(f"  {ext}: {count} 個")

        return file_list

    def load_documents(self, file_list: List[str], selected_dirs: List[str]) -> List[Document]:
        """載入檔案內容"""
        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.CYAN + "[2/4] 載入文件內容")
        print(Fore.CYAN + "=" * 70 + "\n")

        documents = []
        failed_files = []

        for file_path in tqdm(file_list, desc=Fore.YELLOW + "載入中"):
            try:
                encoding = self.detect_encoding(file_path)

                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()

                if not content.strip():
                    continue

                # 建立 Document 並附加 metadata
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": file_path,
                        "filename": os.path.basename(file_path),
                        "extension": Path(file_path).suffix,
                        "encoding": encoding,
                        "module": self._get_module_name(file_path, selected_dirs)
                    }
                )
                documents.append(doc)

            except Exception as e:
                failed_files.append((file_path, str(e)))

        print(Fore.GREEN + f"\n✓ 成功載入 {len(documents)} 個文件")

        if failed_files:
            print(Fore.YELLOW + f"⚠ 失敗 {len(failed_files)} 個文件")
            for fp, err in failed_files[:5]:
                print(f"  - {fp}: {err}")

        return documents

    def _get_module_name(self, file_path: str, selected_dirs: List[str]) -> str:
        """從檔案路徑提取模組名稱"""
        parts = Path(file_path).parts
        for module in selected_dirs:
            if module in parts:
                return module
        return "Unknown"

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """切割文件為片段"""
        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.CYAN + "[3/4] 切割文件片段")
        print(Fore.CYAN + "=" * 70 + "\n")

        chunk_size = self.config['chunking']['chunk_size']
        chunk_overlap = self.config['chunking']['chunk_overlap']

        print(f"片段大小: {chunk_size} 字元")
        print(f"重疊大小: {chunk_overlap} 字元\n")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n\n",
                "\nclass ",
                "\npublic ",
                "\nprivate ",
                "\nprotected ",
                "\n\n",
                "\n",
                " ",
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

        print(Fore.GREEN + f"✓ 切割成 {len(chunks)} 個片段")
        print(f"平均每份文件 {len(chunks)/len(documents):.1f} 個片段\n")

        print(Fore.CYAN + "各模組片段數:")
        for module, count in sorted(module_counts.items()):
            print(f"  {module}: {count} 個片段")

        return chunks

    def build_vectorstore(self, chunks: List[Document], selected_dirs: List[str]):
        """建立向量資料庫"""
        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.CYAN + "[4/4] 建立向量資料庫")
        print(Fore.CYAN + "=" * 70 + "\n")

        embedding_model = self.config['embedding']['model']
        print(f"Embedding 模型: {embedding_model}")
        print(f"Embedding API: {self.config['embedding']['base_url']}")
        print(Fore.YELLOW + f"\n正在向量化 {len(chunks)} 個片段...")
        print(Fore.YELLOW + "(使用 CPU 運算，請耐心等待)\n")

        embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=self.config['embedding']['base_url']
        )

        # 建立資料夾特定的資料庫名稱
        dirs_hash = "_".join(sorted(selected_dirs))
        persist_dir = self.script_dir / f"chroma_db_{dirs_hash}"

        # 如果資料庫已存在，詢問是否覆蓋
        if persist_dir.exists():
            print(Fore.YELLOW + f"⚠ 發現現有的向量資料庫: {persist_dir.name}")
            choice = input("是否覆蓋? (y/n): ").strip().lower()

            if choice == 'y':
                print(Fore.YELLOW + "正在清除舊資料...")
                shutil.rmtree(persist_dir)
            else:
                print(Fore.RED + "操作已取消")
                sys.exit(0)

        # 分批建立向量資料庫
        batch_size = 100
        vectorstore = None

        for i in tqdm(range(0, len(chunks), batch_size), desc=Fore.YELLOW + "建立中"):
            batch = chunks[i:i+batch_size]

            if vectorstore is None:
                # 第一批：建立新資料庫
                vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    persist_directory=str(persist_dir),
                    collection_name="knowledge_base"
                )
            else:
                # 後續批次：新增到現有資料庫
                vectorstore.add_documents(batch)

        # 計算資料庫大小
        db_size = sum(f.stat().st_size for f in persist_dir.rglob('*') if f.is_file()) / (1024 * 1024)

        print(Fore.GREEN + f"\n✓ 向量資料庫建立完成")
        print(f"儲存位置: {persist_dir}")
        print(f"資料庫大小: {db_size:.2f} MB")

        # 儲存索引資訊
        self._save_index_info(persist_dir, selected_dirs, len(chunks))

        return str(persist_dir)

    def _save_index_info(self, persist_dir: Path, selected_dirs: List[str], chunk_count: int):
        """儲存索引資訊"""
        info_file = persist_dir / "index_info.yaml"

        info = {
            'indexed_directories': selected_dirs,
            'chunk_count': chunk_count,
            'created_at': str(Path.cwd()),
            'config': {
                'chunk_size': self.config['chunking']['chunk_size'],
                'chunk_overlap': self.config['chunking']['chunk_overlap'],
                'embedding_model': self.config['embedding']['model']
            }
        }

        with open(info_file, 'w', encoding='utf-8') as f:
            yaml.dump(info, f, allow_unicode=True)

    def build(self):
        """執行完整的建置流程"""
        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.CYAN + "RAG 知識庫建置工具")
        print(Fore.CYAN + "=" * 70)

        try:
            # 1. 選擇資料夾
            selected_dirs = self.select_directories()

            # 2. 掃描檔案
            file_list = self.scan_files(selected_dirs)

            if not file_list:
                print(Fore.RED + "\n❌ 沒有找到任何檔案")
                return

            # 3. 載入文件
            documents = self.load_documents(file_list, selected_dirs)

            if not documents:
                print(Fore.RED + "\n❌ 沒有成功載入任何文件")
                return

            # 4. 切割文件
            chunks = self.split_documents(documents)

            # 5. 建立向量資料庫
            db_path = self.build_vectorstore(chunks, selected_dirs)

            print(Fore.CYAN + "\n" + "=" * 70)
            print(Fore.GREEN + "✅ 知識庫建置完成!")
            print(Fore.CYAN + "=" * 70)
            print(f"\n資料庫路徑: {db_path}")
            print("\n下一步:")
            print("  1. 使用 rag_query.py 進行命令列查詢")
            print("  2. 使用 rag_web_ui.py 啟動網頁介面\n")

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\n操作已取消")
            sys.exit(0)
        except Exception as e:
            print(Fore.RED + f"\n❌ 建置失敗: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主程式入口"""
    # 切換到腳本所在目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    builder = RAGBuilder()
    builder.build()


if __name__ == "__main__":
    main()
