#!/usr/bin/env python3
"""选题记忆库 (Topic Memory) —— 让 AI 简报具备跨天的编辑记忆。

解决两个长期问题：
  ① 同质化：模型每天孤立生成，反复在「大厂+前沿模型+监管」打转。
  ② 凑数：24h 硬发机制下，没东西可写时容易重复昨天的选题。

工作方式（被 cron prompt 调用）：
  生成前：  python3 topic_memory.py recent [N]
            打印最近 N 天（默认7）已发选题摘要 + 高频实体统计，喂给模型做「别再选这些」的去重参考。
  发布后：  python3 topic_memory.py add <article.json>
            把当天选题指纹追加进 topic_memory.json，形成连续记忆。

存储文件: ~/projects/wechat_publisher/topic_memory.json
"""
import sys, os, json, re, glob
from collections import Counter
from datetime import datetime

BASE = os.path.expanduser("~/projects/wechat_publisher")
MEM_PATH = os.path.join(BASE, "topic_memory.json")

# 关注的核心实体（用于高频统计，提醒模型避免扎堆）
ENTITY_PATTERNS = [
    r'\b(?:GPT|Claude|Gemini|Llama|GLM|Qwen|DeepSeek|Mistral|Grok|Fable|Mythos)[\w.\-]*',
    r'(?:OpenAI|Anthropic|Google|DeepMind|Meta|Nvidia|英伟达|微软|Microsoft|苹果|Apple|'
    r'智谱|百度|阿里|腾讯|字节|HuggingFace|Hugging Face|特斯拉|Tesla|马斯克)',
]
# 主题标签关键词（用于主题多样性提醒）
THEME_KEYWORDS = {
    "监管管制": ["管控", "监管", "限制", "封禁", "出口管制", "合规", "禁令"],
    "模型发布": ["发布", "开源", "上线", "权重", "登顶", "霸榜", "trending"],
    "算力芯片": ["算力", "芯片", "GPU", "数据中心", "训练成本", "限流"],
    "融资商业": ["融资", "估值", "营收", "上市", "收购", "IPO"],
    "自进化Agent": ["自我进化", "递归", "agent", "智能体", "自动化", "哥德尔"],
    "安全对齐": ["安全", "对齐", "越狱", "幻觉", "对抗", "漏洞"],
    "应用落地": ["医疗", "金融", "教育", "自动驾驶", "机器人", "实用", "工具"],
}


def load_mem():
    if os.path.exists(MEM_PATH):
        try:
            return json.load(open(MEM_PATH, encoding="utf-8"))
        except Exception:
            pass
    return {"_comment": "选题记忆库:记录已发选题指纹,生成时读此文件去重+保证多样性",
            "entries": []}


def extract_entities(text):
    found = []
    for pat in ENTITY_PATTERNS:
        found += re.findall(pat, text)
    # 归一化 & 去重 & 清洗（去掉混入的中文句子片段）
    norm = []
    for e in found:
        e = e.strip()
        if e == "Hugging Face":
            e = "HuggingFace"
        # 英文型号名(GPT-5.6/GLM-5.2等)：截断尾部粘连的中文，只留 ASCII 型号
        m = re.match(r'^([A-Za-z][A-Za-z0-9.\-]*)', e)
        if m and re.search(r'[A-Za-z]', e):
            e = m.group(1).rstrip(".-")
        # 丢弃过长(>12字符)的纯中文片段（多半是句子误匹配）
        if not re.search(r'[A-Za-z]', e) and len(e) > 12:
            continue
        if e:
            norm.append(e)
    return sorted(set(norm))


def detect_themes(text):
    """按关键词命中【次数】排序，只取主导主题（top3且命中≥2次），
    避免一篇文章因零星关键词命中全部主题，导致去重信号失真。"""
    scored = []
    for theme, kws in THEME_KEYWORDS.items():
        cnt = sum(text.count(k) for k in kws)
        if cnt > 0:
            scored.append((theme, cnt))
    scored.sort(key=lambda x: -x[1])
    # 主导主题：命中≥2次的取前3；若都<2次，至少保留命中最高的1个
    dominant = [t for t, c in scored if c >= 2][:3]
    if not dominant and scored:
        dominant = [scored[0][0]]
    return dominant


