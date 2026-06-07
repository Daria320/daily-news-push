# -*- coding: utf-8 -*-
"""
大盘指数获取模块
通过浏览器 CDP 获取
"""

import subprocess
import json
import time


def fetch_market_index() -> dict:
    """
    获取大盘指数和成交额
    通过浏览器 CDP 获取
    """
    result = {}

    try:
        # 创建新标签页 - 东方财富指数页面
        proc = subprocess.run(
            ['curl', '-s', '-X', 'POST', '--data-raw', 'https://quote.eastmoney.com/sh000001.html',
             'http://localhost:3456/new'],
            capture_output=True, text=True, timeout=10
        )

        target_info = json.loads(proc.stdout)
        target_id = target_info.get('targetId')

        if not target_id:
            return result

        time.sleep(4)

        # 获取指数数据
        js_code = '''
        (() => {
            const text = document.body.innerText;
            const result = {};

            // 匹配格式：上证：4131.53 ↓-3.86 -0.09% 1.315万亿元
            const shMatch = text.match(/上证[：:]\s*(\d+\.?\d*)\s*[↓↑]?\s*-?\d+\.?\d*\s*(-?\d+\.?\d*)%/);
            if (shMatch) {
                result.sh_index = parseFloat(shMatch[1]);
                result.sh_change = parseFloat(shMatch[2]);
            }

            const szMatch = text.match(/深证[：:]\s*(\d+\.?\d*)\s*[↓↑]?\s*-?\d+\.?\d*\s*(-?\d+\.?\d*)%/);
            if (szMatch) {
                result.sz_index = parseFloat(szMatch[1]);
                result.sz_change = parseFloat(szMatch[2]);
            }

            // 从表格中提取创业板指
            const cybMatch = text.match(/创业板指[\\s\\t]+(\d+\.?\d*)[\\s\\t]+(-?\d+\.?\d*)%/);
            if (cybMatch) {
                result.cyb_index = parseFloat(cybMatch[1]);
                result.cyb_change = parseFloat(cybMatch[2]);
            }

            // 提取成交额
            const amountMatch = text.match(/成交额[：:]\s*([\d.]+)万亿/);
            if (amountMatch) {
                result.sh_amount = amountMatch[1] + "万亿";
            }

            return JSON.stringify(result);
        })()
        '''

        proc = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             f'http://localhost:3456/eval?target={target_id}',
             '-d', js_code],
            capture_output=True, text=True, timeout=10
        )

        # 关闭标签页
        subprocess.run(['curl', '-s', f'http://localhost:3456/close?target={target_id}'],
                      capture_output=True, timeout=5)

        response = json.loads(proc.stdout)
        result = json.loads(response.get('value', '{}'))

    except Exception as e:
        print(f"大盘指数获取失败: {e}")

    return result


if __name__ == "__main__":
    print("测试大盘指数获取...")
    data = fetch_market_index()
    print(f"结果: {data}")
