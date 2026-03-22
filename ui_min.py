# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

import gradio as gr
from main import run_chat

def chat_fn(message, history):
    history = history or []
    reply = run_chat(message)
    history.append((message, reply))
    return history, ""

with gr.Blocks() as demo:
    gr.Markdown("## Gemini 本地聊天（最小稳定版）")
    chatbot = gr.Chatbot()
    txt = gr.Textbox(label="输入内容")
    btn = gr.Button("发送")

    btn.click(chat_fn, [txt, chatbot], [chatbot, txt])

demo.launch(share=True)