def fulltext_of(d):
    parts = [d.get("title", ""), d.get("digest", "")]
    for sec in d.get("sections", []):
        for it in sec.get("items", []):
            parts.append(it)
    parts += d.get("trends", []) or []
    return " ".join(parts)


def cmd_recent(n=7):
    mem = load_mem()
    entries = mem.get("entries", [])
    # 取最近 n 天（按 date 排序后取尾部，但同日多条都保留）
    entries = sorted(entries, key=lambda x: x.get("date", ""))
    recent = entries[-n:] if len(entries) > n else entries

    print("=" * 64)
    print(f"选题记忆库 · 最近 {len(recent)} 条已发选题（务必避免重复）")
    print("=" * 64)
    if not recent:
        print("（暂无历史记录，首次运行）")
        return

    for e in recent:
        print(f"\n【{e.get('date','?')}  {e.get('vol','')}】{e.get('title','')}")
        if e.get("digest"):
            print(f"   摘要: {e['digest']}")
        if e.get("themes"):
            print(f"   主题: {', '.join(e['themes'])}")

    # 高频实体统计
    ent_counter = Counter()
    theme_counter = Counter()
    for e in recent:
        ent_counter.update(e.get("entities", []))
        theme_counter.update(e.get("themes", []))

    print("\n" + "-" * 64)
    print("⚠️ 近期高频实体（出现≥2次的，今天尽量换新面孔，别再扎堆）:")
    hot = [(k, c) for k, c in ent_counter.most_common() if c >= 2]
    print("   " + ("、".join(f"{k}×{c}" for k, c in hot) if hot else "（无明显扎堆）"))

    print("\n⚠️ 近期高频主题（出现≥2次的，今天有意识换角度）:")
    hot_t = [(k, c) for k, c in theme_counter.most_common() if c >= 2]
    print("   " + ("、".join(f"{k}×{c}" for k, c in hot_t) if hot_t else "（主题分布均衡）"))

    # 多样性建议：找出最近很少碰的主题
    covered = set(theme_counter.keys())
    fresh = [t for t in THEME_KEYWORDS if t not in covered]
    print("\n💡 近期【未覆盖】的主题方向（优先考虑，调节节奏，建议至少留1条接地气选题）:")
    print("   " + ("、".join(fresh) if fresh else "（所有主题近期都已覆盖）"))
    print("=" * 64)


def cmd_add(article_path):
    if not os.path.exists(article_path):
        print(f"❌ 找不到文章文件: {article_path}")
        sys.exit(1)
    d = json.load(open(article_path, encoding="utf-8"))
    text = fulltext_of(d)

    m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(article_path))
    date = m.group(1) if m else datetime.now().strftime("%Y-%m-%d")

    entry = {
        "date": date,
        "file": os.path.basename(article_path),
        "title": d.get("title", ""),
        "digest": d.get("digest", "")[:200],
        "headings": [s.get("heading", "") for s in d.get("sections", [])],
        "entities": extract_entities(text),
        "themes": detect_themes(text),
        "vol": d.get("vol", ""),
    }

    mem = load_mem()
    # 去重：同 file 已存在则覆盖
    mem["entries"] = [e for e in mem.get("entries", []) if e.get("file") != entry["file"]]
    mem["entries"].append(entry)
    mem["entries"].sort(key=lambda x: x.get("date", ""))
    # 只保留最近 60 条，防无限膨胀
    mem["entries"] = mem["entries"][-60:]

    with open(MEM_PATH, "w", encoding="utf-8") as fp:
        json.dump(mem, fp, ensure_ascii=False, indent=2)
    print(f"✅ 已记录选题指纹到记忆库: {entry['title']}")
    print(f"   主题: {', '.join(entry['themes']) or '(未识别)'}")
    print(f"   实体: {', '.join(entry['entities'][:8]) or '(未识别)'}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "recent":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        cmd_recent(n)
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("用法: python3 topic_memory.py add <article.json>")
            sys.exit(2)
        cmd_add(sys.argv[2])
    else:
        print(f"未知命令: {cmd}（支持 recent / add）")
        sys.exit(2)


if __name__ == "__main__":
    main()
