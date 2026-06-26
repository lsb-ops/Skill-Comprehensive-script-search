#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storyboard-shot-optimizer - 分镜头优化搜索引擎工具
16个搜索引擎 v1.0
支持7个国内引擎 + 9个国际引擎
"""

import argparse
import json
import sys
import time
import random
from datetime import datetime
from typing import List, Dict, Any

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

ENGINES = {
    # 国内引擎 (7个)
    "Baidu": {
        "url": "https://www.baidu.com/s?wd={keyword}",
        "region": "cn",
        "priority": 1,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "BingCN": {
        "url": "https://cn.bing.com/search?q={keyword}&ensearch=0",
        "region": "cn",
        "priority": 2,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "360": {
        "url": "https://www.so.com/s?q={keyword}",
        "region": "cn",
        "priority": 3,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "Sogou": {
        "url": "https://www.sogou.com/web?query={keyword}",
        "region": "cn",
        "priority": 4,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "WeChat": {
        "url": "https://wx.sogou.com/weixin?type=2&query={keyword}",
        "region": "cn",
        "priority": 5,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "Shenma": {
        "url": "https://m.sm.cn/s?q={keyword}",
        "region": "cn",
        "priority": 6,
        "headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
        }
    },
    "Douban": {
        "url": "https://www.douban.com/search?q={keyword}",
        "region": "cn",
        "priority": 7,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    # 国际引擎 (9个)
    "Google": {
        "url": "https://www.google.com/search?q={keyword}",
        "region": "global",
        "priority": 1,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "GoogleHK": {
        "url": "https://www.google.hk/search?q={keyword}",
        "region": "global",
        "priority": 2,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "DuckDuckGo": {
        "url": "https://duckduckgo.com/html/?q={keyword}",
        "region": "global",
        "priority": 3,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "Yahoo": {
        "url": "https://search.yahoo.com/search?p={keyword}",
        "region": "global",
        "priority": 4,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "Startpage": {
        "url": "https://www.startpage.com/sp/search?query={keyword}",
        "region": "global",
        "priority": 5,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "Brave": {
        "url": "https://search.brave.com/search?q={keyword}",
        "region": "global",
        "priority": 6,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "Ecosia": {
        "url": "https://www.ecosia.org/search?q={keyword}",
        "region": "global",
        "priority": 7,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "Qwant": {
        "url": "https://www.qwant.com/?q={keyword}",
        "region": "global",
        "priority": 8,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    },
    "WolframAlpha": {
        "url": "https://www.wolframalpha.com/input?i={keyword}",
        "region": "global",
        "priority": 9,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    }
}


class ResultParser:
    """针对不同搜索引擎的结果解析器"""

    @staticmethod
    def parse_baidu(html: str) -> List[Dict]:
        """解析百度搜索结果"""
        results = []
        if not HAS_DEPS:
            return results
        soup = BeautifulSoup(html, 'lxml')
        for item in soup.select('div.result'):
            try:
                title = item.select_one('h3.t') or item.select_one('.c-title')
                link = item.select_one('a[href]')
                snippet = item.select_one('.c-abstract') or item.select_one('.content-right_8Zs40')
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'url': link.get('href', ''),
                        'snippet': snippet.get_text(strip=True) if snippet else ''
                    })
            except Exception:
                continue
        return results

    @staticmethod
    def parse_google(html: str) -> List[Dict]:
        """解析Google搜索结果"""
        results = []
        if not HAS_DEPS:
            return results
        soup = BeautifulSoup(html, 'lxml')
        for item in soup.select('div.g'):
            try:
                title = item.select_one('h3')
                link = item.select_one('a[href]')
                snippet = item.select_one('div.VwiC3b') or item.select_one('span.aCOpRe')
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'url': link.get('href', ''),
                        'snippet': snippet.get_text(strip=True) if snippet else ''
                    })
            except Exception:
                continue
        return results

    @staticmethod
    def parse_duckduckgo(html: str) -> List[Dict]:
        """解析DuckDuckGo搜索结果"""
        results = []
        if not HAS_DEPS:
            return results
        soup = BeautifulSoup(html, 'lxml')
        for item in soup.select('div.result'):
            try:
                title = item.select_one('h2.result__title')
                link = item.select_one('a.result__a')
                snippet = item.select_one('a.result__snippet')
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'url': link.get('href', ''),
                        'snippet': snippet.get_text(strip=True) if snippet else ''
                    })
            except Exception:
                continue
        return results

    @staticmethod
    def parse_generic(html: str) -> List[Dict]:
        """通用解析器"""
        results = []
        if not HAS_DEPS:
            return results
        soup = BeautifulSoup(html, 'lxml')
        for item in soup.select('div.result, li.result, article'):
            try:
                title = item.select_one('h1, h2, h3, h4')
                link = item.select_one('a[href]')
                snippet = item.select_one('p, div.snippet, div.abstract')
                if title and link:
                    results.append({
                        'title': title.get_text(strip=True),
                        'url': link.get('href', ''),
                        'snippet': snippet.get_text(strip=True)[:200] if snippet else ''
                    })
            except Exception:
                continue
        return results[:10]


class SearchExecutor:
    def __init__(self, timeout: int = 10, delay: float = 1.5):
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()

    def search(self, query: str, engines: List[str] = None, count: int = 5, region: str = 'all') -> Dict:
        """
        执行搜索

        Args:
            query: 搜索关键词
            engines: 引擎列表，如 ['Baidu', 'Google']
            count: 每个引擎返回的结果数
            region: 区域筛选 'cn'/'global'/'all'

        Returns:
            Dict: 包含status和数据
        """
        if not HAS_DEPS:
            return {
                "status": "error",
                "error": "缺少依赖库 requests 和 beautifulsoup4，请运行: pip install requests beautifulsoup4"
            }

        if not query:
            return {"status": "error", "error": "搜索关键词不能为空"}

        # 选择引擎
        if engines:
            selected_engines = {k: v for k, v in ENGINES.items() if k in engines}
        elif region == 'cn':
            selected_engines = {k: v for k, v in ENGINES.items() if v['region'] == 'cn'}
        elif region == 'global':
            selected_engines = {k: v for k, v in ENGINES.items() if v['region'] == 'global'}
        else:
            selected_engines = ENGINES

        all_results = []

        for engine_name, engine_config in selected_engines.items():
            try:
                url = engine_config['url'].format(keyword=query)
                headers = engine_config.get('headers', {})

                response = self.session.get(url, headers=headers, timeout=self.timeout)
                time.sleep(self.delay + random.uniform(0, 0.5))

                if response.status_code == 200:
                    # 根据引擎选择解析器
                    if 'baidu' in engine_name.lower():
                        results = ResultParser.parse_baidu(response.text)
                    elif 'google' in engine_name.lower():
                        results = ResultParser.parse_google(response.text)
                    elif 'duckduckgo' in engine_name.lower():
                        results = ResultParser.parse_duckduckgo(response.text)
                    else:
                        results = ResultParser.parse_generic(response.text)

                    all_results.extend([
                        {**r, 'engine': engine_name} for r in results[:count]
                    ])
                else:
                    print(f"引擎 {engine_name} 返回状态码: {response.status_code}", file=sys.stderr)

            except Exception as e:
                print(f"引擎 {engine_name} 搜索失败: {str(e)}", file=sys.stderr)
                continue

        return {
            "status": "success",
            "data": {
                "query": query,
                "total_results": len(all_results),
                "results": all_results[:count * 3]
            }
        }


def parse_args():
    parser = argparse.ArgumentParser(
        description='分镜头优化搜索引擎工具 - 16个搜索引擎支持',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python3 search.py --query "cinematography shot composition" --engines Google,Baidu --count 5
  python3 search.py --query "分镜头 景别 规则" --region cn --count 10
  python3 search.py --query "film blocking" --engines Google,DuckDuckGo
        '''
    )
    parser.add_argument('--query', '-q', required=True, help='搜索关键词')
    parser.add_argument('--engines', '-e', default='Baidu,Google',
                        help='逗号分隔的引擎列表，默认: Baidu,Google')
    parser.add_argument('--region', '-r', default='all',
                        choices=['all', 'cn', 'global'],
                        help='区域筛选，默认: all')
    parser.add_argument('--count', '-n', type=int, default=5,
                        help='每个引擎返回的结果数，默认: 5')
    parser.add_argument('--timeout', '-t', type=int, default=10,
                        help='超时秒数，默认: 10')
    parser.add_argument('--delay', '-d', type=float, default=1.5,
                        help='请求间隔秒数，默认: 1.5')
    parser.add_argument('--format', '-f', default='json',
                        choices=['json', 'text'],
                        help='输出格式，默认: json')
    return parser.parse_args()


def main():
    args = parse_args()

    engines = args.engines.split(',') if args.engines else None

    executor = SearchExecutor(timeout=args.timeout, delay=args.delay)
    result = executor.search(
        query=args.query,
        engines=engines,
        count=args.count,
        region=args.region
    )

    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result['status'] == 'success':
            for item in result['data']['results']:
                print(f"[{item['engine']}] {item['title']}")
                print(f"  {item['url']}")
                print(f"  {item['snippet'][:100]}...")
                print()
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
