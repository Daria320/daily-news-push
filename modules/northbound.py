# -*- coding: utf-8 -*-
"""
北向资金获取模块
通过东方财富网获取
"""

import subprocess
import json
import time


def fetch_northbound() -> dict:
    """
    获取北向资金数据
    通过东方财富网 CDP 获取
    返回: {'date': str, 'sh_amount': str, 'sz_amount': str, 'total': str, 'net_buy': str}
    """
    try:
        # 创建新标签页
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', '--data-raw', 'https://data.eastmoney.com/hsgt/',
             'http://localhost:3456/new'],
            capture_output=True, text=True, timeout=10
        )
        target_info = json.loads(result.stdout)
        target_id = target_info.get('targetId')

        if not target_id:
            return {}

        # 等待加载
        time.sleep(4)

        # 获取北向资金数据
        js_code = '''
        (() => {
            const text = document.body.innerText;
            const lines = text.split("\\n");

            // 查找数据日期
            let date = "";
            for (const line of lines) {
                const match = line.match(/数据日期[：:]\s*(\d{4}-\d{2}-\d{2})/);
                if (match) {
                    date = match[1];
                    break;
                }
            }

            // 查找北向资金成交额 - 从沪深港通表格提取
            let shAmount = "-";
            let szAmount = "-";
            let shNet = "-";
            let szNet = "-";

            // 解析表格数据
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                // 沪股通
                if (line.includes("港>沪") || line.includes("陆股通")) {
                    // 查找成交净买额
                    const parts = line.split("\\t");
                    for (let j = 0; j < parts.length; j++) {
                        if (parts[j].includes("净买") || parts[j].includes("成交")) {
                            const val = parts[j+1] || parts[j];
                            if (val && val.match(/-?\d+\.?\d*亿/)) {
                                shNet = val.trim();
                            }
                        }
                    }
                }
                // 深股通
                if (line.includes("港>深")) {
                    const parts = line.split("\\t");
                    for (let j = 0; j < parts.length; j++) {
                        if (parts[j].includes("净买") || parts[j].includes("成交")) {
                            const val = parts[j+1] || parts[j];
                            if (val && val.match(/-?\d+\.?\d*亿/)) {
                                szNet = val.trim();
                            }
                        }
                    }
                }
            }

            // 另一种方式：查找"成交净买额(当日)"后面的数值
            let netBuyTotal = "-";
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes("成交净买额") && lines[i].includes("当日")) {
                    // 往后找数值
                    for (let j = i + 1; j < Math.min(i + 10, lines.length); j++) {
                        const val = lines[j].trim();
                        if (val.match(/^-?\d+\.?\d*$/) || val.match(/-?\d+\.?\d*亿/)) {
                            netBuyTotal = val;
                            break;
                        }
                    }
                }
            }

            return JSON.stringify({
                date: date,
                sh_net: shNet,
                sz_net: szNet,
                total_net: netBuyTotal
            });
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

        response = json.loads(result.stdout)
        data = json.loads(response.get('value', '{}'))
        return data

    except Exception as e:
        print(f"北向资金获取失败: {e}")
        return {}


def fetch_northbound_simple() -> dict:
    """
    简化版北向资金获取 - 使用东方财富 API
    使用 curl 命令获取
    """
    import subprocess
    import time

    # 重试机制
    for attempt in range(3):
        try:
            url = "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?lmt=0&klt=1&secid=1.000001&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"

            proc = subprocess.run(
                ['curl', '-s', '--connect-timeout', '10', url],
                capture_output=True, text=True, timeout=15
            )

            if proc.returncode == 0 and proc.stdout:
                data = json.loads(proc.stdout)

                # 解析数据
                if data.get('data') and data['data'].get('klines'):
                    latest = data['data']['klines'][-1]  # 最新一天
                    parts = latest.split(',')
                    if len(parts) >= 6:
                        return {
                            'date': parts[0],
                            'net_inflow': parts[1],  # 北向净流入
                            'balance': parts[5] if len(parts) > 5 else ''
                        }

            return {}

        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                print(f"北向资金 API 获取失败: {e}")
            return {}


if __name__ == "__main__":
    print("测试北向资金获取...")
    data = fetch_northbound_simple()
    print(f"结果: {data}")
