#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 查詢工具 - 命令列版本
支援從建立的知識庫中查詢資訊
"""

import os
import sys
import yaml
from pathlib import Path
from typing import List
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

try:
    from langchain_classic.chains import RetrievalQA
except ImportError:
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains.retrieval import create_retrieval_chain
    RetrievalQA = None

from langchain_core.prompts import PromptTemplate
from colorama import init, Fore, Style

init(autoreset=True)


class RAGQuery:
    """RAG 查詢工具"""

    def __init__(self, config_path: str = "config.yaml"):
        """初始化查詢工具"""
        self.script_dir = Path(__file__).parent
        self.config = self.load_config(config_path)
        self.qa_chain = None

    def load_config(self, config_path: str) -> dict:
        """載入設定檔"""
        config_file = self.script_dir / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def list_databases(self) -> List[Path]:
        """列出所有可用的向量資料庫"""
        dbs = []
        for item in self.script_dir.iterdir():
            if item.is_dir() and item.name.startswith('chroma_db_'):
                dbs.append(item)
        return sorted(dbs)

    def select_database(self) -> Path:
        """選擇要查詢的資料庫"""
        databases = self.list_databases()

        if not databases:
            print(Fore.RED + "❌ 找不到任何向量資料庫")
            print(Fore.YELLOW + "   請先執行 rag_builder.py 建立知識庫")
            sys.exit(1)

        if len(databases) == 1:
            # 只有一個資料庫，直接使用
            db = databases[0]
            print(Fore.GREEN + f"✓ 使用資料庫: {db.name}\n")
            return db

        # 多個資料庫，讓使用者選擇
        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.CYAN + "選擇要查詢的知識庫")
        print(Fore.CYAN + "=" * 70 + "\n")

        for i, db in enumerate(databases, 1):
            # 讀取索引資訊
            info_file = db / "index_info.yaml"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = yaml.safe_load(f)
                    dirs = ', '.join(info.get('indexed_directories', []))
                    chunks = info.get('chunk_count', 0)
                    print(f"  {i}. {Fore.GREEN}{db.name}{Style.RESET_ALL}")
                    print(f"     資料夾: {dirs}")
                    print(f"     片段數: {chunks}")
            else:
                print(f"  {i}. {Fore.GREEN}{db.name}{Style.RESET_ALL}")

        print()

        while True:
            try:
                choice = input(Fore.YELLOW + "請選擇 (輸入數字): ").strip()

                if not choice.isdigit():
                    print(Fore.RED + "請輸入有效的數字")
                    continue

                idx = int(choice)
                if idx < 1 or idx > len(databases):
                    print(Fore.RED + f"數字超出範圍 (1-{len(databases)})")
                    continue

                return databases[idx - 1]

            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n操作已取消")
                sys.exit(0)

    def setup_qa_chain(self, db_path: Path):
        """設定 RAG Chain"""
        print(Fore.YELLOW + "⚙️  初始化 RAG 系統...\n")

        # 1. 載入向量資料庫
        print(f"   載入向量資料庫: {db_path.name}")
        embeddings = OllamaEmbeddings(
            model=self.config['embedding']['model'],
            base_url=self.config['embedding']['base_url']
        )

        vectorstore = Chroma(
            persist_directory=str(db_path),
            embedding_function=embeddings,
            collection_name="knowledge_base"
        )

        # 2. 設定 LLM
        llm_base_url = self.config['llm']['base_url']
        llm_model = self.config['llm']['model']
        print(f"   連接 LLM API: {llm_base_url}")
        print(f"   使用模型: {llm_model}")

        llm = ChatOpenAI(
            base_url=llm_base_url,
            api_key=self.config['llm'].get('api_key', 'not-needed'),
            model=llm_model,
            temperature=self.config['llm']['temperature'],
            max_tokens=self.config['llm']['max_tokens']
        )

        # 3. 設定提示詞模板
        prompt_template = PromptTemplate(
            template="""你是一位資深的軟體工程師，精通各種程式語言和系統架構。

請根據以下程式碼片段和文件，回答使用者的問題。

【相關程式碼片段】
{context}

