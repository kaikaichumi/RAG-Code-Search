#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generic RAG Web UI for local codebase search.
This version is project-agnostic and reads project context from config.yaml.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

import gradio as gr
import yaml
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

try:
    from langchain_classic.chains import RetrievalQA
except ImportError:
    from langchain.chains import RetrievalQA


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def to_display_path(source_path: str, project_root: str) -> str:
    """
    Convert absolute source path to a readable relative path.
    Falls back to normalized absolute path if relpath fails.
    """
    source_norm = source_path.replace("\\", "/")
    root_norm = project_root.replace("\\", "/")
    try:
        rel = os.path.relpath(source_norm, root_norm).replace("\\", "/")
        if not rel.startswith(".."):
            return rel
    except Exception:
        pass
    return source_norm


def format_sources(source_docs, project_root: str) -> str:
    if not source_docs:
        return ""

    html = "<div style='margin-top:20px;padding:15px;background:#f5f5f5;border-radius:8px;'>"
    html += "<h3 style='color:#1976d2;margin-top:0;'>Source Files</h3>"
    html += "<ul style='list-style:none;padding-left:0;'>"

    seen = set()
    for doc in source_docs:
        source = doc.metadata.get("source", "Unknown")
        module = doc.metadata.get("module", "Unknown")
        if source in seen:
            continue
        seen.add(source)
        display = to_display_path(source, project_root)
        html += (
            "<li style='margin:8px 0;'>"
            f"<span style='background:#4caf50;color:white;padding:2px 8px;border-radius:4px;font-size:.85em;margin-right:8px;'>{module}</span>"
            f"<code style='background:#e0e0e0;padding:2px 6px;border-radius:3px;font-size:.9em;'>{display}</code>"
            "</li>"
        )

    html += "</ul></div>"
    return html


def setup_rag_chain(config: dict):
    persist_dir = config["vectorstore"]["persist_directory"]
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(
            f"Vector DB not found: {persist_dir}\nRun build_knowledge_base.py first."
        )

    embeddings = OllamaEmbeddings(
        model=config["embedding"]["model"],
        base_url=config["embedding"]["base_url"],
    )

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name="hmrv_knowledge_base",
    )

    llm = ChatOpenAI(
        base_url=config["llm"]["base_url"],
        api_key=config["llm"].get("api_key", "not-needed"),
        model=config["llm"]["model"],
        temperature=config["llm"]["temperature"],
        max_tokens=config["llm"]["max_tokens"],
    )

    prompt_template = PromptTemplate(
        template=(
            "You are a senior software engineer helping with codebase Q&A.\n"
            "Only answer from the provided context. If uncertain, say you don't know.\n\n"
            "Context:\n{context}\n\n"
            "Question:\n{question}\n\n"
            "Answer format:\n"
            "1. Start with a short conclusion.\n"
            "2. Mention key files/functions if available.\n"
            "3. Use concise bullet points when useful.\n"
            "4. If information is insufficient, clearly state what is missing.\n"
            "5. Use Markdown."
        ),
        input_variables=["context", "question"],
    )

    search_top_k = config["vectorstore"]["search_top_k"]
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": search_top_k},
        ),
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=True,
    )
    return chain


def query_rag(
    question: str,
    qa_chain,
    project_root: str,
    llm_base_url: str,
) -> Tuple[str, str]:
    if not question.strip():
        return "Please enter a question.", ""

    try:
        result = qa_chain.invoke({"query": question})
        answer = result["result"]
        sources_html = format_sources(result.get("source_documents", []), project_root)
        return answer, sources_html
    except Exception as e:
        error_msg = (
            "### Query Failed\n\n"
            f"Error: `{e}`\n\n"
            "Checklist:\n"
            f"1. Ensure LLM endpoint is running: `{llm_base_url}`\n"
            "2. Verify `config.yaml` LLM settings.\n"
            "3. Verify the selected model is loaded in your LLM server."
        )
        return error_msg, ""


def create_ui(config: dict, qa_chain):
    project_root = config["project"]["root_path"]
    llm_model = config["llm"]["model"]
    llm_base_url = config["llm"]["base_url"]
    embedding_model = config["embedding"]["model"]
    top_k = config["vectorstore"]["search_top_k"]

    examples = [
        ["這個專案的主要入口點在哪裡？"],
        ["請說明資料流程與核心模組。"],
        ["哪些檔案負責 API 路由或控制器？"],
        ["設定檔與環境變數是在哪些地方定義？"],
        ["哪些部分與資料庫或外部服務整合？"],
    ]

    custom_css = """
    .gradio-container { max-width: 1200px !important; }
    """

    with gr.Blocks(title="RAG Code Search", theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.Markdown(
            f"""
# RAG Code Search

目前索引專案: `{project_root}`
"""
        )

        with gr.Row():
            with gr.Column(scale=2):
                question_box = gr.Textbox(
                    label="請輸入問題",
                    placeholder="例如：這個專案如何初始化？某個功能的關鍵檔案在哪裡？",
                    lines=2,
                )
                with gr.Row():
                    submit_btn = gr.Button("查詢", variant="primary", size="lg")
                    clear_btn = gr.Button("清空", size="lg")
            with gr.Column(scale=1):
                gr.Markdown(
                    f"""
### Runtime
- Embedding: `{embedding_model}`
- LLM: `{llm_model}`
- LLM URL: `{llm_base_url}`
- Top K: `{top_k}`
"""
                )

        gr.Markdown("### 範例問題")
        gr.Examples(examples=examples, inputs=question_box, label=None)

        gr.Markdown("---")
        gr.Markdown("### 回答")
        answer_box = gr.Markdown(value="請輸入問題後查詢")
        sources_box = gr.HTML(value="")

        def handle_query(question):
            return query_rag(question, qa_chain, project_root, llm_base_url)

        submit_btn.click(
            fn=handle_query,
            inputs=[question_box],
            outputs=[answer_box, sources_box],
        )
        question_box.submit(
            fn=handle_query,
            inputs=[question_box],
            outputs=[answer_box, sources_box],
        )
        clear_btn.click(
            fn=lambda: ("", "請輸入問題後查詢", ""),
            outputs=[question_box, answer_box, sources_box],
        )

    return demo


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 60)
    print("RAG Code Search (Web UI)")
    print("=" * 60)

    try:
        config = load_config()
        print("Initializing RAG chain...")
        qa_chain = setup_rag_chain(config)
        print("RAG chain ready.")

        demo = create_ui(config, qa_chain)
        demo.launch(
            server_name=config["web_ui"]["host"],
            server_port=config["web_ui"]["port"],
            share=config["web_ui"]["share"],
            inbrowser=True,
        )
    except Exception as e:
        print(f"Startup failed: {e}")
        raise


if __name__ == "__main__":
    main()
