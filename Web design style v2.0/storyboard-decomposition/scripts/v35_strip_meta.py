#!/usr/bin/env python3
"""
v35_strip_meta.py — v3.5 元注释剥离·AI 理解度优化

用法:
    python3 v35_strip_meta.py <file.txt>           # 单文件
    python3 v35_strip_meta.py <dir> --batch        # 批量目录下所有 .txt

功能:
    1. 标题精简：去除 (M11决策#XXX...) 等决策标注
    2. 段内元注释剥离：
       - **修正原版xxx** / **AI友好** / **避免双重失败**
       - **压缩原版8个微表情** / **🔴删xxx凭空细节**
       - (M11决策#XXX) / (M9 Gap-X) / (剧本原文...) 等带加粗的括号注解
    3. 粗体段元注释剥离（第二遍）：**xxx** 内含 元关键词 → 整段剥离
    4. 自检段外置：【本镜自检·M9+M12+M13+M14】整段删除
    5. 合规信息单点化：仅保留【合规】行，删除其他位置的"严禁字幕文字"重复
    6. 间隔号 → 句号（主体内容中的 ·）

    保留：
    - 主体信号（资产引用/场景空间坐标/镜头参数/画面描述/光影氛围/技术参数/音效/台词）
    - 物理数字（米/秒/度/mm/K/dB）
    - 剧本原词 100%
    - 合规信息（图片无法承载的）
"""

import sys
import re
from pathlib import Path


# === 元注释模式（精确匹配，优先级最高）===
META_PATTERNS = [
    # 标题中的决策标注
    (r'[（(]M11决策#\d+[^）)]*[）)]', ''),
    (r'[（(]M9 Gap-\d+[^）)]*[）)]', ''),
    (r'[（(]M12规则\d+[^）)]*[）)]', ''),
    (r'[（(]CUE[^）)]*[）)]', ''),
    (r'[（(]M\d+[^）)]*[）)]', ''),

    # 加粗元注释（带 ** 包裹）— 精确前缀匹配
    (r'\*\*修正原版[^*]+\*\*', ''),
    (r'\*\*AI友好[^*]*\*\*', ''),
    (r'\*\*AI友好·[^*]*\*\*', ''),
    (r'\*\*避免双重失败[^*]*\*\*', ''),
    (r'\*\*避免[^*]*双重失败[^*]*\*\*', ''),
    (r'\*\*避免[^*]*失败[^*]*\*\*', ''),
    (r'\*\*避免[^*]*AI[^*]*失败[^*]*\*\*', ''),
    (r'\*\*压缩原版\d+[^*]*\*\*', ''),
    (r'\*\*🔴删[^*]+\*\*', ''),
    (r'\*\*删[^*]*凭空细节[^*]*\*\*', ''),
    (r'\*\*删[^*]*凭空[^*]*\*\*', ''),
    (r'\*\*替代原版[^*]*\*\*', ''),
    (r'\*\*替代[^*]*色温数值[^*]*\*\*', ''),
    (r'\*\*替代[^*]*[^*]*\*\*', ''),
    (r'\*\*剧本原文[^*]*\*\*', ''),
    (r'\*\*剧本未提[^*]*\*\*', ''),
    (r'\*\*保留[^*]*[^*]*\*\*', ''),
    (r'\*\*长台词[^*]*AI友好[^*]*\*\*', ''),
    (r'\*\*9s长镜[^*]*\*\*', ''),
    (r'\*\*接近上限[^*]*\*\*', ''),
    (r'\*\*但每段单一动作[^*]*\*\*', ''),
    (r'\*\*升华断点可接受[^*]*\*\*', ''),
    (r'\*\*修正原版[^*]*场景突变[^*]*\*\*', ''),
    (r'\*\*修正原版[^*]*内心OS[^*]*\*\*', ''),
    (r'\*\*修正原版[^*]*字幕[^*]*\*\*', ''),
    (r'\*\*修正原版[^*]*小仇[^*]*\*\*', ''),
    (r'\*\*修正原版[^*]*刘一鸣[^*]*\*\*', ''),
    (r'\*\*修正[^*]*为[^*]*\*\*', ''),

    # 元注释单独（不带括号）
    (r'[（(]\*\*修正原版[^*]+[）)]', ''),
    (r'[（(]\*\*AI友好[^*]*[）)]', ''),
    (r'[（(]\*\*避免双重失败[）)]', ''),
    (r'[（(]\*\*压缩原版[^*]*[）)]', ''),
    (r'[（(]\*\*🔴删[^*]+[）)]', ''),
    (r'[（(]\*\*删[^*]*凭空细节[）)]', ''),
    (r'[（(]\*\*剧本未提[）)]', ''),
    (r'[（(]\*\*剧本原文[^*]*[）)]', ''),

    # 自检段整段
    (r'【本镜自检[^\n]*\n(?:.*\n)*?(?=\n*|\Z)', ''),
    (r'【本镜自检·[^\n]*', ''),
]


