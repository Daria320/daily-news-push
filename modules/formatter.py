# -*- coding: utf-8 -*-
"""
消息格式化模块
支持钉钉 Markdown 格式
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List


def get_weekday_name(dt=None) -> str:
    """获取星期几的中文名"""
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    if dt is None:
        dt = datetime.now()
    return weekdays[dt.weekday()]


def format_header(title: str, date: datetime = None) -> str:
    """格式化消息头部"""
    if date is None:
        date = datetime.now()

    weekday = get_weekday_name(date)
    return f"daily 📰 {title} | {date.strftime('%Y-%m-%d')} {weekday}"


def format_section(title: str, emoji: str = "") -> str:
    """格式化板块标题"""
    if emoji:
        return f"\n\n**{emoji} {title}**\n"
    return f"\n\n**{title}**\n"


def format_separator() -> str:
    """格式化分隔线"""
    return "\n\n━━━━━━━━━━━━━━━━\n"


def format_hot_news(news_by_category: Dict[str, List[Dict]]) -> str:
    """
    格式化热点新闻
    按分类展示，每个分类下显示标题
    """
    lines = [format_section("热点新闻", "🔥")]

    category_emoji = {
        "时政": "🏛️",
        "财经": "💰",
        "社会": "👥",
        "国际": "🌍",
        "科技": "🔬"
    }

    for category in ["时政", "国际", "财经", "社会", "科技"]:
        news_list = news_by_category.get(category, [])
        if not news_list:
            continue

        emoji = category_emoji.get(category, "📌")
        lines.append(f"\n**{emoji} {category}**")

        for i, news in enumerate(news_list, 1):
            title = news.get('title', '')[:45]
            source = news.get('source', '')
            lines.append(f"{i}. {title}")

    return '\n'.join(lines)


def format_finance_news(news_text: str, max_items: int = 10) -> str:
    """
    格式化财经快讯
    从原始文本提取并美化
    """
    lines = [format_section("财经快讯", "⚡")]

    # 解析原始文本
    items = []
    for line in news_text.split('\n'):
        line = line.strip()
        if line.startswith('- `') and '`' in line[3:]:
            # 提取时间和内容
            parts = line.split('`', 2)
            if len(parts) >= 3:
                time = parts[1]
                content = parts[2].strip()
                if content.startswith('['):
                    # 去掉标签如 [焦点]
                    content = content.split(']', 1)[-1].strip()
                items.append({'time': time, 'content': content})
            if len(items) >= max_items:
                break

    for item in items:
        lines.append(f"- **{item['time']}** {item['content'][:50]}")

    return '\n'.join(lines)


def format_market_summary(summary_text: str) -> str:
    """
    格式化市场概况
    """
    lines = [format_section("市场概况", "📊")]

    # 解析关键信息
    if '赚钱效应' in summary_text:
        # 提取赚钱效应
        import re
        match = re.search(r'赚钱效应\s*(\d+\.?\d*%)\s*[（(]?([^）)]+)[）)]?', summary_text)
        if match:
            percent = match.group(1)
            strength = match.group(2).strip()
            lines.append(f"\n**赚钱效应 {percent}**（{strength}）")

    # 提取题材、资金、游资
    keywords = ['题材', '资金', '游资', '焦点']
    for kw in keywords:
        pattern = rf'\*\*{kw}\*\*[：:]\s*([^\n]+)'
        match = re.search(pattern, summary_text)
        if match:
            content = match.group(1).strip()
            lines.append(f"- **{kw}**：{content}")

    return '\n'.join(lines)


def format_margin_data(margin_text: str, is_weekly: bool = False) -> str:
    """
    格式化两融数据 - 将表格转为列表
    """
    lines = []

    if is_weekly:
        lines.append(format_section("融资融券周报", "📈"))
    else:
        lines.append(format_section("融资融券", "📈"))

    # 提取关键数据
    import re

    # 最新余额
    match = re.search(r'最新融资余额[：:]\s*\*\*(\d+\.?\d*)\s*亿?\*\*', margin_text)
    if match:
        lines.append(f"\n**融资余额**：{match.group(1)} 亿")

    match = re.search(r'最新融券余额[：:]\s*\*\*(\d+\.?\d*)\s*亿?\*\*', margin_text)
    if match:
        lines.append(f"**融券余额**：{match.group(1)} 亿")

    # 变化
    match = re.search(r'7\s*日融资变化[：:]\s*\*\*([+-]?\d+\.?\d*)\s*亿?\*\*', margin_text)
    if match:
        change = match.group(1)
        arrow = "📈" if float(change) > 0 else "📉"
        lines.append(f"**7日变化**：{arrow} {change} 亿")

    # 净买入 TOP 5
    lines.append("\n**融资净买入 TOP5**")
    top_pattern = r'\|\s*([^|]+)\s*\|\s*[\d.]+\s*\|\s*([+-][\d.]+)\s*\|\s*([+-][\d.]+%)\s*\|'
    matches = re.findall(top_pattern, margin_text)

    count = 0
    for match in matches:
        stock = match[0].strip()
        change_val = match[1]
        change_pct = match[2]
        if stock not in ['股票', '---', '']:
            count += 1
            lines.append(f"  {count}. **{stock}** {change_val}亿 ({change_pct})")
            if count >= 5:
                break

    return '\n'.join(lines)


def format_market_index(data: dict) -> str:
    """
    格式化大盘指数数据
    """
    lines = [format_section("大盘指数", "📈")]

    if not data:
        lines.append("\n暂无数据")
        return '\n'.join(lines)

    # 上证指数
    if 'sh_index' in data:
        sh_change = data.get('sh_change', 0)
        arrow = "🔺" if sh_change >= 0 else "🔻"
        lines.append(f"\n**上证指数**：{data['sh_index']} {arrow} {sh_change:+.2f}%")

    # 深证成指
    if 'sz_index' in data:
        sz_change = data.get('sz_change', 0)
        arrow = "🔺" if sz_change >= 0 else "🔻"
        lines.append(f"**深证成指**：{data['sz_index']} {arrow} {sz_change:+.2f}%")

    # 创业板指
    if 'cyb_index' in data:
        cyb_change = data.get('cyb_change', 0)
        arrow = "🔺" if cyb_change >= 0 else "🔻"
        lines.append(f"**创业板指**：{data['cyb_index']} {arrow} {cyb_change:+.2f}%")

    # 两市成交额
    if 'total_amount' in data:
        amount = data['total_amount']
        lines.append(f"\n**两市成交**：{amount} 亿")

    return '\n'.join(lines)


def format_northbound(data: dict) -> str:
    """
    格式化北向资金数据
    """
    lines = [format_section("北向资金", "🌏")]

    if not data:
        lines.append("\n暂无数据")
        return '\n'.join(lines)

    date = data.get('date', '')
    net_inflow = data.get('net_inflow', '')

    if net_inflow:
        try:
            # 转换为亿元
            net_val = float(net_inflow) / 100000000
            if net_val > 0:
                arrow = "📈"
                direction = "净流入"
            else:
                arrow = "📉"
                direction = "净流出"
            lines.append(f"\n**{arrow} {direction}**：{abs(net_val):.2f} 亿")
        except:
            lines.append(f"\n**净流入**：{net_inflow}")

    if date:
        # 只保留日期部分
        date_str = date.split()[0] if ' ' in date else date
        lines.append(f"📅 日期：{date_str}")

    return '\n'.join(lines)


def format_calendar(calendar_text: str) -> str:
    """
    格式化财经日历
    """
    lines = [format_section("财经日历", "📅")]

    if not calendar_text:
        lines.append("\n暂无重要事件")
        return '\n'.join(lines)

    # 提取本周重要事件
    events = []
    for line in calendar_text.split('\n'):
        line = line.strip()
        if line.startswith('- **') and '**' in line[4:]:
            # 格式：- **2026-05-19** [unlock] 限售解禁
            parts = line.split('**')
            if len(parts) >= 3:
                date = parts[1]
                event = parts[2].strip()
                if event.startswith('['):
                    event = event  # 保留标签
                events.append({'date': date, 'event': event})

    # 显示前5个事件
    for i, event in enumerate(events[:5], 1):
        lines.append(f"\n{i}. **{event['date']}** {event['event'][:30]}")

    return '\n'.join(lines)


def format_daily_report(snapshot_text: str, margin_text: str, index_data: dict = None) -> str:
    """
    格式化晚间日报
    """
    lines = [format_header("股市日报")]
    lines.append(format_separator())

    # 大盘指数
    if index_data:
        lines.append(format_market_index(index_data))
        lines.append(format_separator())

    # 市场概况部分
    lines.append(format_section("行情概况", "📊"))

    # 提取主要指数
    import re

    # 简化处理，提取关键信息
    if '赚钱效应' in snapshot_text:
        match = re.search(r'赚钱效应\s*(\d+\.?\d*%)', snapshot_text)
        if match:
            lines.append(f"\n**赚钱效应**：{match.group(1)}")

    # 题材、资金
    for kw in ['题材', '资金', '游资']:
        pattern = rf'\*\*{kw}\*\*[：:]\s*([^\n]+)'
        match = re.search(pattern, snapshot_text)
        if match:
            lines.append(f"- **{kw}**：{match.group(1).strip()}")

    lines.append(format_separator())

    # 两融数据
    lines.append(format_margin_data(margin_text))

    lines.append(format_separator())
    lines.append("\n📌 数据来源：恢复量化 hhxg.top、东方财富")

    return '\n'.join(lines)


def format_weekly_report(snapshot_text: str, margin_text: str) -> str:
    """
    格式化周报
    """
    now = datetime.now()
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=6)
    week_range = f"{start.strftime('%m/%d')} - {end.strftime('%m/%d')}"

    lines = [format_header("股市周报")]
    lines.append(f"\n📅 本周：{week_range}")
    lines.append(format_separator())

    # 市场概况
    lines.append(format_section("本周行情", "📊"))

    # 详细数据
    lines.append(snapshot_text[:2000])

    lines.append(format_separator())

    # 两融
    lines.append(format_margin_data(margin_text, is_weekly=True))

    lines.append(format_separator())
    lines.append("\n📌 数据来源：恢复量化 hhxg.top")

    return '\n'.join(lines)


def format_morning_message(
    hot_news: Dict[str, List[Dict]],
    finance_news: str,
    market_summary: str
) -> str:
    """
    格式化完整的早间推送
    """
    lines = [format_header("早间快讯")]
    lines.append(format_separator())

    # 热点新闻
    lines.append(format_hot_news(hot_news))

    lines.append(format_separator())

    # 财经快讯
    lines.append(format_finance_news(finance_news))

    lines.append(format_separator())

    # 市场概况
    lines.append(format_market_summary(market_summary))

    lines.append(format_separator())
    lines.append("\n📌 数据来源：知乎热榜、今日头条、恢复量化")

    return '\n'.join(lines)


if __name__ == "__main__":
    # 测试
    test_news = {
        "时政": [{"title": "国务院发布新政策促进经济发展", "source": "知乎"}],
        "国际": [{"title": "中美领导人举行会谈", "source": "今日头条"}],
        "财经": [{"title": "央行宣布降准", "source": "知乎"}],
    }
    print(format_hot_news(test_news))
