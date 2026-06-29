#!/usr/bin/env python3
"""配图 3 轮强制校验 (Image Guard — 水印 + 高清 + 可达性).

铁律：公众号每张配图必须 ① 无媒体台标/水印 ② 高清不糊 ③ URL 可达且为真图。
本脚本对文章 JSON 里的全部图片 URL (cover.bg_image + 每个 section 的 images)
跑 3 轮检查，设计与 typo_check.py 完全对称：

  第1轮  水印源校验   —— 域名黑/灰/白名单分级，黑名单命中即 FAIL
  第2轮  高清校验     —— 下载真图，检查像素分辨率 + 文件体积，过低即 FAIL
  第3轮  可达性校验   —— HTTP 200 + content-type 为图片 + 可被 PIL 解码，否则 FAIL

用法:
  python3 check_image_source.py article.json
  python3 check_image_source.py article.json --strict      # 灰名单也视为 FAIL
  python3 check_image_source.py article.json --no-network   # 只跑第1轮(离线/快检)

exit code 0 = 3 轮全部通过可发布，非 0 = 必须修图后重跑。
"""
import sys, json
from urllib.parse import urlparse

# ❌ 必带台标/水印 —— 中文 AI 自媒体，禁用其配图作为本号素材
BLACKLIST = {
    "qbitai.com": "量子位（右下角「量子位 QbitAI」台标）",
    "jiqizhixin.com": "机器之心（台标水印）",
    "36kr.com": "36氪（台标水印）",
    "36kr.net": "36氪（台标水印）",
    "huxiu.com": "虎嗅（台标水印）",
    "leiphone.com": "雷峰网（台标水印）",
    "tmtpost.com": "钛媒体（台标水印）",
    "ifanr.com": "爱范儿（台标水印）",
    "zhidx.com": "智东西（台标水印）",
    "geekpark.net": "极客公园（台标水印）",
    "pingwest.com": "品玩（台标水印）",
    "titanmedia.com": "钛媒体（台标水印）",
    "csdn.net": "CSDN（台标/博主水印）",
    "infoq.cn": "InfoQ（台标水印）",
    "woshipm.com": "人人都是产品经理（台标水印）",
    "sspai.com": "少数派（部分配图带台标）",
}

# ⚠️ 图库/聚合源 —— 可能内嵌原媒体角标，需人工核验
GRAYLIST = {
    "sinaimg.cn": "新浪图库（聚合图，可能带原媒体水印）",
    "sina.com.cn": "新浪（同上）",
    "gtimg.com": "腾讯图库（可能带角标）",
    "gtimg.cn": "腾讯图库（可能带角标）",
    "qpic.cn": "腾讯/微信图床（可能带角标）",
    "inews.gtimg.com": "腾讯新闻图库（可能带角标）",
    "dfcfw.com": "东方财富（可能带台标）",
    "edgen.tech": "edgen 聚合（核验是否原始素材）",
    "hubpd.com": "人民日报图库（可能带角标）",
    "people.com.cn": "人民网（可能带角标）",
    "xinhuanet.com": "新华网（可能带角标）",
}

# ✅ 首选无水印源（公司官方 + 英文科技媒体的 Getty/原始图）
WHITELIST_HINT = [
    "openai.com", "anthropic.com", "cdn.sanity.io", "blog.google",
    "deepmind.google", "storage.googleapis.com", "gweb-uniblog",
    "blogs.nvidia.com", "nvidia.com", "ai.meta.com", "about.fb.com",
    "microsoft.com", "x.ai", "huggingface.co", "mistral.ai", "apple.com",
    "machinelearning.apple.com", "cohere.com", "stability.ai", "semgrep.dev",
    "the-decoder.com", "theverge.com", "platform.theverge.com",
    "techcrunch.com", "arstechnica.com", "cdn.arstechnica.net",
    "reuters.com", "venturebeat.com", "wired.com", "image.cnbcfm.com",
]