# === 元注释关键词（粗体段第二遍剥离用）===
# 任何 **xxx** 内含下列模式之一 → 整段剥离
META_BOLD_PATTERNS = [
    r'M\d+\s*决策',
    r'M\d+\s*Gap',
    r'M\d+\s*规则',
    r'决策#\d+',
    r'Gap-\d+',
    r'规则\d+',
    r'修正原版',
    r'AI友好',
    r'避免.{0,15}失败',
    r'避免.{0,15}双重',
    r'压缩原版',
    r'🔴',
    r'凭空',
    r'替代原版',
    r'剧本未提',
    r'9s长镜',
    r'接近上限',
    r'升华断点可接受',
    r'场景突变',
    r'\d+个微表情',
    r'微表情合并',
    r'微表情压缩',
    r'内心OS.{0,15}(字幕|时间|安排)',
    r'内心OS.{0,15}不合理',
    r'内心OS.{0,15}修正',
    r'修正.{0,15}内心OS',
    r'修正.{0,15}小仇',
    r'修正.{0,15}刘一鸣',
    r'修正.{0,15}字幕',
    r'修正.{0,15}场景',
    r'删.{0,5}凭空',
    r'删.{0,5}细节',
    r'压缩原版',
]


# 合规信息合并模式
COMPLIANCE_PATTERN = re.compile(
    r'(?:严禁字幕文字[^。\n]*[。\n]?|'
    r'AI画面严禁[^。\n]*[。\n]?|'
    r'AI提示词严禁[^。\n]*[。\n]?|'
    r'画面中不出现任何文字或字幕[^。\n]*[。\n]?|'
    r'所有字幕后期PR/AE叠加[^。\n]*[。\n]?|'
    r'AI画面保持纯净[^。\n]*[。\n]?)',
    re.MULTILINE
)


def strip_meta_in_line(line):
    """剥离单行内的元注释（两遍：精确模式 + 粗体元注释）"""
    # 1. 保护引号内容（避免误剥离）
    quoted = []
    def protect(m):
        quoted.append(m.group(0))
        return f"\x00Q{len(quoted)-1}\x00"
    line = re.sub(r'"[^"]*"', protect, line)
    line = re.sub(r"'[^']*'", protect, line)

    # 2. 应用精确元注释模式
    for pattern, replacement in META_PATTERNS:
        line = re.sub(pattern, replacement, line)

    # 3. 第二遍：粗体段元注释剥离
    def bold_replacer(m):
        content = m.group(1)
        for kw in META_BOLD_PATTERNS:
            if re.search(kw, content):
                return ""  # 剥离
        return m.group(0)  # 保留

    line = re.sub(r'\*\*([^*]+)\*\*', bold_replacer, line)

    # 3.5 第三遍：括号内含元关键词 → 整段剥离
    paren_meta_keywords = (
        'M11决策', 'M9 Gap', 'M12规则',
        '修正原版', 'AI友好', '压缩原版', '🔴',
        '凭空', '替代原版', '剧本未提', '9s长镜', '接近上限',
        '升华断点可接受', '场景突变', '微表情', '内心OS字幕', '内心OS时间',
    )
    def paren_replacer(m):
        content = m.group(1)
        for kw in paren_meta_keywords:
            if kw in content:
                return ""  # 剥离
        return m.group(0)  # 保留

    line = re.sub(r'[（(]([^）)]*)[）)]', paren_replacer, line)

    # 4. 还原引号
    for i, q in enumerate(quoted):
        line = line.replace(f"\x00Q{i}\x00", q)

    # 5. 清理残留
    line = clean_residuals(line)
    return line


def clean_residuals(line):
    """清理元注释剥离后的残留"""
    # 空括号（）/（ ）
    line = re.sub(r'[（(]\s*[）)]', '', line)
    # 括号内只有标点（，）/+）等
    line = re.sub(r'[（(]\s*[，,+\s]+\s*[）)]', '', line)
    # 多个连续 ，
    line = re.sub(r'，\s*，+', '，', line)
    # 多个连续 +
    line = re.sub(r'\+\s*\++', '+', line)
    # +紧跟 ，
    line = re.sub(r'\+\s*，', '，', line)
    line = re.sub(r'，\s*\+', '，', line)
    # 行尾 ，
    line = re.sub(r'，\s*$', '', line.rstrip())
    # 行尾 +
    line = re.sub(r'\+\s*$', '', line.rstrip())
    # 行首 ，
    line = re.sub(r'^\s*，\s*', '', line)
    # 行首 +
    line = re.sub(r'^\s*\+\s*', '', line)
    # （后面紧跟 ，
    line = re.sub(r'[（(]\s*，\s*', '（', line)
    # ）前面紧跟 ，
    line = re.sub(r'，\s*[）)]', '）', line)
    # 多个空格
    line = re.sub(r' {2,}', ' ', line)
    # 双重逗号）  → ）
    line = re.sub(r'）\s*，', '）', line)
    # （，  → （
    line = re.sub(r'[（(]\s*，\s*([^，。；）)])', r'（\1', line)
    return line


