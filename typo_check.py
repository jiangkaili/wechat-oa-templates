#!/usr/bin/env python3
"""Automated Chinese typo scanner for wechat-oa-templates.

Runs 3 rounds of checking:
  1. Known error-pattern scan (50+ wrong→correct pairs)
  2. Field-by-field extraction and review of all Chinese text in JSON files
  3. Documentation files + special checks (登陆/登录, 帐号/账号, duplicate punctuation)

Usage:
    python3 scripts/typo_check.py [project_dir]

If project_dir is omitted, defaults to ~/projects/wechat_publisher.

Exit code 0 = no errors found, 1 = errors found.
"""
import json
import os
import re
import sys

# ============================================================
# Known error patterns (wrong → correct)
# ============================================================
ERROR_PATTERNS = {
    # 人名
    "周鸿社": "周鸿祎",
    "周鸿韦": "周鸿祎",
    # 公司名
    "字芎": "字节",
    "谷哥": "谷歌",
    # 产品名
    "屠龙凤": "屠龙锋",
    "屠龙峰": "屠龙锋",
    # 术语
    "论料": "论文",
    "多太态": "多模态",
    "多模太": "多模态",
    "推里": "推理",
    "竞技能": "竞技场",
    # 同音字
    "发步": "发布",
    "登鼎": "登顶",
    "将低": "降低",
    "超跃": "超越",
    "支迟": "支持",
    "须可": "许可",
    "破白万": "破百万",
    "逼进": "逼近",
    "布署": "部署",
    "持须": "持续",
    "下绛": "下降",
    "剪报": "简报",
    "摸板": "模板",
    "图创": "图床",
    "览加载": "懒加载",
    "蓝目": "栏目",
    "郑文": "正文",
    "摘腰": "摘要",
    "数名": "署名",
    "风面": "封面",
    "材剪": "裁剪",
    "限治": "限制",
    "配制": "配置",
    "评证": "凭证",
    "依懒": "依赖",
    "供献": "贡献",
    "验正": "验证",
    "修付": "修复",
    "改近": "改进",
    # 形近字
    "己知": "已知",
    "己经": "已经",
    "竟技": "竞技",
    "竟赛": "竞赛",
    "登陆": "登录",
    "帐号": "账号",
    "帐户": "账户",
    # 重复标点/字
    "。。": "。",
    "，，": "，",
    "；；": "；",
    "：：": "：",
    "、、": "、",
    "的的": "的",
    "了了": "了",
    "是是": "是",
    "在在": "在",
}

# Special context-sensitive checks (word → should be, but flag if in wrong context)
CONTEXT_CHECKS = {
    "登陆": ("登录", "always wrong in tech context"),
    "帐号": ("账号", "always wrong in tech context"),
    "帐户": ("账户", "always wrong in tech context"),
}


def find_chinese_files(base_dir):
    """Find all JSON and Markdown files with Chinese content."""
    files = []
    # Template example.json files
    templates_dir = os.path.join(base_dir, "templates")
    if os.path.isdir(templates_dir):
        for style in os.listdir(templates_dir):
            style_dir = os.path.join(templates_dir, style)
            if not os.path.isdir(style_dir):
                continue
            for fname in ["example.json", "README.md"]:
                path = os.path.join(style_dir, fname)
                if os.path.exists(path):
                    files.append(path)
    # _shared.py (for docstrings)
    shared = os.path.join(templates_dir, "_shared.py")
    if os.path.exists(shared):
        files.append(shared)
    # Root files
    for fname in ["README.md", "README.en.md", "CONTRIBUTING.md"]:
        path = os.path.join(base_dir, fname)
        if os.path.exists(path):
            files.append(path)
    # examples/
    examples_dir = os.path.join(base_dir, "examples")
    if os.path.isdir(examples_dir):
        for fname in os.listdir(examples_dir):
            if fname.endswith(".json"):
                files.append(os.path.join(examples_dir, fname))
    return files


def has_chinese(text):
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def round1_pattern_scan(files):
    """Round 1: Scan all files for known error patterns."""
    print("=" * 60)
    print("第1轮：已知错误模式扫描")
    print("=" * 60)
    errors = []
    for path in files:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for wrong, correct in ERROR_PATTERNS.items():
            if wrong in content:
                for i, line in enumerate(content.split("\n"), 1):
                    if wrong in line:
                        errors.append((path, i, wrong, correct, line.strip()[:80]))
    if errors:
        for path, lineno, wrong, correct, context in errors:
            print(f"  [!] {os.path.relpath(path)}:L{lineno}: 「{wrong}」→「{correct}」 | {context}")
    else:
        print("  [PASS] 未发现已知错误模式")
    print(f"  扫描文件数: {len(files)}, 发现错误: {len(errors)}")
    return errors


