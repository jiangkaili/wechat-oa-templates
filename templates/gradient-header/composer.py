"""Gradient Header — vibrant gradient hero with accent-bordered items.

Opens with a full-width purple-to-indigo gradient hero (white text), then uses
an accent-colored section header with underline and a thin accent left-border on
every item. Eye-catching yet readable. Designed for the wechat_publisher gallery.
"""

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared import colorUpDown, parse_item


def compose_html(article_data, image_urls):
    """Returns HTML string for WeChat article body."""
    today = time.strftime("%Y年%m月%d日")
    title = article_data.get("title", "")
    vol = article_data.get("vol", "")
    subtitle = article_data.get("subtitle", "")
    sections = article_data.get("sections", [])
    trends = article_data.get("trends", [])
    ACCENT = "#667eea"
    PAD = "28px"

    parts = []

    # Hero: gradient background, white text
    hero = (
        f'<section style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);padding:60px {PAD} 50px;">'
        f'<p style="font-size:12px;color:#FFFFFF;margin:0 0 10px;letter-spacing:2px;opacity:0.85;">{vol}</p>'
        f'<p style="font-size:20px;font-weight:bold;color:#FFFFFF;line-height:1.5;margin:0 0 12px;">{title}</p>'
        f'<p style="font-size:13px;color:#FFFFFF;margin:0 0 6px;opacity:0.85;">{today}</p>'
    )
    if subtitle:
        hero += f'<p style="font-size:13px;color:#FFFFFF;margin:0;opacity:0.85;">{subtitle}</p>'
    hero += '</section>'
    parts.append(hero)

    # Body sections
    parts.append(f'<section style="background:#FFFFFF;padding:36px {PAD} 10px;">')

    for section in sections:
        heading = section["heading"]
        items = section.get("items", [])
        section_images = section.get("images", [])

        parts.append(
            f'<p style="font-size:18px;font-weight:bold;color:{ACCENT};margin:0 0 22px;padding-bottom:8px;border-bottom:2px solid {ACCENT};">{heading}</p>'
        )

        for idx, item in enumerate(items, 1):
            head_text, tail, date_str = parse_item(item)
            date_html = ('<span style="color:#999999;font-weight:400;font-size:12px;margin-left:8px;">' + date_str + '</span>') if date_str else ""

            parts.append(
                f'<section style="border-left:3px solid {ACCENT};padding-left:16px;margin:0 0 22px;">'
            )
            parts.append(
                f'<p style="font-size:16px;font-weight:bold;color:#1D1D1F;line-height:1.6;margin:0 0 8px;">{head_text}{date_html}</p>'
            )
            if tail:
                parts.append(f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 12px;">{tail}</p>')
            img_url = section_images[idx - 1] if section_images and idx - 1 < len(section_images) else None
            if img_url:
                parts.append(f'<p style="margin:0;text-align:center;"><img src="{img_url}" style="max-width:100%;border-radius:8px;" /></p>')
            parts.append('</section>')

    parts.append('</section>')

    # Trends — accent heading, plain text body
    if trends:
        parts.append(f'<section style="background:#FFFFFF;padding:20px {PAD} 40px;">')
        parts.append(
            f'<p style="font-size:18px;font-weight:bold;color:{ACCENT};margin:0 0 20px;padding-bottom:8px;border-bottom:2px solid {ACCENT};">趋势观察</p>'
        )
        for trend in trends:
            trend = colorUpDown(trend)
            parts.append(f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 16px;">{trend}</p>')
        parts.append('</section>')

    return "\n".join(parts)