【使用者問題】
{question}

【回答要求】
1. 用繁體中文回答
2. 明確指出相關的檔案路徑和行數（如果有）
3. 如果涉及程式碼，請說明關鍵邏輯
4. 如果涉及資料庫，請說明相關的 Table 和欄位
5. 如果問題無法從片段中找到答案，請誠實告知

【回答】：""",
            input_variables=["context", "question"]
        )

        # 4. 建立 QA Chain
        search_top_k = self.config['vectorstore']['search_top_k']
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": search_top_k}
            ),
            chain_type_kwargs={"prompt": prompt_template},
            return_source_documents=True
        )

        print(Fore.GREEN + "   ✓ 初始化完成\n")

    def print_sources(self, source_docs):
        """顯示來源文件"""
        print(Fore.YELLOW + "\n📁 相關檔案來源:")
        seen_sources = set()

        for i, doc in enumerate(source_docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            module = doc.metadata.get('module', 'Unknown')

            if source not in seen_sources:
                seen_sources.add(source)
                # 簡化路徑顯示
                display_source = source.replace('\\', '/')
                parts = display_source.split('/')
                if len(parts) > 3:
                    display_source = '/'.join(parts[-3:])

                print(f"  {i}. [{Fore.GREEN}{module}{Style.RESET_ALL}] {display_source}")

    def print_help(self):
        """顯示說明"""
        print(Fore.CYAN + "\n📖 使用說明:")
        print("  - 直接輸入問題，按 Enter 查詢")
        print("  - 輸入 'help' 顯示此說明")
        print("  - 輸入 'clear' 清空螢幕")
        print("  - 輸入 'q' 或 'quit' 或 'exit' 離開")
        print()
        print(Fore.CYAN + "💡 範例問題:")
        print("  - 這個專案的主要功能是什麼？")
        print("  - 認證的流程是什麼？")
        print("  - 資料庫連線設定在哪個檔案？")
        print("  - Controller 在哪裡？")
        print("  - 如何新增一個新功能？")
        print()

    def query_loop(self):
        """互動式查詢迴圈"""
        self.print_help()

        while True:
            print(Fore.GREEN + "🤔 你的問題: ", end="")
            question = input().strip()

            # 處理指令
            if not question:
                continue
            if question.lower() in ['q', 'quit', 'exit']:
                print(Fore.CYAN + "\n👋 再見!")
                break
            if question.lower() == 'help':
                self.print_help()
                continue
            if question.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                self.print_header()
                continue

            # 查詢
            print(Fore.YELLOW + "\n🔍 搜尋中...")
            try:
                result = self.qa_chain.invoke({"query": question})

                # 顯示回答
                print(Fore.CYAN + "\n" + "=" * 70)
                print(Fore.WHITE + result['result'])
                print(Fore.CYAN + "=" * 70)

                # 顯示來源
                if 'source_documents' in result and result['source_documents']:
                    self.print_sources(result['source_documents'])

                print()

            except Exception as e:
                print(Fore.RED + f"\n❌ 查詢失敗: {e}")
                print(Fore.YELLOW + "   請檢查:")
                print("   1. LLM API 是否正常運作")
                print("   2. config.yaml 中的 API 位址是否正確")
                print("   3. 網路連線是否正常")
                print()

    def print_header(self):
        """顯示標題"""
        print(Fore.CYAN + "=" * 70)
        print(Fore.CYAN + "RAG 智慧查詢系統 (命令列版)")
        print(Fore.CYAN + "=" * 70)
        print()

    def run(self):
        """執行查詢工具"""
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        self.print_header()

        try:
            # 選擇資料庫
            db_path = self.select_database()

            # 設定 QA Chain
            self.setup_qa_chain(db_path)

            # 開始查詢
            self.query_loop()

        except FileNotFoundError:
            print(Fore.RED + "❌ 找不到 config.yaml，請確認檔案存在")
            sys.exit(1)
        except Exception as e:
            print(Fore.RED + f"❌ 啟動失敗: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主程式入口"""
    query_tool = RAGQuery()
    query_tool.run()


if __name__ == "__main__":
    main()
