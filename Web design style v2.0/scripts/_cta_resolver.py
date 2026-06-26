#!/usr/bin/env python3
"""
WebPPT Maker · CTA 单一来源决议 (v3.3)

CLI > config > 主题默认 的优先级链。
4 个产物 (HTML / douyin_post.md / script_timeline.md / subtitle.srt) 都从这里取,
保证所有产物 CTA 文本完全一致 (N1 诚实契约)。
"""
import sys
from pathlib import Path

# 让脚本可独立运行 (python3 _cta_resolver.py)
sys.path.insert(0, str(Path(__file__).parent))
from _constants import DEFAULT_CTA_BY_STYLE


def resolve_cta(cli_cta: str, config_cta: str, style: str) -> str:
    """CTA 优先级: CLI > config > 主题默认

    Args:
        cli_cta: --cta 命令行参数 (可能为空字符串)
        config_cta: config.json cta_text 字段
        style: 主题名 (现代简约/知识科普/...)

    Returns:
        最终 CTA 文本 (trim 后)
    """
    cli = (cli_cta or "").strip()
    cfg = (config_cta or "").strip()
    if cli:
        return cli
    if cfg:
        return cfg
    return DEFAULT_CTA_BY_STYLE.get(style, DEFAULT_CTA_BY_STYLE["默认"])


if __name__ == "__main__":
    # CLI 自测: python3 _cta_resolver.py "扫码加我" "" "现代简约"
    args = sys.argv[1:]
    cli_cta = args[0] if len(args) > 0 else ""
    config_cta = args[1] if len(args) > 1 else ""
    style = args[2] if len(args) > 2 else "默认"
    print(resolve_cta(cli_cta, config_cta, style))