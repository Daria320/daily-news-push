# -*- coding: utf-8 -*-
"""
热点新闻抓取模块
支持：知乎热榜、今日头条
"""

import urllib.request
import json
import ssl
import re
from typing import List, Dict, Tuple

# 创建更宽松的 SSL 上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
ssl_context.options |= ssl.OP_NO_SSLv2
ssl_context.options |= ssl.OP_NO_SSLv3


def fetch_weibo_hots(count: int = 20) -> List[Dict]:
    """
    获取微博热搜
    通过浏览器 CDP 获取
    返回: [{'title': str, 'excerpt': str, 'url': str, 'hot': str}, ...]
    """
    import subprocess
    import time
    import json as json_mod

    try:
        # 创建新标签页
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', '--data-raw', 'https://s.weibo.com/top/summary',
             'http://localhost:3456/new'],
            capture_output=True, text=True, timeout=10
        )
        target_info = json_mod.loads(result.stdout)
        target_id = target_info.get('targetId')

        if not target_id:
            return []

        # 等待加载
        time.sleep(4)

        # 获取热搜数据 - 使用修正后的正则表达式
        js_code = '''
        (() => {
            const results = [];
            const text = document.body.innerText;
            const lines = text.split("\\n");

            for (const line of lines) {
                // 匹配格式: 数字 TAB 关键词 热度 TAB 标记
                const match = line.match(/^(\\d+)\\t(.+?)\\s+(\\d+)\\t/);
                if (match) {
                    const title = match[2].trim();
                    const hot = match[3];
                    results.push({
                        title: title,
                        excerpt: "",
                        url: "",
                        hot: hot,
                        source: "微博"
                    });
                }
            }
            return JSON.stringify(results);
        })()
        '''

        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             f'http://localhost:3456/eval?target={target_id}',
             '-d', js_code],
            capture_output=True, text=True, timeout=10
        )

        # 关闭标签页
        subprocess.run(['curl', '-s', f'http://localhost:3456/close?target={target_id}'],
                      capture_output=True, timeout=5)

        response = json_mod.loads(result.stdout)
        data = json_mod.loads(response.get('value', '[]'))
        return data[:count]

    except Exception as e:
        print(f"微博热搜获取失败: {e}")
        return []


def fetch_zhihu_hotlist(count: int = 20) -> List[Dict]:
    """
    获取知乎热榜
    通过浏览器 CDP 获取（需要已登录知乎）
    返回: [{'title': str, 'excerpt': str, 'url': str, 'hot': str}, ...]
    """
    import subprocess
    import time
    import json as json_mod

    try:
        # 创建新标签页
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', '--data-raw', 'https://www.zhihu.com/hot',
             'http://localhost:3456/new'],
            capture_output=True, text=True, timeout=10
        )
        target_info = json_mod.loads(result.stdout)
        target_id = target_info.get('targetId')

        if not target_id:
            return []

        # 等待加载
        time.sleep(4)

        # 获取热榜数据
        js_code = '''
        (() => {
            const results = [];
            const text = document.body.innerText;
            const lines = text.split("\\n");

            let i = 0;
            while (i < lines.length && results.length < 30) {
                const line = lines[i].trim();

                // 匹配数字开头的标题行
                const match = line.match(/^(\\d+)\\s+(.+)$/);
                if (match && match[2].length > 5 && match[2].length < 80) {
                    const title = match[2].trim();
                    results.push({
                        title: title,
                        excerpt: "",
                        url: "",
                        hot: "",
                        source: "知乎"
                    });
                }
                i++;
            }
            return JSON.stringify(results);
        })()
        '''

        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             f'http://localhost:3456/eval?target={target_id}',
             '-d', js_code],
            capture_output=True, text=True, timeout=10
        )

        # 关闭标签页
        subprocess.run(['curl', '-s', f'http://localhost:3456/close?target={target_id}'],
                      capture_output=True, timeout=5)

        response = json_mod.loads(result.stdout)
        data = json_mod.loads(response.get('value', '[]'))
        return data[:count]

    except Exception as e:
        print(f"知乎热榜获取失败: {e}")
        return []


