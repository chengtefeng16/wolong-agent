# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from main import run_chat
from datetime import datetime

def local_time_answer(user_text: str) -> str | None:
    t = user_text.strip()
    # 只要你问的是“时间/日期”，我们就不调用 Gemini，直接用电脑时间回答
    if any(k in t for k in ["几点", "时间", "几号", "日期", "星期"]):
        now = datetime.now()
        return now.strftime("本机时间：%Y-%m-%d %H:%M:%S")
    return None

def main():
    print("Gemini CLI 已启动，输入 exit 退出")
    while True:
        user = input("你：").strip()
        if user.lower() in ["exit", "quit", "q"]:
            break

        # 1) 时间类问题：走本地，不耗配额
        local = local_time_answer(user)
        if local is not None:
            print("Gemini：", local)
            continue

        # 2) 其它问题：才调用 Gemini，并且抓异常
        try:
            reply = run_chat(user)
            print("Gemini：", reply)
        except Exception as e:
            s = str(e)
            # 429：配额耗尽，别再狂刷
            if "RESOURCE_EXHAUSTED" in s or "429" in s:
                print("出错了：429 配额已用完（今天/这一分钟的请求次数到顶了）。")
                print("解决办法：")
                print("1) 先别继续问（继续问只会继续失败）")
                print("2) 换一个模型/开通计费/等配额恢复")
            else:
                print("出错了：", s)

if __name__ == "__main__":
    main()