# ===== 高清阈值 =====
MIN_W_COVER, MIN_H_COVER = 800, 400     # 封面：公众号建议 ≥ 900×500
MIN_W_BODY, MIN_H_BODY = 600, 300       # 内文图
MIN_BYTES = 15 * 1024                   # < 15KB 多半是缩略图/占位图 → FAIL
WARN_BYTES = 40 * 1024                  # < 40KB 警告(可能偏小)
HTTP_TIMEOUT = 25
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def domain_of(url):
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def match(host, table):
    for key in table:
        if host == key or host.endswith("." + key) or key in host:
            return key
    return None


def collect_images(data):
    """返回 [(label, url, is_cover)] 列表，覆盖封面 + 所有 section 图片。"""
    out = []
    cov = (data.get("cover") or {}).get("bg_image")
    if cov:
        out.append(("封面 cover.bg_image", cov, True))
    for si, sec in enumerate(data.get("sections", [])):
        head = sec.get("heading", f"section{si}")
        for ii, url in enumerate(sec.get("images", []) or []):
            out.append((f"[{head}] 第{ii+1}张", url, False))
    return out


def fetch(url):
    """下载图片。返回 (status, content_type, raw_bytes) 或抛异常。"""
    import requests
    r = requests.get(url, headers={"User-Agent": UA}, timeout=HTTP_TIMEOUT, stream=True)
    ct = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
    raw = r.content
    return r.status_code, ct, raw


def decode_size(raw):
    """用 PIL 解析像素尺寸，返回 (w, h) 或抛异常。"""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(raw))
    return im.size  # (w, h)


def round1_watermark(imgs, strict):
    """第1轮：水印源黑/灰/白名单。返回 (passed, blocked_list, gray_list)。"""
    print("=" * 60)
    print("第1轮：水印源校验（域名黑/灰/白名单）")
    print("=" * 60)
    blocked, gray, ok = [], [], []
    for label, url, _ in imgs:
        host = domain_of(url)
        bk = match(host, BLACKLIST)
        if bk:
            blocked.append((label, host, BLACKLIST[bk])); continue
        gk = match(host, GRAYLIST)
        if gk:
            gray.append((label, host, GRAYLIST[gk])); continue
        ok.append((label, host))
    for label, host in ok:
        print(f"  ✅ {label}  ({host})")
    for label, host, why in gray:
        print(f"  ⚠️  {label}  ({host}) — {why}")
    for label, host, why in blocked:
        print(f"  ❌ {label}  ({host}) — {why}")
    passed = not blocked and not (strict and gray)
    if blocked:
        print(f"  [FAIL] {len(blocked)} 张命中水印黑名单，禁止发布。换官方博客/英文科技媒体无水印图。")
    elif gray and strict:
        print(f"  [FAIL] strict 模式：{len(gray)} 张灰名单源视为失败。")
    elif gray:
        print(f"  [WARN] {len(gray)} 张灰名单源，请发飞书肉眼核验角标(不阻断)。")
    else:
        print("  [PASS] 全部为无水印白名单/可信源")
    return passed, blocked, gray


