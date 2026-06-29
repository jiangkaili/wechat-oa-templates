#!/usr/bin/env python3
"""Render real template previews via headless Chromium (no PIL mockups).

For each built-in template, compose a sample article with its own composer.py,
wrap it in a WeChat-article-width page, and screenshot it with Playwright.
Output: docs/images/preview_<template>.png

Usage:
    python3 scripts/render_previews.py
    python3 scripts/render_previews.py --width 420

Requires: playwright (pip install playwright && playwright install chromium)
"""
import os, sys, time, argparse, importlib.util

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = ["apple-minimalist", "card-layout", "dark-mode",
             "gradient-header", "tech-terminal", "warm-paper"]

# 各模板页面底色（与 composer 内主背景一致，防深色模板露白边）
PAGE_BG = {
    "apple-minimalist": "#FFFFFF", "card-layout": "#FFFFFF",
    "dark-mode": "#1D1D1F", "gradient-header": "#FFFFFF",
    "tech-terminal": "#0D1117", "warm-paper": "#FAF9F5",
}

# 高清无水印示例配图（Unsplash，免费可商用）
IMG = {
    "ai_brain": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800",
    "ai_robot": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800",
    "app_phone": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800",
    "headset_vr": "https://images.unsplash.com/photo-1593508512255-86ab42a8e620?w=800",
    "chip": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800",
    "server": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800",
    "startup": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=800",
    "growth": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
    "code": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800",
    "terminal": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=800",
    "book": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800",
    "coffee": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800",
}

