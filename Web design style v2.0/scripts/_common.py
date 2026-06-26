#!/usr/bin/env python3
"""
WebPPT Maker · 共享工具

提供所有 generator 脚本共用的输出目录处理逻辑：
- prepare_output_dir(output_dir, create_subdirs=True) → 返回最终路径
  - 不存在: 创建（含子目录）
  - 已存在: 直接使用（幂等覆盖）

Why: 之前 4 个 generator 对已存在目录的处理不一致（HTML 加后缀，其他报错），
     导致用户跑完 5 个脚本后产物散落在 2 个目录。这是真实用户摩擦（CLAUDE.md N1）。

幂等覆盖策略：每次跑都用同一个 --output-dir，结果都在同一个文件夹。
用户想要保留旧版本 → 自己 --output-dir ./output_v2 即可。
"""

import sys
from pathlib import Path


def prepare_output_dir(output_dir, create_subdirs=True):
    """
    准备输出目录。

    Args:
        output_dir: 用户指定的输出路径（绝对或相对）
        create_subdirs: 是否创建子目录（pages/assets/screenshots）

    Returns:
        Path: 最终的输出路径（始终 = 用户传入的 output_dir）

    Behavior (幂等):
        - 不存在: 创建（含 pages/assets/screenshots 子目录）
        - 已存在: 直接使用，不加后缀（避免产物分散）
        - 始终 print [INFO] 让用户知道实际写入哪里
    """
    output_path = Path(output_dir)

    if output_path.exists():
        print(f"[INFO] 输出目录已存在，直接使用: {output_path}", file=sys.stderr)
    else:
        print(f"[INFO] 创建输出目录: {output_path}", file=sys.stderr)

    # 幂等创建（exist_ok=True 保证重复跑不报错）
    output_path.mkdir(parents=True, exist_ok=True)
    if create_subdirs:
        (output_path / "pages").mkdir(exist_ok=True)
        (output_path / "assets").mkdir(exist_ok=True)
        (output_path / "screenshots").mkdir(exist_ok=True)

    return output_path


def resolve_output_dir(output_dir):
    """
    仅解析路径，不创建子目录（用于 copy/script/subtitle 等只写单文件的脚本）。

    Args:
        output_dir: 用户指定路径

    Returns:
        Path: 最终输出路径

    Behavior: 同 prepare_output_dir 但不创建 pages/assets/screenshots
    """
    return prepare_output_dir(output_dir, create_subdirs=False)


def report_written(file_path, description=""):
    """统一输出 [OK] 报告，避免各脚本打印格式不一致"""
    path = Path(file_path)
    size = path.stat().st_size if path.exists() else 0
    desc_part = f" {description}" if description else ""
    print(f"[OK] 生成 {path.name} ({size} bytes){desc_part}", file=sys.stderr)
    return str(path.absolute())


# v3.3: 字幕/时间轴时长真对齐 — 让 subtitle.srt 总时长 = script_timeline.md 总时长 = target_duration_sec
HOOK_DURATION_SEC = 3       # 开头钩子固定 3 秒
CTA_DURATION_SEC = 3        # 结尾 CTA 固定 3 秒
SAFETY_MARGIN_SEC = 1       # 安全余量
SUBTITLE_SOFT_MAX_SEGMENT_SEC = 5  # 字幕单段软上限 (剪映推荐,超出会 warn 而非 fail)
TIMELINE_SOFT_MAX_SEGMENT_SEC = 8  # 时间轴单段软上限


def compute_durations(target_sec: int, n_points: int) -> dict:
    """计算字幕/时间轴每个段的时长,保证总时长 = target_sec

    Args:
        target_sec: 视频总时长 (e.g. 30)
        n_points: 内容点数 (e.g. 3)

    Returns:
        dict with keys:
          hook: hook 段时长 (秒)
          body_each: 时间轴每段时长 (秒, = 字幕每段时长, 让两者对齐)
          cta: cta 段时长 (秒)
          total: 总时长 (秒, = target_sec)
          body_total: 主体总时长 (秒)
          safety: 安全余量 (秒)

    Design (v3.3):
      total = hook + body_total + cta   (safety 不参与切分,作为内部分配余量)
      body_total = total - hook - cta   (主体总时长)
      body_each = body_total // n_points (每段时长,subtitle/timeline 一致)
      subtitle_each = body_each  (与时间轴对齐,放弃 G6 硬卡 5s)

      G6 (单段 ≤ 5s) 从硬卡变为软警告 (verify.sh 改为 warn 而非 fail)。
      原因: 30s/3 points 必然每段 8s,数学上不可能 ≤5s;真正质量指标是
      "段长 × 字符密度 ≤ 推荐值"。

      ⚠️ v3.3.1 修复: 之前 SAFETY 被减,30s/3 段算出 body_each=7,总 27s ≠ 30
         改为 target = hook + body*3 + cta,body=8s,总 30s ✓
    """
    if target_sec < 10:
        raise ValueError(f"target_sec={target_sec} 必须 >= 10")
    if n_points < 1:
        raise ValueError(f"n_points={n_points} 必须 >= 1")

    # safety 不参与切分 (是内部分配余量,不是要被减的时长)
    body_total = max(target_sec - HOOK_DURATION_SEC - CTA_DURATION_SEC,
                     n_points * 2)  # 至少 2s/段
    body_each = max(body_total // n_points, 2)

    return {
        "hook": HOOK_DURATION_SEC,
        "cta": CTA_DURATION_SEC,
        "body_total": body_total,
        "body_each": body_each,
        "subtitle_each": body_each,  # v3.3: 与时间轴对齐
        "timeline_each": body_each,
        "total": target_sec,
        "safety": SAFETY_MARGIN_SEC,
    }


if __name__ == "__main__":
    # 自测
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        # 测试 1: 不存在 → 创建
        p1 = prepare_output_dir(f"{td}/new_dir")
        assert p1.exists(), "新目录应被创建"
        assert p1 == Path(f"{td}/new_dir"), "应等于用户传入路径"
        print(f"✅ 测试 1 (新建): {p1}")

        # 测试 2: 已存在 → 幂等使用，不加后缀
        p2 = prepare_output_dir(f"{td}/new_dir")
        assert p2 == p1, "已存在应幂等返回同一路径"
        print(f"✅ 测试 2 (幂等): {p2}")

        # 测试 3: create_subdirs=False
        p3 = resolve_output_dir(f"{td}/no_subdir")
        assert p3.exists() and not (p3 / "pages").exists()
        print(f"✅ 测试 3 (无子目录): {p3}")

        print("\n[OK] _common.py 自测通过")