def round2_field_review(base_dir):
    """Round 2: Extract and review every Chinese text field in JSON files."""
    print("\n" + "=" * 60)
    print("第2轮：逐条字段审查")
    print("=" * 60)
    errors = []

    json_files = []
    # Template examples
    templates_dir = os.path.join(base_dir, "templates")
    if os.path.isdir(templates_dir):
        for style in os.listdir(templates_dir):
            path = os.path.join(templates_dir, style, "example.json")
            if os.path.exists(path):
                json_files.append(path)
    # examples/
    examples_dir = os.path.join(base_dir, "examples")
    if os.path.isdir(examples_dir):
        for fname in os.listdir(examples_dir):
            if fname.endswith(".json"):
                json_files.append(os.path.join(examples_dir, fname))

    for path in json_files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        texts = []
        for field in ["title", "digest", "author", "vol"]:
            val = data.get(field, "")
            if val:
                texts.append((field, val))
        for i, sec in enumerate(data.get("sections", [])):
            texts.append((f"sec[{i}].heading", sec.get("heading", "")))
            for j, item in enumerate(sec.get("items", [])):
                texts.append((f"sec[{i}].items[{j}]", item))
        for k, trend in enumerate(data.get("trends", [])):
            texts.append((f"trends[{k}]", trend))

        for field, text in texts:
            if not has_chinese(text):
                continue
            for wrong, correct in ERROR_PATTERNS.items():
                if wrong in text:
                    errors.append((os.path.relpath(path), field, wrong, correct))
                    print(f"  [!] {os.path.relpath(path)} [{field}]: 「{wrong}」→「{correct}」")

    if not errors:
        print("  [PASS] 逐条字段审查未发现错误")
    print(f"  审查JSON文件数: {len(json_files)}, 发现错误: {len(errors)}")
    return errors


def round3_doc_check(base_dir):
    """Round 3: Documentation files + special checks."""
    print("\n" + "=" * 60)
    print("第3轮：文档 + 专项检查")
    print("=" * 60)
    errors = []

    doc_files = []
    for fname in ["README.md", "README.en.md", "CONTRIBUTING.md"]:
        path = os.path.join(base_dir, fname)
        if os.path.exists(path):
            doc_files.append(path)
    # Template READMEs
    templates_dir = os.path.join(base_dir, "templates")
    if os.path.isdir(templates_dir):
        for style in os.listdir(templates_dir):
            path = os.path.join(templates_dir, style, "README.md")
            if os.path.exists(path):
                doc_files.append(path)

    for path in doc_files:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        fname = os.path.relpath(path)
        file_errors = []
        for wrong, correct in ERROR_PATTERNS.items():
            if wrong in content:
                for i, line in enumerate(content.split("\n"), 1):
                    if wrong in line:
                        file_errors.append((i, wrong, correct))
                        errors.append((fname, wrong, correct))
        if file_errors:
            print(f"  [!] {fname}:")
            for lineno, wrong, correct in file_errors:
                print(f"      L{lineno}: 「{wrong}」→「{correct}」")
        else:
            print(f"  [PASS] {fname}")

    # Special checks
    print("\n  专项检查:")
    special_errors = 0
    for path in doc_files + [os.path.join(base_dir, "templates", s, "example.json")
                             for s in os.listdir(templates_dir) if os.path.isdir(os.path.join(templates_dir, s))]:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for wrong, correct in CONTEXT_CHECKS.items():
            if wrong in content:
                print(f"  [!] {os.path.relpath(path)}: 「{wrong}」→「{correct}」")
                special_errors += 1
    if special_errors == 0:
        print("    [PASS] 登陆/帐号/帐户 专项检查通过")

    print(f"\n  文档文件数: {len(doc_files)}, 发现错误: {len(errors) + special_errors}")
    return errors + [("doc", w, c) for w, (c, _) in CONTEXT_CHECKS.items()] * special_errors


def main():
    base_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/projects/wechat_publisher")
    if not os.path.isdir(base_dir):
        print(f"ERROR: directory not found: {base_dir}")
        sys.exit(1)

    print(f"项目目录: {base_dir}\n")
    files = find_chinese_files(base_dir)
    print(f"找到 {len(files)} 个文件待检查\n")

    e1 = round1_pattern_scan(files)
    e2 = round2_field_review(base_dir)
    e3 = round3_doc_check(base_dir)

    total = len(e1) + len(e2) + len(e3)
    print("\n" + "=" * 60)
    print(f"3轮检查完成，共发现 {total} 个错误")
    print("=" * 60)
    sys.exit(1 if total > 0 else 0)


if __name__ == "__main__":
    main()
