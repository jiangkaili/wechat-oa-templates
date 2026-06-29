#!/usr/bin/env python3
"""事实核验 3 轮闸门 (Fact Guard) —— 抓「幻觉式新闻」。

铁律：24h 硬发机制下，模型没真新闻可写时容易编造——精确到小数点的假数字、
不存在的产品名、张冠李戴的公司。一条假新闻就能毁掉公众号信誉。本闸门强制
每条新闻必须能追溯到真实可达的原始来源，与 typo_check / check_image_source
完全对称（exit 0 才放行）。

核验对象：JSON 里每个 section 的每条 item，必须在 section 的 "sources" 数组里
有等长、一一对应的来源 URL（与 images 数组同构）。

  第1轮  来源完备性  —— 每条 item 必须有对应的非空 source URL，缺失即 FAIL
  第2轮  来源可达性  —— source URL 必须 HTTP 200 可访问，超时/404/5xx 即 FAIL
  第3轮  内容印证    —— 抓取来源正文，检查是否包含该新闻的核心实体/数字，
                       命中率过低 = 疑似来源对不上内容(张冠李戴/编造) FAIL

用法:
  python3 fact_check.py article.json
  python3 fact_check.py article.json --strict       # 第3轮印证命中阈值提高
  python3 fact_check.py article.json --no-network    # 只跑第1轮(离线/快检)

exit code 0 = 3 轮全部通过可发布，非 0 = 必须核实/补来源后重跑。

—— JSON 需要的新字段（与 images 同构）——
  "sections": [
    {
      "heading": "24小时AI大事件",
      "items":   ["标题<br/>正文（6月29日）", ...],
      "images":  ["https://图片URL", ...],
      "sources": ["https://原始新闻来源URL", ...]   ← 新增，与 items 等长
    }
  ]
"""
import sys, json, re
from urllib.parse import urlparse

HTTP_TIMEOUT = 25
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

# 第3轮内容印证：从 item 正文里抽取「可核验事实锚点」用于在来源页里比对
ENTITY_PAT = [
    r'\b(?:GPT|Claude|Gemini|Llama|GLM|Qwen|DeepSeek|Mistral|Grok|Fable|Mythos)[\w.\-]*',
    r'(?:OpenAI|Anthropic|Google|DeepMind|Meta|Nvidia|Microsoft|HuggingFace|Hugging Face|'
    r'Semgrep|Cursor|Tesla|Apple|Mistral|Cohere|Stability)',
]
# 印证命中阈值：抽取的锚点中，至少多少比例能在来源页正文里找到
MIN_HIT_RATIO = 0.34          # 普通模式
MIN_HIT_RATIO_STRICT = 0.50   # --strict


def domain_of(url):
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def first_line_title(item):
    """item 形如 '标题<br/>正文...'，取标题部分（用于报告显示）。"""
    return re.split(r'<br\s*/?>', item, maxsplit=1)[0].strip()[:40]


def collect_items(data):
    """返回 [(label, item_text, source_url_or_None)] —— 覆盖所有 section 的每条。"""
    out = []
    for si, sec in enumerate(data.get("sections", [])):
        head = sec.get("heading", f"section{si}")
        items = sec.get("items", []) or []
        sources = sec.get("sources", []) or []
        for ii, item in enumerate(items):
            src = sources[ii] if ii < len(sources) else None
            out.append((f"[{head}] 第{ii+1}条「{first_line_title(item)}」", item, src))
    return out


def extract_anchors(item_text):
    """从正文抽取可核验锚点：英文实体名 + 显著数字(百分比/参数量/下载量等)。"""
    anchors = []
    for pat in ENTITY_PAT:
        for m in re.findall(pat, item_text):
            m = m.strip()
            mm = re.match(r'^([A-Za-z][A-Za-z0-9.\-]*)', m)
            anchors.append((mm.group(1).rstrip(".-") if mm else m))
    # 显著数字：百分比、带B/万/亿的量、版本号
    anchors += re.findall(r'\d+\.?\d*\s*%', item_text)
    anchors += re.findall(r'\d+\.?\d*\s*[BbMm](?:illion)?\b', item_text)
    # 去重、丢弃太短的
    uniq = []
    for a in anchors:
        a = a.strip()
        if len(a) >= 2 and a not in uniq:
            uniq.append(a)
    return uniq[:8]  # 最多取8个锚点比对，够判断即可


def fetch_text(url):
    """抓取来源页，返回 (status, plain_text) 或抛异常。"""
    import requests
    r = requests.get(url, headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT)
    txt = ""
    if r.status_code == 200:
        # 粗去标签，只留可比对的可见文本
        html = r.text
        html = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.I)
        html = re.sub(r'<style[\s\S]*?</style>', ' ', html, flags=re.I)
        txt = re.sub(r'<[^>]+>', ' ', html)
        txt = re.sub(r'\s+', ' ', txt)
    return r.status_code, txt


