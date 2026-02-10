#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 查詢工具 - Web UI 版本
使用 Gradio 提供友善的網頁介面
"""

import os
import sys
import yaml
from pathlib import Path
from typing import List, Tuple
import gradio as gr
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


class RAGWebUI:
    """RAG Web UI 工具"""

    def __init__(self, config_path: str = "config.yaml"):
        """初始化 Web UI"""
        self.script_dir = Path(__file__).parent
        self.config = self.load_config(config_path)
        self.qa_chains = {}  # 儲存多個資料庫的 QA Chain

    def load_config(self, config_path: str) -> dict:
        """載入設定檔"""
        config_file = self.script_dir / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def list_databases(self) -> List[Tuple[str, Path]]:
        """列出所有可用的向量資料庫"""
        dbs = []
        for item in self.script_dir.iterdir():
            if item.is_dir() and item.name.startswith('chroma_db_'):
                # 讀取索引資訊
                info_file = item / "index_info.yaml"
                if info_file.exists():
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = yaml.safe_load(f)
                        dirs = ', '.join(info.get('indexed_directories', []))
                        label = f"{item.name} ({dirs})"
                else:
                    label = item.name

                dbs.append((label, item))

        return sorted(dbs, key=lambda x: x[0])

    def setup_qa_chain(self, db_path: Path):
        """設定 RAG Chain"""
        if str(db_path) in self.qa_chains:
            return self.qa_chains[str(db_path)]

        # 1. 載入向量資料庫
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
        llm = ChatOpenAI(
            base_url=self.config['llm']['base_url'],
            api_key=self.config['llm'].get('api_key', 'not-needed'),
            model=self.config['llm']['model'],
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
6. 使用 Markdown 格式輸出，讓內容更清晰易讀

【回答】：""",
            input_variables=["context", "question"]
        )

        # 4. 建立 QA Chain
        search_top_k = self.config['vectorstore']['search_top_k']
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": search_top_k}
            ),
            chain_type_kwargs={"prompt": prompt_template},
            return_source_documents=True
        )

        # 快取 QA Chain
        self.qa_chains[str(db_path)] = qa_chain
        return qa_chain

    def format_sources(self, source_docs) -> str:
        """格式化來源文件"""
        if not source_docs:
            return "無相關來源"

        sources_md = "### 📁 相關檔案來源\n\n"
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

                sources_md += f"{i}. **[{module}]** `{display_source}`\n"

        return sources_md

    def query(self, question: str, db_choice: str) -> Tuple[str, str]:
        """執行查詢"""
        if not question.strip():
            return "請輸入問題", ""

        try:
            # 找到選擇的資料庫
            databases = self.list_databases()
            selected_db = None

            for label, db_path in databases:
                if label == db_choice:
                    selected_db = db_path
                    break

            if selected_db is None:
                return "❌ 找不到選擇的資料庫", ""

            # 設定 QA Chain
            qa_chain = self.setup_qa_chain(selected_db)

            # 執行查詢
            result = qa_chain.invoke({"query": question})

            # 格式化回答
            answer = result['result']

            # 格式化來源
            sources = ""
            if 'source_documents' in result and result['source_documents']:
                sources = self.format_sources(result['source_documents'])

            return answer, sources

        except Exception as e:
            error_msg = f"""❌ 查詢失敗

**錯誤訊息:** {str(e)}

**請檢查:**
1. LLM API 是否正常運作
2. config.yaml 中的 API 位址是否正確
3. 網路連線是否正常
4. Ollama 服務是否正在執行
"""
            return error_msg, ""

    def create_interface(self):
        """建立 Gradio 介面"""
        databases = self.list_databases()

        if not databases:
            print("❌ 找不到任何向量資料庫")
            print("   請先執行 rag_builder.py 建立知識庫")
            sys.exit(1)

        # 預設選擇第一個資料庫
        db_choices = [label for label, _ in databases]
        default_db = db_choices[0] if db_choices else None

        # 建立介面
        with gr.Blocks(
            title="RAG 智慧查詢系統",
            theme=gr.themes.Soft()
        ) as demo:
            gr.Markdown("# 🔍 RAG 智慧查詢系統")
            gr.Markdown("透過自然語言查詢程式碼和文件")

            with gr.Row():
                with gr.Column(scale=3):
                    db_selector = gr.Dropdown(
                        choices=db_choices,
                        value=default_db,
                        label="選擇知識庫",
                        info="選擇要查詢的向量資料庫"
                    )

            with gr.Row():
                with gr.Column():
                    question_input = gr.Textbox(
                        label="輸入問題",
                        placeholder="例如：這個專案的主要功能是什麼？",
                        lines=3
                    )

                    with gr.Row():
                        submit_btn = gr.Button("🔍 查詢", variant="primary", scale=2)
                        clear_btn = gr.Button("🗑️ 清除", scale=1)

            with gr.Row():
                with gr.Column():
                    answer_output = gr.Markdown(
                        label="回答",
                        value="在此顯示查詢結果..."
                    )

            with gr.Row():
                with gr.Column():
                    sources_output = gr.Markdown(
                        label="相關來源",
                        value=""
                    )

            # 範例問題
            gr.Markdown("### 💡 範例問題")
            gr.Examples(
                examples=[
                    ["這個專案的主要功能是什麼？"],
                    ["認證的流程是什麼？"],
                    ["資料庫連線設定在哪個檔案？"],
                    ["Controller 在哪裡？"],
                    ["如何新增一個新功能？"],
                ],
                inputs=question_input
            )

            # 事件處理
            submit_btn.click(
                fn=self.query,
                inputs=[question_input, db_selector],
                outputs=[answer_output, sources_output]
            )

            clear_btn.click(
                fn=lambda: ("", "在此顯示查詢結果...", ""),
                outputs=[question_input, answer_output, sources_output]
            )

        return demo

    def launch(self):
        """啟動 Web UI"""
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        print("=" * 70)
        print("RAG 智慧查詢系統 - Web UI")
        print("=" * 70)
        print()

        try:
            demo = self.create_interface()

            # 啟動服務
            host = self.config['web_ui']['host']
            port = self.config['web_ui']['port']
            share = self.config['web_ui'].get('share', False)

            print(f"⚙️  啟動 Web 服務...")
            print(f"   主機: {host}")
            print(f"   埠口: {port}")
            print()

            demo.launch(
                server_name=host,
                server_port=port,
                share=share,
                show_error=True
            )

        except Exception as e:
            print(f"❌ 啟動失敗: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主程式入口"""
    web_ui = RAGWebUI()
    web_ui.launch()


if __name__ == "__main__":
    main()
