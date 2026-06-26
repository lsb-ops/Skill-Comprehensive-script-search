#!/usr/bin/env python3
"""
WebPPT Maker · 从 generate_*.py 输出中提取 output_folder

用途: run_all.sh 调用 generate_*.py 后，stdout 包含 log 行 + JSON 状态块
本脚本从 stdin 读取，提取 output_folder 字段（支持多行 JSON）

为什么单独成文件: 避免 sc-2 (python3 -c + $VAR 注入) 误报

修复: v1.1.1 — 支持多行 JSON (原 v1.1.0 只处理单行，HTML output 的 JSON 是多行的)
"""
import sys
import json


def main():
    raw = sys.stdin.read()
    # 找 JSON 块（可能跨多行）
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(raw):
        # 跳过非 { 字符
        while idx < len(raw) and raw[idx] != "{":
            idx += 1
        if idx >= len(raw):
            break
        try:
            data, end = decoder.raw_decode(raw[idx:])
            out = data.get("output_folder", "")
            if out:
                print(out)
                return 0
            # 找到 JSON 但没 output_folder，继续找下一个
            idx += end
        except json.JSONDecodeError:
            idx += 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
