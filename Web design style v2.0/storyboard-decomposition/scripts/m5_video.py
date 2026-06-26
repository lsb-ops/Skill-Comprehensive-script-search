#!/usr/bin/env python3
"""
m5_video.py — M5 视频生成模块（v1.0 工程化）

输入：M3 输出的 镜{NN}_xxx.txt（AI 视频 prompt）
输出：每镜的 mp4 视频文件
  - 真实模式：调用 即梦/可灵/Sora API
  - Mock 模式：生成 mock 视频文件 + 元数据（无 API 凭证时降级）

用法:
    python3 m5_video.py <M3_DIR> <output_dir> --platform 即梦
    python3 m5_video.py <M3_DIR> <output_dir> --mock        # 强制 mock
    python3 m5_video.py <M3_DIR> <output_dir> --mirror 001   # 只生成镜 001

设计哲学：
1. 端到端：M3 骨架 → 视频文件，一键完成
2. 双模式：有 API 走真实，无 API 走 mock（工程链路完整）
3. 失败重试：单镜最多重试 3 次（指数退避）
4. 元数据：每镜生成 manifest.json（prompt 哈希 + API response + 时长）
5. 进度可见：实时输出进度条

Why: 解决"skill 是中间产物"偏差 — 真正交付物是视频文件。
     mock 模式保证即使没 API，工程链路也能跑通。
"""

import sys
import json
import argparse
import time
import hashlib
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


# === API 配置（从环境变量读取，避免硬编码） ===

API_CONFIGS = {
    "即梦": {
        "endpoint": "https://jimeng.jianying.com/api/v1/video/generate",
        "auth_env": "JIMENG_API_KEY",
        "max_duration": 10,  # 单次最大 10 秒
        "response_path": ["data", "video_url"],
    },
    "可灵": {
        "endpoint": "https://api.klingai.com/v1/videos/text2video",
        "auth_env": "KLING_API_KEY",
        "max_duration": 10,
        "response_path": ["data", "video_url"],
    },
    "Sora": {
        "endpoint": "https://api.openai.com/v1/video/generations",
        "auth_env": "OPENAI_API_KEY",
        "max_duration": 20,
        "response_path": ["data", "0", "url"],
    },
    "Runway": {
        "endpoint": "https://api.runwayml.com/v1/generate",
        "auth_env": "RUNWAY_API_KEY",
        "max_duration": 16,
        "response_path": ["url"],
    },
}


# === Prompt 解析（从 txt 提取核心 prompt） ===

def extract_prompt_from_txt(txt_path: Path) -> Dict[str, Any]:
    """从 M3 输出的 txt 中提取 prompt 各段

    返回：
        {
            "title": str,
            "duration_sec": float,
            "shot_size": str,
            "camera_movement": str,
            "description": str,        # 画面描述段（核心）
            "lighting": str,            # 光影氛围段
            "tech_params": str,         # 技术参数段
            "full_prompt": str,         # 完整 prompt（供视频 API）
        }
    """
    content = txt_path.read_text(encoding="utf-8")

    # 解析标题行：镜001 xxx 8秒
    title = ""
    duration_sec = 0.0
    first_line = content.split('\n')[0].strip()
    # 匹配 "镜001 名称 X秒"
    import re
    m = re.match(r'镜(\d+)\s+(.+?)\s+(\d+(?:\.\d+)?)\s*秒', first_line)
    if m:
        title = f"镜{m.group(1)} {m.group(2)}"
        duration_sec = float(m.group(3))

    # 解析各段
    sections = {}
    current = None
    for line in content.split('\n'):
        line_stripped = line.strip()
        if line_stripped in ["资产引用", "人物资产档案", "镜头参数", "画面描述", "光影氛围", "技术参数"]:
            current = line_stripped
            sections[current] = []
        elif current:
            sections[current].append(line)

    for k in sections:
        sections[k] = '\n'.join(sections[k]).strip()

    # 提取关键参数
    shot_size = ""
    camera_movement = ""
    if "镜头参数" in sections:
        params_text = sections["镜头参数"]
        m_size = re.search(r'景别(\S+)', params_text)
        m_move = re.search(r'运镜(\S+)', params_text)
        if m_size: shot_size = m_size.group(1)
        if m_move: camera_movement = m_move.group(1)

    # 构造完整 prompt（视频 API 接受）
    prompt_parts = []
    if title:
        prompt_parts.append(f"[{title}]")
    if shot_size:
        prompt_parts.append(f"景别:{shot_size}")
    if camera_movement:
        prompt_parts.append(f"运镜:{camera_movement}")
    if "画面描述" in sections:
        prompt_parts.append(sections["画面描述"])
    if "光影氛围" in sections:
        prompt_parts.append(f"光影:{sections['光影氛围']}")

    return {
        "title": title,
        "duration_sec": duration_sec,
        "shot_size": shot_size,
        "camera_movement": camera_movement,
        "description": sections.get("画面描述", ""),
        "lighting": sections.get("光影氛围", ""),
        "tech_params": sections.get("技术参数", ""),
        "full_prompt": "\n".join(prompt_parts),
    }