def round1_completeness(items):
    """第1轮：来源完备性。返回 (passed, missing_labels)。"""
    print("=" * 60)
    print("第1轮：来源完备性（每条新闻必须有可追溯的来源 URL）")
    print("=" * 60)
    missing = []
    for label, _item, src in items:
        if not src or not str(src).strip() or not str(src).startswith("http"):
            print(f"  ❌ {label}  缺少来源 URL")
            missing.append(label)
        else:
            print(f"  ✅ {label}  → {domain_of(src)}")
    passed = not missing
    if missing:
        print(f"  [FAIL] {len(missing)} 条缺来源。每条新闻必须在 section.sources 里给出原始链接。")
    else:
        print("  [PASS] 全部条目都有来源 URL")
    return passed, missing


def round23_reach_corroborate(items, strict):
    """第2轮可达性 + 第3轮内容印证（共用一次抓取）。返回 (r2_passed, r3_passed)。"""
    threshold = MIN_HIT_RATIO_STRICT if strict else MIN_HIT_RATIO
    fetched = []  # (label, item, src, status, text, err)
    for label, item, src in items:
        if not src or not str(src).startswith("http"):
            fetched.append((label, item, src, 0, "", "无来源"))
            continue
        try:
            status, text = fetch_text(src)
            fetched.append((label, item, src, status, text, None))
        except Exception as e:
            fetched.append((label, item, src, 0, "", f"抓取失败:{e}"))

    # 第2轮：可达性
    print("=" * 60)
    print("第2轮：来源可达性（HTTP 200）")
    print("=" * 60)
    r2_fail = []
    for label, item, src, status, text, err in fetched:
        if status == 200:
            print(f"  ✅ {label}  HTTP 200")
        else:
            print(f"  ❌ {label}  {err or f'HTTP {status}'}")
            r2_fail.append(label)
    r2_passed = not r2_fail
    print("  [PASS] 全部来源可达" if r2_passed else f"  [FAIL] {len(r2_fail)} 条来源不可达，换可访问的权威来源。")

    # 第3轮：内容印证
    print("=" * 60)
    print(f"第3轮：内容印证（来源正文需含新闻锚点，命中率 ≥ {int(threshold*100)}%）")
    print("=" * 60)
    r3_fail, r3_warn = [], []
    for label, item, src, status, text, err in fetched:
        if status != 200 or not text:
            print(f"  ⏭️  {label}  跳过(第2轮已判不可达)")
            r3_fail.append(label)
            continue
        anchors = extract_anchors(item)
        if not anchors:
            print(f"  ⚠️  {label}  未能从正文抽到可核验锚点，人工复核")
            r3_warn.append(label)
            continue
        low = text.lower()
        hits = [a for a in anchors if a.lower() in low]
        ratio = len(hits) / len(anchors)
        tag = f"{len(hits)}/{len(anchors)} 锚点命中 ({int(ratio*100)}%)"
        if ratio >= threshold:
            print(f"  ✅ {label}  {tag}")
        else:
            miss = [a for a in anchors if a not in hits]
            print(f"  ❌ {label}  {tag} — 来源页未提及: {', '.join(miss[:5])}（疑似张冠李戴/编造，务必人工核实）")
            r3_fail.append(label)
    r3_passed = not r3_fail
    if r3_fail:
        print(f"  [FAIL] {len(r3_fail)} 条来源与内容对不上，核实后改正或换源。")
    elif r3_warn:
        print(f"  [WARN] {len(r3_warn)} 条无法自动印证，建议人工复核(不阻断)。")
    else:
        print("  [PASS] 全部条目来源与内容印证一致")
    return r2_passed, r3_passed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    no_network = "--no-network" in sys.argv
    if not args:
        print("用法: python3 fact_check.py article.json [--strict] [--no-network]")
        sys.exit(2)

    data = json.load(open(args[0], encoding="utf-8"))
    items = collect_items(data)
    if not items:
        print("⚠️  未发现任何新闻条目")
        sys.exit(0)

    print(f"\n找到 {len(items)} 条新闻待核验（覆盖各栏目）\n")

    r1_passed, _ = round1_completeness(items)

    if no_network:
        print("\n--no-network：跳过第2/3轮（可达性+内容印证）。")
        r2_passed = r3_passed = True
    else:
        print()
        r2_passed, r3_passed = round23_reach_corroborate(items, strict)

    print("\n" + "=" * 60)
    rounds = [("第1轮 来源完备", r1_passed), ("第2轮 可达性", r2_passed), ("第3轮 内容印证", r3_passed)]
    for name, ok in rounds:
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  {name}")
    all_passed = all(ok for _, ok in rounds)
    print("=" * 60)
    if all_passed:
        print("✅ 3 轮全部通过，事实可追溯，可发布。")
        sys.exit(0)
    else:
        print("❌ 存在未通过轮次，禁止发布，请核实事实/补来源后重跑。")
        sys.exit(1)


if __name__ == "__main__":
    main()
