#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HMRV RAG 查詢工具（Web UI 版）
用途：提供友善的網頁介面查詢專案程式碼和文件
"""

import os
import sys
import yaml
import gradio as gr
from typing import List, Tuple
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

# 全域變數
qa_chain = None
config = None

def load_config(config_path: str = "config.yaml") -> dict:
    """載入設定檔"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def format_sources(source_docs) -> str:
    """格式化來源文件為 HTML"""
    if not source_docs:
        return ""

    html = "<div style='margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-radius: 8px;'>"
    html += "<h3 style='color: #1976d2; margin-top: 0;'>📁 相關檔案來源</h3>"
    html += "<ul style='list-style-type: none; padding-left: 0;'>"

    seen_sources = set()
    for i, doc in enumerate(source_docs, 1):
        source = doc.metadata.get('source', 'Unknown')
        module = doc.metadata.get('module', 'Unknown')

        if source not in seen_sources:
            seen_sources.add(source)
            # 簡化路徑顯示
            display_source = source.replace('\\', '/')
            if 'HM_original/' in display_source:
                display_source = display_source.split('HM_original/')[1]

            html += f"<li style='margin: 8px 0;'>"
            html += f"<span style='background-color: #4caf50; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; margin-right: 8px;'>{module}</span>"
            html += f"<code style='background-color: #e0e0e0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em;'>{display_source}</code>"
            html += "</li>"

    html += "</ul></div>"
    return html

def setup_rag_chain():
    """初始化 RAG Chain"""
    global config

    # 載入設定
    config = load_config()

    # 載入向量資料庫
    persist_dir = config['vectorstore']['persist_directory']
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(f"找不到向量資料庫：{persist_dir}\n請先執行 build_knowledge_base.py")

    embeddings = OllamaEmbeddings(
        model=config['embedding']['model'],
        base_url=config['embedding']['base_url']
    )

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name="hmrv_knowledge_base"
    )

    # 設定 LLM
    llm = ChatOpenAI(
        base_url=config['llm']['base_url'],
        api_key=config['llm'].get('api_key', 'not-needed'),
        model=config['llm']['model'],
        temperature=config['llm']['temperature'],
        max_tokens=config['llm']['max_tokens']
    )

    # 提示詞模板
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
6. 使用 Markdown 格式讓回答更易讀

【回答】：""",
        input_variables=["context", "question"]
    )

    # 建立 QA Chain
    search_top_k = config['vectorstore']['search_top_k']
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": search_top_k}
        ),
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=True
    )

    return chain

def query_rag(question: str, history: List[Tuple[str, str]]) -> Tuple[str, str]:
    """
    處理使用者查詢
    回傳：(回答, 來源文件 HTML)
    """
    if not question.strip():
        return "請輸入問題", ""

    try:
        # 執行查詢
        result = qa_chain.invoke({"query": question})

        # 取得回答
        answer = result['result']

        # 格式化來源文件
        sources_html = format_sources(result.get('source_documents', []))

        return answer, sources_html

    except Exception as e:
        error_msg = f"""### ❌ 查詢失敗

**錯誤訊息：** {str(e)}

**請檢查：**
1. 區網 LLM API 是否正常運作（{config['llm']['base_url']}）
2. config.yaml 中的 API 位址是否正確
3. 網路連線是否正常
4. Ollama 服務是否正在執行
"""
        return error_msg, ""

def create_ui():
    """建立 Gradio UI"""

    # 範例問題
    examples = [
        ["病歷審查的抽樣邏輯在哪裡？"],
        ["如何新增一個審查類別？"],
        ["LDAP 認證的流程是什麼？"],
        ["DB2 連線設定在哪個檔案？"],
        ["如何修改審查結果的計算方式？"],
        ["Spring MVC Controller 在哪裡？"],
        ["batch 批次處理的主要功能是什麼？"],
        ["報表產生的邏輯在哪裡？"],
    ]

    # 自訂 CSS
    custom_css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    .source-box {
        margin-top: 10px;
    }
    """

    with gr.Blocks(
        title="HMRV RAG 智慧查詢系統",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as demo:
        gr.Markdown("""
        # 🏥 HMRV RAG 智慧查詢系統

        透過自然語言查詢病歷審查系統的程式碼、文件、設定資訊。

        **提示：** 查詢時會自動搜尋最相關的程式碼片段，並由 AI 整合回答。
        """)

        with gr.Row():
            with gr.Column(scale=2):
                # 問題輸入區
                question_box = gr.Textbox(
                    label="🤔 輸入你的問題",
                    placeholder="例如：病歷審查的抽樣邏輯在哪裡？",
                    lines=2
                )

                with gr.Row():
                    submit_btn = gr.Button("🔍 查詢", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ 清除", size="lg")

            with gr.Column(scale=1):
                # 系統資訊
                gr.Markdown(f"""
                ### ⚙️ 系統資訊

                **Embedding 模型：** {config['embedding']['model']}
                **LLM 模型：** {config['llm']['model']}
                **搜尋相關片段數：** {config['vectorstore']['search_top_k']}
                """)

        # 範例問題
        gr.Markdown("### 💡 範例問題（點擊直接查詢）")
        gr.Examples(
            examples=examples,
            inputs=question_box,
            label=None
        )

        # 回答顯示區
        gr.Markdown("---")
        gr.Markdown("### 📝 查詢結果")

        answer_box = gr.Markdown(
            label="AI 回答",
            value="等待查詢..."
        )

        sources_box = gr.HTML(
            label="相關檔案來源",
            value=""
        )

        # 事件處理
        def handle_query(question):
            answer, sources = query_rag(question, [])
            return answer, sources

        submit_btn.click(
            fn=handle_query,
            inputs=[question_box],
            outputs=[answer_box, sources_box]
        )

        question_box.submit(
            fn=handle_query,
            inputs=[question_box],
            outputs=[answer_box, sources_box]
        )

        clear_btn.click(
            fn=lambda: ("", "等待查詢...", ""),
            outputs=[question_box, answer_box, sources_box]
        )

        gr.Markdown("""
        ---
        <div style='text-align: center; color: #666; font-size: 0.9em;'>
        HMRV RAG 智慧查詢系統 v1.0 | 由 Claude Code 協助建立
        </div>
        """)

    return demo

def main():
    """主程式"""
    global qa_chain

    # 切換到腳本所在目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 60)
    print("HMRV RAG 智慧查詢系統 (Web UI)")
    print("=" * 60)
    print()

    try:
        # 初始化 RAG Chain
        print("⚙️  初始化 RAG 系統...")
        qa_chain = setup_rag_chain()
        print("✓ 初始化完成")
        print()

        # 建立並啟動 UI
        print("🚀 啟動 Web UI...")
        demo = create_ui()

        # 啟動伺服器
        demo.launch(
            server_name=config['web_ui']['host'],
            server_port=config['web_ui']['port'],
            share=config['web_ui']['share'],
            inbrowser=True  # 自動開啟瀏覽器
        )

    except FileNotFoundError as e:
        print(f"❌ 錯誤：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 啟動失敗：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