def fetch_toutiao_news(count: int = 20) -> List[Dict]:
    """
    获取今日头条热点新闻
    通过浏览器 CDP 获取
    返回: [{'title': str, 'excerpt': str, 'url': str, 'hot': str}, ...]
    """
    import subprocess
    import time
    import json as json_mod

    try:
        # 创建新标签页
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', '--data-raw', 'https://www.toutiao.com/',
             'http://localhost:3456/new'],
            capture_output=True, text=True, timeout=10
        )
        target_info = json_mod.loads(result.stdout)
        target_id = target_info.get('targetId')

        if not target_id:
            return []

        # 等待加载
        time.sleep(4)

        # 获取热榜数据
        js_code = '''
        (() => {
            const text = document.body.innerText;
            const lines = text.split("\\n");

            // 找到头条热榜后面的内容
            let startIdx = -1;
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes("头条热榜")) {
                    startIdx = i;
                    break;
                }
            }

            if (startIdx === -1) return "[]";

            // 提取热榜内容
            const hotList = [];
            for (let i = startIdx + 1; i < lines.length && hotList.length < 20; i++) {
                const line = lines[i].trim();
                // 跳过空行、数字、无关内容
                if (line && !line.match(/^\\d+$/) && line.length > 5 && line.length < 50 &&
                    !line.includes("扫码下载") && !line.includes("举报") &&
                    !line.includes("©") && !line.includes("换一换")) {
                    hotList.push({
                        title: line,
                        excerpt: "",
                        url: "",
                        hot: "",
                        source: "今日头条"
                    });
                }
            }
            return JSON.stringify(hotList);
        })()
        '''

        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             f'http://localhost:3456/eval?target={target_id}',
             '-d', js_code],
            capture_output=True, text=True, timeout=10
        )

        # 关闭标签页
        subprocess.run(['curl', '-s', f'http://localhost:3456/close?target={target_id}'],
                      capture_output=True, timeout=5)

        response = json_mod.loads(result.stdout)
        data = json_mod.loads(response.get('value', '[]'))
        return data[:count]

    except Exception as e:
        print(f"今日头条获取失败: {e}")
        return []


def classify_news(title: str, category_keywords: dict) -> Tuple[str, bool]:
    """
    对新闻进行分类
    返回: (分类名称, 是否匹配)
    """
    title_lower = title.lower()

    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword.lower() in title_lower:
                return category, True

    return "其他", False


def is_entertainment(title: str, blacklist: list) -> bool:
    """
    判断是否为娱乐新闻或噪音内容
    """
    title_lower = title.lower()

    # 娱乐黑名单
    for keyword in blacklist:
        if keyword.lower() in title_lower:
            return True

    # 噪音过滤：排除明显无关的内容
    noise_patterns = [
        "用户协议", "隐私政策", "广告合作", "友情链接", "下载", "APP",
        "新闻信息服务许可证", "互联网新闻", "营业执照", "广播电视节目",
        "药品医疗器械", "举报", "京ICP", "京公网安备", "网络文化经营",
        "演出许可证", "出版物经营", "互联网宗教", "扫码", "版权所有"
    ]
    for pattern in noise_patterns:
        if pattern in title:
            return True

    return False


def filter_and_classify_news(
    news_list: List[Dict],
    blacklist: list,
    category_keywords: dict,
    allowed_categories: list
) -> Dict[str, List[Dict]]:
    """
    过滤并分类新闻
    返回: {'时政': [...], '财经': [...], ...}
    """
    classified = {cat: [] for cat in allowed_categories}

    for news in news_list:
        title = news.get('title', '')

        # 过滤娱乐内容
        if is_entertainment(title, blacklist):
            continue

        # 分类
        category, matched = classify_news(title, category_keywords)

        if matched and category in allowed_categories:
            classified[category].append(news)

    return classified


def merge_and_dedupe(
    zhihu_news: List[Dict],
    toutiao_news: List[Dict],
    max_per_category: int = 4
) -> Dict[str, List[Dict]]:
    """
    合并去重，每个分类限制数量
    """
    # 简单标题去重
    seen_titles = set()
    merged = {}

    categories = ['时政', '国际', '财经', '社会', '科技']

    for cat in categories:
        merged[cat] = []
        # 优先知乎
        for news in zhihu_news.get(cat, []):
            title_key = news['title'][:20]
            if title_key not in seen_titles and len(merged[cat]) < max_per_category:
                merged[cat].append(news)
                seen_titles.add(title_key)
        # 补充今日头条
        for news in toutiao_news.get(cat, []):
            title_key = news['title'][:20]
            if title_key not in seen_titles and len(merged[cat]) < max_per_category:
                merged[cat].append(news)
                seen_titles.add(title_key)

    return merged


def get_hot_news(
    blacklist: list,
    category_keywords: dict,
    allowed_categories: list,
    total_count: int = 12
) -> Dict[str, List[Dict]]:
    """
    主入口：获取过滤后的热点新闻
    """
    # 计算每分类最大数量
    max_per_cat = (total_count // len(allowed_categories)) + 2

    # 获取原始数据 - 使用微博热搜作为主要来源
    weibo_raw = fetch_weibo_hots(50)
    toutiao_raw = fetch_toutiao_news(30)
    zhihu_raw = fetch_zhihu_hotlist(30)

    # 合并所有数据
    all_raw = weibo_raw + toutiao_raw + zhihu_raw

    # 过滤分类
    filtered = filter_and_classify_news(
        all_raw, blacklist, category_keywords, allowed_categories
    )

    # 限制每个分类的数量
    result = {}
    for cat in allowed_categories:
        result[cat] = filtered.get(cat, [])[:max_per_cat]

    return result


if __name__ == "__main__":
    # 测试
    from config.settings import BLACKLIST_KEYWORDS, CATEGORY_KEYWORDS, ALLOWED_CATEGORIES

    result = get_hot_news(BLACKLIST_KEYWORDS, CATEGORY_KEYWORDS, ALLOWED_CATEGORIES, 12)

    for cat, news_list in result.items():
        print(f"\n【{cat}】")
        for news in news_list:
            print(f"  - {news['title'][:40]} ({news['source']})")