def strip_self_check_section(text):
    """剥离【本镜自检...】整段"""
    pattern = r'【本镜自检.*?(?=\Z)'
    text = re.sub(pattern, '', text, flags=re.DOTALL)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.rstrip() + '\n'


def consolidate_compliance(text):
    """合规信息单点化：只保留第一处，其余删除"""
    matches = list(COMPLIANCE_PATTERN.finditer(text))
    if len(matches) <= 1:
        return text

    first = matches[0]
    result = text[:first.end()]
    last_end = first.end()
    for m in matches[1:]:
        result += text[last_end:m.start()]
        last_end = m.end()
    result += text[last_end:]
    return result


def replace_separator_in_body(text):
    """主体内容中的间隔号 · 替换为逗号（保留中英文标点的语义清晰）"""
    lines = text.split('\n')
    in_metadata_section = False
    result = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('【合规保留】') or stripped.startswith('【合规】'):
            in_metadata_section = False
            result.append(line)
            continue

        if stripped.startswith('【参考_') or stripped.startswith('【人物_') or stripped.startswith('【道具_') or stripped.startswith('【场景_'):
            in_metadata_section = True
            result.append(line)
            continue

        if not in_metadata_section:
            line = re.sub(r'·', '，', line)

        result.append(line)

    return '\n'.join(result)


def strip_title_meta(text):
    """剥离标题中的决策标注 + 所有括号注解（v3.5 治本：标题只保留镜号+主题+CUE+时长）"""
    lines = text.split('\n')
    if lines:
        title = lines[0]
        # 1. 剥离 M11决策/M9 Gap/M12规则/CUE 决策标注
        title = re.sub(r'[（(]M11决策#[^）)]*[）)]', '', title)
        title = re.sub(r'[（(]M9 Gap-[^）)]*[）)]', '', title)
        title = re.sub(r'[（(]M12规则[^）)]*[）)]', '', title)
        title = re.sub(r'[（(]CUE[^）)]*[）)]', '', title)
        # 2. 剥离所有括号注解（v3.5 治本：标题不应有 meta-content）
        # 例如：（戏剧断点，全剧第一个风格切换）
        title = re.sub(r'[（(][^）)]*[）)]', '', title)
        # 3. 间隔号 → 逗号
        title = re.sub(r'·', '，', title)
        title = re.sub(r'\s+', ' ', title).strip()
        title = re.sub(r'，\s*$', '', title)
        title = re.sub(r'，\s*，', '，', title)
        lines[0] = title

    return '\n'.join(lines)


def clean_extra_spaces(text):
    """清理多余空行和空格"""
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r' +$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n\s+\n', '\n\n', text)
    return text


def refactor_file(file_path):
    """重构单文件：v3.5 元注释剥离"""
    text = Path(file_path).read_text(encoding="utf-8")
    original_text = text

    # 1. 标题精简
    text = strip_title_meta(text)

    # 2. 自检段剥离（整段删除）
    text = strip_self_check_section(text)

    # 3. 行内元注释剥离
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(strip_meta_in_line(line))
    text = '\n'.join(new_lines)

    # 4. 合规信息单点化
    text = consolidate_compliance(text)

    # 5. 间隔号替换（主体内容）
    text = replace_separator_in_body(text)

    # 6. 清理多余空格
    text = clean_extra_spaces(text)

    original_len = len(original_text)
    new_len = len(text)

    Path(file_path).write_text(text, encoding="utf-8")

    return {
        "file": str(file_path),
        "original_len": original_len,
        "new_len": new_len,
        "saved_chars": original_len - new_len,
        "saved_pct": (original_len - new_len) * 100 // original_len if original_len else 0,
    }


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 v35_strip_meta.py <file.txt>")
        print("  python3 v35_strip_meta.py <dir> --batch")
        sys.exit(1)

    target = Path(sys.argv[1])
    is_batch = "--batch" in sys.argv

    if target.is_file():
        results = [refactor_file(target)]
    elif target.is_dir() and is_batch:
        results = [refactor_file(f) for f in sorted(target.glob("*.txt"))]
    else:
        print(f"错误：{target} 不是文件或目录（--batch）")
        sys.exit(1)

    print("=" * 70)
    print("v3.5 元注释剥离·AI 理解度优化报告")
    print("=" * 70)

    total_original = sum(r["original_len"] for r in results)
    total_new = sum(r["new_len"] for r in results)
    total_saved = total_original - total_new

    for r in results:
        print(f"\n✅ {Path(r['file']).name}")
        print(f"   字数: {r['original_len']} → {r['new_len']} (节省 {r['saved_chars']} 字, -{r['saved_pct']}%)")

    print(f"\n" + "=" * 70)
    print(f"总计：{len(results)} 文件")
    print(f"  原始总字数: {total_original}")
    print(f"  优化后总字数: {total_new}")
    print(f"  总节省: {total_saved} 字 (-{total_saved * 100 // total_original if total_original else 0}%)")
    print("=" * 70)


if __name__ == "__main__":
    main()
