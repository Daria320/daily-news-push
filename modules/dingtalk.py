# -*- coding: utf-8 -*-
"""
钉钉推送模块
"""

import urllib.request
import json
import ssl
from typing import Dict, Any

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def send_markdown(webhook: str, title: str, content: str) -> Dict[str, Any]:
    """
    发送 Markdown 格式消息到钉钉

    Args:
        webhook: 钉钉机器人 webhook URL
        title: 消息标题
        content: Markdown 格式的消息内容

    Returns:
        API 响应
    """
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        }
    }

    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')

    req = urllib.request.Request(
        webhook,
        data=json_data,
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req, context=ssl_context) as resp:
        return json.loads(resp.read().decode('utf-8'))


def send_text(webhook: str, content: str) -> Dict[str, Any]:
    """
    发送纯文本消息到钉钉

    Args:
        webhook: 钉钉机器人 webhook URL
        content: 文本内容

    Returns:
        API 响应
    """
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')

    req = urllib.request.Request(
        webhook,
        data=json_data,
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req, context=ssl_context) as resp:
        return json.loads(resp.read().decode('utf-8'))


def send_to_all_webhooks(webhooks: list, title: str, content: str, msg_type: str = "markdown") -> list:
    """
    发送消息到多个钉钉群

    Args:
        webhooks: webhook URL 列表
        title: 消息标题
        content: 消息内容
        msg_type: 消息类型 "markdown" 或 "text"

    Returns:
        每个群的发送结果列表
    """
    results = []
    for i, webhook in enumerate(webhooks, 1):
        if msg_type == "markdown":
            result = send_markdown(webhook, title, content)
        else:
            result = send_text(webhook, content)
        results.append({"group": i, "result": result})
    return results


if __name__ == "__main__":
    # 测试
    from config.settings import DINGTALK_WEBHOOK

    result = send_text(DINGTALK_WEBHOOK, "测试消息：推送模块正常工作")
    print(f"发送结果: {result}")
