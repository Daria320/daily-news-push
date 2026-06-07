#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日信息推送主程序 - GitHub Actions 版本
支持：早间快讯、晚间日报、周报
"""

import sys
import os
import json
import urllib.request
import ssl
from datetime import datetime, timedelta

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# ========== 配置 ==========
DINGTALK_WEBHOOKS = os.environ.get('DINGTALK_WEBHOOKS', '').split(',') if os.environ.get('DINGTALK_WEBHOOKS') else [
    "https://oapi.dingtalk.com/robot/send?access_token=d55e07ded7ec9331cfbf316a93605b2eb10b7f7f94f5721841fee5f8ebf6199c",
    "https://oapi.dingtalk.com/robot/send?access_token=e330974aa458165dd3352d046d9803d47521e9e78e76c85edcf8dd81cfe7ff9c",
]

# ========== 钉钉发送 ==========
def send_dingtalk(webhook, msg):
    """发送钉钉消息"""
    data = json.dumps({
        "msgtype": "markdown",
        "markdown": {"title": "每日推送", "text": msg}
    }, ensure_ascii=False).encode('utf-8')

    req = urllib.request.Request(webhook, data=data, headers={
        'Content-Type': 'application/json'
    })

    with urllib.request.urlopen(req, context=ssl_context) as resp:
        return json.loads(resp.read().decode('utf-8'))

def send_to_all(msg):
    """发送到所有群"""
    results = []
    for i, webhook in enumerate(DINGTALK_WEBHOOKS, 1):
        if webhook.strip():
            result = send_dingtalk(webhook.strip(), msg)
            results.append({"group": i, "result": result})
            print(f"群{i}: {result}")
    return results

# ========== 数据获取 ==========
def fetch_json(url):
    """获取 JSON"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except:
        return None

# ========== 早间快讯 ==========
def get_morning_news():
    now = datetime.now()
    msg = f"## 📰 早间财经快讯\n\n⏰ {now.strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"

    # 获取百度热搜
    try:
        data = fetch_json("https://top.baidu.com/api/board?tab=realtime")
        if data:
            items = data.get('data', {}).get('cards', [{}])[0].get('content', [])[:10]
            msg += "### 🔥 热搜头条\n\n"
            for i, item in enumerate(items, 1):
                title = item.get('word', '')[:35]
                msg += f"{i}. {title}\n"
    except:
        pass

    msg += "\n---\n\n"

    # 获取东方财富快讯
    try:
        data = fetch_json("https://newsapi.eastmoney.com/kuaixun/v1/kuaixun/quicknews/list.json")
        if data:
            items = data.get('data', {}).get('fastnews', [])[:8]
            msg += "### 📊 财经快讯\n\n"
            for item in items:
                title = item.get('title', '')[:40]
                msg += f"• {title}\n"
    except:
        pass

    msg += "\n---\n\n📌 数据来源: 百度热搜/东方财富"
    return msg

# ========== 日报 ==========
def get_daily_report():
    now = datetime.now()
    msg = f"## 📈 股市日报\n\n⏰ {now.strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"

    # 市场概况
    msg += "### 📊 市场概况\n\n"
    msg += "详见: https://hhxg.top\n\n"

    # 两融数据
    msg += "### 💰 融资融券\n\n"
    msg += "详见: https://hhxg.top/rzrq.html\n\n"

    msg += "---\n\n📌 数据来源: 恢复量化 hhxg.top"
    return msg

# ========== 周报 ==========
def get_weekly_report():
    now = datetime.now()
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=6)

    msg = f"## 📊 股市周报\n\n"
    msg += f"⏰ {now.strftime('%Y-%m-%d %H:%M')}\n"
    msg += f"📅 本周: {start.strftime('%m/%d')} - {end.strftime('%m/%d')}\n\n---\n\n"

    msg += "### 📈 行情概览\n\n"
    msg += "详见: https://hhxg.top\n\n"

    msg += "### 💰 两融数据\n\n"
    msg += "详见: https://hhxg.top/rzrq.html\n\n"

    msg += "---\n\n📌 数据来源: 恢复量化 hhxg.top"
    return msg

# ========== 主入口 ==========
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"

    print(f"正在准备 {mode} 推送...")

    if mode == "morning":
        msg = get_morning_news()
    elif mode == "daily":
        msg = get_daily_report()
    elif mode == "weekly":
        msg = get_weekly_report()
    else:
        msg = get_morning_news()

    results = send_to_all(msg)
    print(f"发送完成: {results}")