# === Mock 视频生成 ===

def generate_mock_video(prompt_data: Dict, output_path: Path, duration_sec: float) -> Dict:
    """生成 mock 视频文件（无 API 时降级）

    实际生成：1 个空白 mp4 占位 + 完整 manifest.json
    """
    # 写 mock mp4（最小有效 mp4 字节）
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 写一个标记文件（不写真实 mp4，因为需要 ffmpeg）
    # 改用 .mp4.txt 作为 mock 标识，避免假 mp4
    mock_path = output_path.with_suffix('.mp4.mock')
    mock_path.write_text(
        f"MOCK VIDEO\n"
        f"Title: {prompt_data['title']}\n"
        f"Duration: {duration_sec}s\n"
        f"Shot: {prompt_data['shot_size']}\n"
        f"Movement: {prompt_data['camera_movement']}\n"
        f"---PROMPT---\n{prompt_data['full_prompt']}\n",
        encoding="utf-8"
    )

    # 写 manifest
    manifest = {
        "title": prompt_data["title"],
        "duration_sec": duration_sec,
        "shot_size": prompt_data["shot_size"],
        "camera_movement": prompt_data["camera_movement"],
        "mode": "mock",
        "mock_file": str(mock_path),
        "prompt_hash": hashlib.md5(prompt_data["full_prompt"].encode()).hexdigest(),
        "generated_at": datetime.now().isoformat(),
    }
    manifest_path = output_path.with_suffix('.manifest.json')
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "status": "mock_ok",
        "video_path": str(mock_path),
        "manifest_path": str(manifest_path),
        "duration_sec": duration_sec,
    }


# === 真实 API 调用 ===

def call_video_api(prompt_data: Dict, output_path: Path, platform: str, max_retries: int = 3) -> Dict:
    """调用视频生成 API（带重试）"""
    config = API_CONFIGS.get(platform)
    if not config:
        return {"status": "error", "error": f"未知平台: {platform}"}

    api_key = os.environ.get(config["auth_env"])
    if not api_key:
        return {
            "status": "no_api_key",
            "error": f"未设置环境变量 {config['auth_env']}，请设置 API 凭证后重试",
            "hint": f"export {config['auth_env']}=your_api_key",
        }

    # 截断 prompt（视频 API 通常有 token 限制）
    max_prompt_chars = 4000
    prompt_text = prompt_data["full_prompt"][:max_prompt_chars]

    payload = {
        "prompt": prompt_text,
        "duration": min(prompt_data.get("duration_sec", 5), config["max_duration"]),
        "aspect_ratio": "9:16",
    }

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                config["endpoint"],
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            # 提取视频 URL
            video_url = result
            for key in config["response_path"]:
                video_url = video_url.get(key) if isinstance(video_url, dict) else None
                if video_url is None:
                    break

            if not video_url:
                return {"status": "error", "error": f"API 响应无视频 URL: {result}"}

            # 下载视频
            output_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(video_url, str(output_path))

            # 写 manifest
            manifest = {
                "title": prompt_data["title"],
                "duration_sec": prompt_data.get("duration_sec", 5),
                "mode": "real",
                "platform": platform,
                "video_url": video_url,
                "prompt_hash": hashlib.md5(prompt_data["full_prompt"].encode()).hexdigest(),
                "generated_at": datetime.now().isoformat(),
                "attempts": attempt,
            }
            manifest_path = output_path.with_suffix('.manifest.json')
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            return {
                "status": "real_ok",
                "video_path": str(output_path),
                "manifest_path": str(manifest_path),
                "attempts": attempt,
            }

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  ⚠ 尝试 {attempt} 失败，{wait}s 后重试: {e}", file=sys.stderr)
                time.sleep(wait)
            else:
                return {
                    "status": "error",
                    "error": f"API 调用失败 {max_retries} 次: {e}",
                    "attempts": attempt,
                }


# === 单镜生成 ===

