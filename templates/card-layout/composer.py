"""Card Layout — modular rounded cards on pure white, modern and clean.

Each news item is wrapped in its own rounded card (#F5F5F7) with a soft shadow,
giving the article a structured, scannable "card grid" feel without using
flex/grid (which WeChat strips out). Designed for the wechat_publisher gallery.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared import colorUpDown, parse_item


def compose_html(article_data, image_urls):
    """Returns HTML string for WeChat article body."""
    today = time.strftime("%Y年%m月%d日")
    sections = article_data.get("sections", [])
    trends = article_data.get("trends", [])
    vol = article_data.get("vol", "")
    PAD = "28px"

    parts = []

    # Top: vol + date on white
    parts.append(
        f'<section style="background:#FFFFFF;padding:50px {PAD} 0;">'
        f'<p style="font-size:12px;color:#86868B;margin:0 0 8px;letter-spacing:2px;">{vol}</p>'
        f'<p style="font-size:13px;color:#86868B;margin:0 0 36px;">{today}</p>'
        f'</section>'
    )

    # Content
    parts.append(f'<section style="background:#FFFFFF;padding:0 {PAD} 10px;">')

    for section in sections:
        heading = section["heading"]
        items = section.get("items", [])
        section_images = section.get("images", [])

        parts.append(
            f'<p style="font-size:18px;font-weight:bold;color:#1D1D1F;text-align:center;margin:0 0 24px;">{heading}</p>'
        )

        for idx, item in enumerate(items, 1):
            head_text, tail, date_str = parse_item(item)
            date_html = '<span style="color:#86868B;font-weight:400;font-size:12px;margin-left:8px;">' + date_str + '</span>' if date_str else ''

            parts.append(
                '<section style="background:#F5F5F7;border-radius:12px;padding:20px;margin:0 0 20px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
            )
            parts.append(
                f'<p style="font-size:16px;font-weight:bold;color:#1D1D1F;line-height:1.6;margin:0 0 10px;">{head_text}{date_html}</p>'
            )
            if tail:
                parts.append(f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 12px;">{tail}</p>')
            img_url = section_images[idx - 1] if section_images and idx - 1 < len(section_images) else None
            if img_url:
                parts.append(f'<p style="margin:0;text-align:center;"><img src="{img_url}" style="max-width:100%;border-radius:8px;" /></p>')
            parts.append('</section>')

    parts.append('</section>')

    # Trends — each in its own small card
    if trends:
        parts.append(f'<section style="background:#FFFFFF;padding:16px {PAD} 40px;">')
        parts.append(
            '<p style="font-size:18px;font-weight:bold;color:#1D1D1F;text-align:center;margin:0 0 24px;">深度解码</p>'
        )
        for trend in trends:
            trend = colorUpDown(trend)
            parts.append(
                f'<section style="background:#F5F5F7;border-radius:10px;padding:16px 20px;margin:0 0 14px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">'
                f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0;">{trend}</p>'
                f'</section>'
            )
        # Interaction question
        interaction = article_data.get("interaction", "")
        if interaction:
            parts.append(
                f'<p style="margin:28px 0 0;padding-top:16px;border-top:1px solid #E5E5E5;'
                f'font-size:16px;color:#1D1D1F;line-height:1.8;font-weight:600;">{interaction}</p>'
            )

        parts.append('</section>')

    return "\n".join(parts)
