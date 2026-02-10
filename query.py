#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HMRV RAG 查詢工具（命令列版）
用途：透過自然語言查詢專案程式碼和文件
"""

import os
import sys
import yaml
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI

# 嘗試使用新版 langchain_chroma，如果沒有則用舊版
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
# 從 langchain-classic 導入 RetrievalQA
try:
    from langchain_classic.chains import RetrievalQA
except ImportError:
    # 如果沒有 langchain-classic，使用新版 API
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains.retrieval import create_retrieval_chain
    RetrievalQA = None  # 標記使用新 API

from langchain_core.prompts import PromptTemplate
from colorama import init, Fore, Style

# 初始化 colorama（Windows 終端支援顏色）
init(autoreset=True)

def load_config(config_path: str = "config.yaml") -> dict:
    """載入設定檔"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def print_header():
    """顯示標題"""
    print(Fore.CYAN + "=" * 70)
    print(Fore.CYAN + "HMRV RAG 智慧查詢系統 (命令列版)")
    print(Fore.CYAN + "=" * 70)
    print()

def print_sources(source_docs):
    """顯示來源文件"""
    print(Fore.YELLOW + "\n📁 相關檔案來源：")
    seen_sources = set()
    for i, doc in enumerate(source_docs, 1):
        source = doc.metadata.get('source', 'Unknown')
        module = doc.metadata.get('module', 'Unknown')

        # 避免重複顯示相同檔案
        if source not in seen_sources:
            seen_sources.add(source)
            # 只顯示相對路徑的後半段，更易讀
            display_source = source.replace('\\', '/')
            if 'HM_original/' in display_source:
                display_source = display_source.split('HM_original/')[1]

            print(f"  {i}. [{Fore.GREEN}{module}{Style.RESET_ALL}] {display_source}")

def setup_rag_chain(config: dict):
    """設定 RAG Chain"""
    print(Fore.YELLOW + "⚙️  初始化 RAG 系統...")

    # 1. 載入向量資料庫
    persist_dir = config['vectorstore']['persist_directory']
    if not os.path.exists(persist_dir):
        print(Fore.RED + f"❌ 找不到向量資料庫：{persist_dir}")
        print(Fore.RED + "   請先執行 build_knowledge_base.py 建立知識庫")
        sys.exit(1)

    print(f"   載入向量資料庫：{persist_dir}")
    embeddings = OllamaEmbeddings(
        model=config['embedding']['model'],
        base_url=config['embedding']['base_url']
    )

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name="hmrv_knowledge_base"
    )

    # 2. 設定 LLM（區網 API）
    llm_base_url = config['llm']['base_url']
    llm_model = config['llm']['model']
    print(f"   連接 LLM API：{llm_base_url}")
    print(f"   使用模型：{llm_model}")

    llm = ChatOpenAI(
        base_url=llm_base_url,
        api_key=config['llm'].get('api_key', 'not-needed'),
        model=llm_model,
        temperature=config['llm']['temperature'],
        max_tokens=config['llm']['max_tokens']
    )

    # 3. 設定提示詞模板
    prompt_template = PromptTemplate(
        template="""你是一位資深的 HMRV 病歷審查系統工程師，精通 Java、Spring MVC、JSP、DB2 資料庫。

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
    search_top_k = config['vectorstore']['search_top_k']
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": search_top_k}
        ),
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=True  # 回傳來源文件
    )

    print(Fore.GREEN + "   ✓ 初始化完成")
    print()
    return qa_chain

def print_help():
    """顯示說明"""
    print(Fore.CYAN + "\n📖 使用說明：")
    print("  - 直接輸入問題，按 Enter 查詢")
    print("  - 輸入 'help' 顯示此說明")
    print("  - 輸入 'clear' 清空螢幕")
    print("  - 輸入 'q' 或 'quit' 或 'exit' 離開")
    print()
    print(Fore.CYAN + "💡 範例問題：")
    print("  - 病歷審查的抽樣邏輯在哪裡？")
    print("  - 如何新增一個審查類別？")
    print("  - LDAP 認證的流程是什麼？")
    print("  - DB2 連線設定在哪個檔案？")
    print("  - 如何修改審查結果的計算方式？")
    print("  - Spring MVC Controller 在哪裡？")
    print()

def main():
    """主程式"""
    # 切換到腳本所在目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print_header()

    try:
        # 載入設定
        config = load_config()

        # 初始化 RAG Chain
        qa_chain = setup_rag_chain(config)

        # 顯示說明
        print_help()

        # 互動式查詢迴圈
        while True:
            # 輸入問題
            print(Fore.GREEN + "🤔 你的問題：", end="")
            question = input().strip()

            # 處理指令
            if not question:
                continue
            if question.lower() in ['q', 'quit', 'exit']:
                print(Fore.CYAN + "\n👋 再見！")
                break
            if question.lower() == 'help':
                print_help()
                continue
            if question.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                print_header()
                continue

            # 查詢
            print(Fore.YELLOW + "\n🔍 搜尋中...")
            try:
                result = qa_chain.invoke({"query": question})

                # 顯示回答
                print(Fore.CYAN + "\n" + "=" * 70)
                print(Fore.WHITE + result['result'])
                print(Fore.CYAN + "=" * 70)

                # 顯示來源
                if 'source_documents' in result and result['source_documents']:
                    print_sources(result['source_documents'])

                print()

            except Exception as e:
                print(Fore.RED + f"\n❌ 查詢失敗：{e}")
                print(Fore.YELLOW + "   請檢查：")
                print("   1. 區網 LLM API 是否正常運作")
                print("   2. config.yaml 中的 API 位址是否正確")
                print("   3. 網路連線是否正常")
                print()

    except FileNotFoundError:
        print(Fore.RED + "❌ 找不到 config.yaml，請確認檔案存在")
        sys.exit(1)
    except Exception as e:
        print(Fore.RED + f"❌ 啟動失敗：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
