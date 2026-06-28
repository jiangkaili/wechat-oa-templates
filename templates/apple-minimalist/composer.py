"""Apple Minimalist — pure white, black/gray, Apple Newsroom style."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared import colorUpDown, parse_item


def compose_html(article_data, image_urls):
    today = time.strftime("%Y年%m月%d日")
    vol = article_data.get("vol", "")
    sections = article_data.get("sections", [])
    trends = article_data.get("trends", [])
    PAD = "30px"

    parts = []

    # Header: date + vol, small gray
    vol_part = f' &nbsp; {vol}' if vol else ''
    parts.append(
        f'<section style="background:#FFFFFF;padding:60px {PAD} 0;">'
        f'<p style="font-size:13px;color:#86868B;margin:0 0 40px;">{today}{vol_part}</p>'
        f'</section>'
    )

    # Content
    parts.append(f'<section style="background:#FFFFFF;padding:0 {PAD};">')

    for section in sections:
        heading = section["heading"]
        items = section.get("items", [])
        section_images = section.get("images", [])

        parts.append(
            f'<p style="font-size:18px;font-weight:600;color:#1D1D1F;margin:0 0 30px;padding-bottom:12px;border-bottom:1px solid #E5E5E5;">{heading}</p>'
        )

        for idx, item in enumerate(items, 1):
            head_text, tail, date_str = parse_item(item)
            date_html = '<span style="color:#86868B;font-weight:400;font-size:12px;margin-left:8px;">' + date_str + '</span>' if date_str else ''
            parts.append(
                f'<p style="font-size:16px;color:#1D1D1F;line-height:1.8;margin:0 0 8px;font-weight:600;">'
                f'{head_text}{date_html}</p>'
            )
            if tail:
                parts.append(f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 12px;">{tail}</p>')
            else:
                parts.append('<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 12px;">&nbsp;</p>')
            img_url = section_images[idx - 1] if section_images and idx - 1 < len(section_images) else None
            if img_url:
                parts.append(f'<p style="margin:0 0 32px;text-align:center;"><img src="{img_url}" style="max-width:100%;border-radius:8px;" /></p>')
            else:
                parts.append('<p style="margin:0 0 20px;">&nbsp;</p>')

    parts.append('</section>')

    # Trends
    if trends:
        parts.append(f'<section style="background:#FFFFFF;padding:8px {PAD} 0;">')
        parts.append(
            '<p style="font-size:18px;font-weight:600;color:#1D1D1F;margin:0 0 20px;padding-bottom:10px;border-bottom:1px solid #E5E5E5;">趋势观察</p>'
        )
        for trend in trends:
            trend = colorUpDown(trend)
            parts.append(f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 16px;">{trend}</p>')
        parts.append('</section>')

    return "\n".join(parts)