def generate_single_mirror(txt_path: Path, output_dir: Path, platform: str, use_mock: bool) -> Dict:
    """生成单镜视频"""
    mirror_id = txt_path.stem.split('_')[0]  # 镜001
    print(f"  → {mirror_id}: 解析 prompt...", file=sys.stderr)

    prompt_data = extract_prompt_from_txt(txt_path)
    if prompt_data["duration_sec"] <= 0:
        return {"status": "error", "error": f"无法解析时长: {txt_path}"}

    output_path = output_dir / f"{mirror_id}.mp4"

    # 选择模式
    if use_mock:
        print(f"  → {mirror_id}: Mock 模式...", file=sys.stderr)
        result = generate_mock_video(prompt_data, output_path, prompt_data["duration_sec"])
    else:
        print(f"  → {mirror_id}: 真实 API ({platform})...", file=sys.stderr)
        result = call_video_api(prompt_data, output_path, platform)

    return result


# === 批量生成 ===

def generate_all_mirrors(m3_dir: Path, output_dir: Path, platform: str, use_mock: bool, target_mirror: Optional[str] = None) -> List[Dict]:
    """批量生成所有镜"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 找到所有镜 txt
    txt_files = sorted(m3_dir.glob("镜*.txt"))
    if target_mirror:
        txt_files = [f for f in txt_files if target_mirror in f.name]

    print(f"📦 找到 {len(txt_files)} 个镜 txt", file=sys.stderr)
    results = []

    for i, txt_path in enumerate(txt_files, 1):
        print(f"[{i}/{len(txt_files)}]", file=sys.stderr, end=" ")
        result = generate_single_mirror(txt_path, output_dir, platform, use_mock)
        result["mirror_id"] = txt_path.stem
        result["txt_path"] = str(txt_path)
        results.append(result)

    return results


# === 总结报告 ===

def summarize_results(results: List[Dict]) -> Dict:
    """汇总结果"""
    ok = [r for r in results if r.get("status") in ["real_ok", "mock_ok"]]
    no_key = [r for r in results if r.get("status") == "no_api_key"]
    errors = [r for r in results if r.get("status") == "error"]

    summary = {
        "total": len(results),
        "ok": len(ok),
        "no_api_key": len(no_key),
        "errors": len(errors),
        "ok_mirrors": [r["mirror_id"] for r in ok],
        "error_mirrors": [r.get("mirror_id", "?") for r in errors],
    }
    return summary


# === Main ===

import os

def main():
    parser = argparse.ArgumentParser(description="M5 视频生成（v1.0 工程化）")
    parser.add_argument("m3_dir", help="M3 输出目录（镜*.txt）")
    parser.add_argument("output_dir", help="视频输出目录")
    parser.add_argument("--platform", default="即梦", help="AI 平台（即梦/可灵/Sora/Runway）")
    parser.add_argument("--mock", action="store_true", help="强制 mock 模式")
    parser.add_argument("--mirror", help="只生成指定镜（如 001）")
    parser.add_argument("--report", help="报告输出路径（默认 <output_dir>/m5_report.json）")
    args = parser.parse_args()

    m3_dir = Path(args.m3_dir)
    output_dir = Path(args.output_dir)
    if not m3_dir.exists():
        print(f"❌ M3 目录不存在: {m3_dir}", file=sys.stderr)
        sys.exit(1)

    # 检测是否走 mock（无 API 凭证 + 没指定 --mock）
    use_mock = args.mock
    if not use_mock:
        config = API_CONFIGS.get(args.platform, {})
        env_key = config.get("auth_env", "")
        if env_key and not os.environ.get(env_key):
            print(f"⚠ 未检测到 {env_key}，自动降级到 mock 模式", file=sys.stderr)
            print(f"  提示: export {env_key}=your_api_key 启用真实模式", file=sys.stderr)
            use_mock = True

    # 生成
    results = generate_all_mirrors(m3_dir, output_dir, args.platform, use_mock, args.mirror)

    # 报告
    summary = summarize_results(results)
    report = {
        "summary": summary,
        "results": results,
        "platform": args.platform,
        "mode": "mock" if use_mock else "real",
        "generated_at": datetime.now().isoformat(),
    }
    report_path = Path(args.report) if args.report else output_dir / "m5_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # 打印总结
    print(f"\n═══════════════════════════════════════", file=sys.stderr)
    print(f"📊 M5 视频生成总结", file=sys.stderr)
    print(f"═══════════════════════════════════════", file=sys.stderr)
    print(f"  总数: {summary['total']}", file=sys.stderr)
    print(f"  成功: {summary['ok']}", file=sys.stderr)
    print(f"  缺凭证: {summary['no_api_key']}", file=sys.stderr)
    print(f"  错误: {summary['errors']}", file=sys.stderr)
    print(f"  模式: {'mock' if use_mock else 'real'}", file=sys.stderr)
    print(f"  报告: {report_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