# 每个模板用一套贴合其气质的独立内容（让画廊像 6 篇真实不同的文章，而非同一篇换皮）
SAMPLES = {
    # 纯净极简 → AI 大事件简报
    "apple-minimalist": {
        "title": "多模态登顶，一句解读", "vol": "AI.142",
        "sections": [{
            "heading": "24小时AI大事件",
            "items": [
                "新一代多模态模型发布，推理成本直降七成<br/>厂商官方博客披露，新架构把单位推理成本压到上一代的三成，长上下文吞吐显著提升，开发者可即刻在 API 调用。（6月29日）",
                "AI 助手接入操作系统，全局唤起改写交互<br/>系统级集成让用户在任意应用内一键唤起助手，隐私处理在端侧完成，被视为下一代人机交互的关键落子。（6月29日）",
            ],
            "images": [IMG["ai_brain"], IMG["ai_robot"]],
        }],
        "trends": [
            "趋势一：推理成本快速下探，应用层创业窗口打开，小团队也能负担规模化调用。",
            "趋势二：系统级 AI 集成成为巨头必争之地，入口之争重新开始。",
        ],
        "interaction": "系统级 AI 助手，你会用还是关掉？",
    },
    # 卡片盘点 → AI 工具/产品速览
    "card-layout": {
        "title": "本周 AI 工具，三连发", "vol": "TOOLS.07",
        "sections": [{
            "heading": "本周工具速览",
            "items": [
                "AI 视频剪辑工具上线，口播一键成片<br/>上传文稿即自动配音、配图、加字幕，三分钟产出竖屏短视频，免费额度足够个人创作者起步。（6月29日）",
                "空间计算头显开放开发者预览<br/>手势 + 眼动交互配合 AI 场景理解，办公与设计类应用率先适配，开发者社区一周新增数百个 demo。（6月29日）",
            ],
            "images": [IMG["app_phone"], IMG["headset_vr"]],
        }],
        "trends": [
            "趋势一：内容创作工具持续降低门槛，「想法到成片」的链路被压到分钟级。",
            "趋势二：空间计算从概念走向可用，杀手级应用仍待挖掘。",
        ],
        "interaction": "你最想要一个什么样的 AI 工具？",
    },
    # 科技暗黑 → 芯片/算力硬核
    "dark-mode": {
        "title": "算力暗战，谁主沉浮", "vol": "CHIP.21",
        "sections": [{
            "heading": "算力前线",
            "items": [
                "新一代 AI 加速卡流片成功，能效比翻倍<br/>采用先进封装与片上互联，单卡训练吞吐较上代提升一倍以上，量产时间表提前，供应链已开始备货。（6月29日）",
                "云厂商扩建超大规模 AI 集群<br/>新数据中心专为大模型训练设计，液冷与自研网络降低单位算力成本，租用价格有望随之走低。（6月29日）",
            ],
            "images": [IMG["chip"], IMG["server"]],
        }],
        "trends": [
            "趋势一：算力能效成为竞争核心，先进封装是下一个主战场。",
            "趋势二：训练成本下行，中小团队也将分到算力红利。",
        ],
        "interaction": "算力会不会像电费一样越来越便宜？",
    },
    # 活力渐变 → 创投/融资风向
    "gradient-header": {
        "title": "资本涌入，AI 创投热", "vol": "VC.33",
        "sections": [{
            "heading": "融资风向",
            "items": [
                "AI 应用层公司完成新一轮融资，估值大涨 +180%<br/>主打垂直行业的 AI 助手，付费转化率亮眼，本轮由头部基金领投，将用于扩张企业级销售团队。（6月29日）",
                "开源模型公司获战略投资，押注商业化<br/>以开源建立生态、企业版变现的路线获资本认可，新资金将投入推理优化与私有化部署能力。（6月29日）",
            ],
            "images": [IMG["startup"], IMG["growth"]],
        }],
        "trends": [
            "趋势一：资本从「模型层」向「应用层」迁移，能赚钱的产品更受青睐。",
            "趋势二：开源 + 企业版的商业模式逐渐跑通，估值逻辑被重估。",
        ],
        "interaction": "AI 创业，你更看好应用层还是模型层？",
    },
    # 终端黑客 → 开源项目雷达
    "tech-terminal": {
        "title": "开源雷达，本周高星", "vol": "OSS.58",
        "sections": [{
            "heading": "开源雷达",
            "items": [
                "本地优先代码助手登顶趋势榜<br/>无需上传代码即可补全与重构，支持企业自托管，文档完善，首周斩获过万 star，隐私党狂喜。（6月29日）",
                "轻量推理框架开源，树莓派也能跑大模型<br/>极致量化 + 内存优化，让边缘设备运行十亿级参数模型成为可能，社区一周贡献上百个适配。（6月29日）",
            ],
            "images": [IMG["code"], IMG["terminal"]],
        }],
        "trends": [
            "趋势一：本地优先与隐私成为开源工具的核心卖点。",
            "趋势二：边缘推理快速成熟，「人人可跑大模型」不再是口号。",
        ],
        "interaction": "你会把模型跑在云端还是自己的设备上？",
    },
    # 书卷暖纸 → 人文观点长读
    "warm-paper": {
        "title": "当 AI 学会写作，我们读什么", "vol": "READ.12",
        "sections": [{
            "heading": "深度观察",
            "items": [
                "AI 生成内容泛滥，「人味」反而成了稀缺品<br/>当文字可以批量生产，读者开始重新珍视真实的经历、笨拙的真诚与不完美的个人视角，这或许是创作者的新护城河。（6月29日）",
                "慢阅读回归：在信息洪流里重新学会专注<br/>越来越多人主动关闭推荐流，回到长文与纸书，把注意力当作需要保护的稀缺资源来经营。（6月29日）",
            ],
            "images": [IMG["book"], IMG["coffee"]],
        }],
        "trends": [
            "观察一：内容越廉价，真实与真诚越值钱。",
            "观察二：注意力是这个时代最该被守护的资产。",
        ],
        "interaction": "AI 时代，你还会为「人写的字」付费吗？",
    },
}


def load_composer(name):
    path = os.path.join(BASE, "templates", name, "composer.py")
    spec = importlib.util.spec_from_file_location(f"templates.{name}.composer", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.compose_html


def build_page(body_html, bg, width):
    """Wrap composer body into a full HTML page at WeChat article width."""
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:{bg}; width:{width}px;
         font-family:-apple-system,'PingFang SC','Helvetica Neue',Arial,sans-serif;
         -webkit-font-smoothing:antialiased; }}
</style></head><body>{body_html}</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=420, help="viewport width (WeChat article ~375-420)")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    out_dir = os.path.join(BASE, "docs", "images")
    os.makedirs(out_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name in TEMPLATES:
            compose = load_composer(name)
            data = dict(SAMPLES[name], style=name)  # 每个模板用自己的独立内容
            body = compose(data, {})
            html = build_page(body, PAGE_BG.get(name, "#FFFFFF"), args.width)

            page = browser.new_page(viewport={"width": args.width, "height": 800},
                                    device_scale_factor=2)  # retina = 锐利
            page.set_content(html, wait_until="networkidle")
            time.sleep(0.8)  # 等图片解码
            out = os.path.join(out_dir, f"preview_{name}.png")
            page.screenshot(path=out, full_page=True)
            page.close()
            print(f"✅ {name} -> {out}")
        browser.close()
    print("done")


if __name__ == "__main__":
    main()
