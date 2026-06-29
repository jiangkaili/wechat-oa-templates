#!/usr/bin/env python3
"""Render the hero gallery image (docs/images/hero_templates.png) via Chromium.

Places all 6 template previews side by side as phone mockups in one banner,
so the README top image showcases real rendered differences (no PIL mockups).

Usage: python3 scripts/render_hero.py
Run AFTER render_previews.py (it consumes the per-template PNGs).
"""
import os, base64, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, "docs", "images")
TEMPLATES = [
    ("apple-minimalist", "Apple Minimalist"),
    ("card-layout", "Card Layout"),
    ("dark-mode", "Dark Mode"),
    ("gradient-header", "Gradient Header"),
    ("tech-terminal", "Tech Terminal"),
    ("warm-paper", "Warm Paper"),
]


def data_uri(path):
    b = base64.b64encode(open(path, "rb").read()).decode()
    return f"data:image/png;base64,{b}"


def main():
    from playwright.sync_api import sync_playwright

    cards = []
    for name, label in TEMPLATES:
        uri = data_uri(os.path.join(IMG_DIR, f"preview_{name}.png"))
        # 每个手机框只露出顶部一屏，避免过高；圆角+阴影=精致
        cards.append(f"""
        <div class="card">
          <div class="phone">
            <div class="screen"><img src="{uri}"/></div>
          </div>
          <div class="label">{label}</div>
        </div>""")

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      body {{ background:linear-gradient(135deg,#f5f7fa 0%,#e8edf3 100%);
             font-family:-apple-system,'PingFang SC','Helvetica Neue',Arial,sans-serif;
             padding:48px 40px; }}
      .row {{ display:flex; gap:28px; justify-content:center; align-items:flex-start; }}
      .card {{ display:flex; flex-direction:column; align-items:center; }}
      .phone {{ width:220px; height:430px; background:#111; border-radius:30px;
               padding:10px; box-shadow:0 18px 50px rgba(0,0,0,0.22); }}
      .screen {{ width:100%; height:100%; border-radius:22px; overflow:hidden; background:#fff; }}
      .screen img {{ width:100%; display:block; object-fit:cover; object-position:top; }}
      .label {{ margin-top:18px; font-size:15px; font-weight:600; color:#1d1d1f;
               letter-spacing:0.3px; }}
    </style></head><body>
      <div class="row">{''.join(cards)}</div>
    </body></html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1640, "height": 600}, device_scale_factor=2)
        page.set_content(html, wait_until="networkidle")
        time.sleep(0.6)
        out = os.path.join(IMG_DIR, "hero_templates.png")
        # 截内容区，紧贴卡片
        el = page.query_selector(".row")
        (el or page).screenshot(path=out)
        browser.close()
    print(f"✅ hero -> {out}")


if __name__ == "__main__":
    main()
