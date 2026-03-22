# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import os

# ===== 强制清空所有代理 & NO_PROXY =====
for k in [
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
    "NO_PROXY", "no_proxy"
]:
    os.environ.pop(k, None)

# 明确告诉 Python：localhost 不走代理
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

import gradio as gr
from main import run_chat

def chat_interface(message, history):
    if history is None:
        history = []

    reply = run_chat(message)
    history.append((message, reply))
    return history, ""

with gr.Blocks(title="Gemini 本地最小稳定客户端") as demo:
    gr.Markdown("## Gemini 本地最小稳定客户端")

    chatbot = gr.Chatbot(label="模型回复")
    txt = gr.Textbox(label="输入内容")
    btn = gr.Button("发送")

    btn.click(
        chat_interface,
        inputs=[txt, chatbot],
        outputs=[chatbot, txt]
    )

demo.launch(
    server_name="127.0.0.1",
    server_port=7860,
    share=False,
    show_api=False
)