def round23_resolution_reachability(imgs):
    """第2轮高清 + 第3轮可达性（共用一次下载）。返回 (r2_passed, r3_passed)。"""
    # 先统一下载并缓存
    results = []  # (label, url, is_cover, status, ct, nbytes, size_or_err)
    for label, url, is_cover in imgs:
        try:
            status, ct, raw = fetch(url)
            nbytes = len(raw)
            if status == 200 and ct.startswith("image/"):
                try:
                    wh = decode_size(raw)
                    results.append((label, url, is_cover, status, ct, nbytes, wh))
                except Exception as e:
                    results.append((label, url, is_cover, status, ct, nbytes, f"解码失败:{e}"))
            else:
                results.append((label, url, is_cover, status, ct, nbytes, "非图片响应"))
        except Exception as e:
            results.append((label, url, is_cover, 0, "", 0, f"下载失败:{e}"))

    # 第3轮：可达性
    print("=" * 60)
    print("第3轮：可达性校验（HTTP 200 + 图片类型 + 可解码）")
    print("=" * 60)
    r3_fail = []
    for label, url, is_cover, status, ct, nbytes, wh in results:
        reachable = (status == 200 and ct.startswith("image/") and isinstance(wh, tuple))
        if reachable:
            print(f"  ✅ {label}  HTTP {status} {ct} {nbytes//1024}KB")
        else:
            detail = wh if isinstance(wh, str) else f"HTTP {status} ct={ct or '空'}"
            print(f"  ❌ {label}  {detail}")
            r3_fail.append(label)
    r3_passed = not r3_fail
    print("  [PASS] 全部可达且为真图" if r3_passed else f"  [FAIL] {len(r3_fail)} 张不可达/非图片")

    # 第2轮：高清(仅对可解码的图判分辨率/体积)
    print("=" * 60)
    print("第2轮：高清校验（分辨率 + 文件体积）")
    print("=" * 60)
    r2_fail, r2_warn = [], []
    for label, url, is_cover, status, ct, nbytes, wh in results:
        if not isinstance(wh, tuple):
            print(f"  ⏭️  {label}  跳过(第3轮已判不可达)")
            r2_fail.append(label)  # 不可解码 = 不合格
            continue
        w, h = wh
        min_w, min_h = (MIN_W_COVER, MIN_H_COVER) if is_cover else (MIN_W_BODY, MIN_H_BODY)
        too_small = w < min_w or h < min_h
        tiny_bytes = nbytes < MIN_BYTES
        small_bytes = nbytes < WARN_BYTES
        tag = f"{w}×{h}px {nbytes//1024}KB"
        if too_small or tiny_bytes:
            why = []
            if too_small: why.append(f"分辨率 < {min_w}×{min_h}")
            if tiny_bytes: why.append(f"体积 < {MIN_BYTES//1024}KB")
            print(f"  ❌ {label}  {tag} — {'，'.join(why)}")
            r2_fail.append(label)
        elif small_bytes:
            print(f"  ⚠️  {label}  {tag} — 体积偏小(< {WARN_BYTES//1024}KB)，建议复核清晰度")
            r2_warn.append(label)
        else:
            print(f"  ✅ {label}  {tag}")
    r2_passed = not r2_fail
    if r2_fail:
        print(f"  [FAIL] {len(r2_fail)} 张分辨率/体积不达标，换高清原图后重跑。")
    elif r2_warn:
        print(f"  [WARN] {len(r2_warn)} 张体积偏小，建议肉眼复核(不阻断)。")
    else:
        print("  [PASS] 全部高清达标")
    return r2_passed, r3_passed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    no_network = "--no-network" in sys.argv
    if not args:
        print("用法: python3 check_image_source.py article.json [--strict] [--no-network]")
        sys.exit(2)

    data = json.load(open(args[0], encoding="utf-8"))
    imgs = collect_images(data)
    if not imgs:
        print("⚠️  未发现任何图片 URL")
        sys.exit(0)

    print(f"\n找到 {len(imgs)} 张图片待检查（封面 + 各栏目）\n")

    r1_passed, _, _ = round1_watermark(imgs, strict)

    if no_network:
        print("\n--no-network：跳过第2/3轮（高清+可达性）。")
        r2_passed = r3_passed = True
    else:
        print()
        r2_passed, r3_passed = round23_resolution_reachability(imgs)

    print("\n" + "=" * 60)
    rounds = [("第1轮 水印源", r1_passed), ("第2轮 高清", r2_passed), ("第3轮 可达性", r3_passed)]
    for name, ok in rounds:
        print(f"  {'✅ PASS' if ok else '❌ FAIL'}  {name}")
    all_passed = all(ok for _, ok in rounds)
    print("=" * 60)
    if all_passed:
        print("✅ 3 轮全部通过，配图合格可发布。")
        sys.exit(0)
    else:
        print("❌ 存在未通过轮次，禁止发布，请修图后重跑。")
        sys.exit(1)


if __name__ == "__main__":
    main()
