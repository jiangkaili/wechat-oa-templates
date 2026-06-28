"""Warm Paper — warm cream background, serif fonts, book/journal aesthetic."""


def compose_html(article_data, image_urls):
    """Returns HTML string for WeChat article body."""
    import time, re

    today = time.strftime("%Y年%m月%d日")
    vol = article_data.get("vol", "")
    sections = article_data.get("sections", [])
    trends = article_data.get("trends", [])
    PAD = "30px"
    BG = "#FAF9F5"        # warm cream background
    TEXT = "#3D3530"       # dark brown text
    BODY = "#5C5048"       # warm body text
    LABEL = "#8B7E6E"      # warm gray labels
    BORDER = "#D4C9B8"     # warm gray underline/border
    FONT = "font-family:Georgia,'Times New Roman',serif;"

    def colorUpDown(text):
        text = re.sub(r'(\+[0-9.]+%)', r'<span style="color:#22C55E;font-weight:bold;">\1</span>', text)
        text = re.sub(r'(-[0-9.]+%)', r'<span style="color:#EF4444;font-weight:bold;">\1</span>', text)
        return text

    parts = []
    vol_part = f' &nbsp; {vol}' if vol else ''

    # Header: date + vol, small warm gray
    parts.append(
        f'<section style="background:{BG};padding:60px {PAD} 0;">'
        f'<p style="{FONT}font-size:12px;color:{LABEL};margin:0 0 40px;letter-spacing:1px;">{today}{vol_part}</p>'
        f'</section>'
    )

    # Content
    parts.append(f'<section style="background:{BG};padding:0 {PAD};">')

    for section in sections:
        heading = section["heading"]
        items = section.get("items", [])
        section_images = section.get("images", [])

        parts.append(
            f'<p style="{FONT}font-size:18px;font-weight:bold;color:{TEXT};margin:0 0 30px;'
            f'padding-bottom:12px;border-bottom:1px solid {BORDER};">{heading}</p>'
        )

        for idx, item in enumerate(items, 1):
            if "<br/>" in item:
                head_text, tail = item.split("<br/>", 1)
            else:
                head_text, tail = item, ""
            head_text = colorUpDown(head_text)
            date_html = ""
            if tail:
                tail = colorUpDown(tail)
                date_match = re.search(r'（\d+月\d+日）$', tail)
                if date_match:
                    date_label = date_match.group()
                    tail = tail[:date_match.start()].rstrip()
                    date_html = (
                        f'<span style="{FONT}color:{LABEL};font-weight:400;font-size:12px;'
                        f'margin-left:8px;">{date_label}</span>'
                    )
            parts.append(
                f'<p style="{FONT}font-size:16px;color:{TEXT};line-height:1.9;margin:0 0 8px;font-weight:bold;">'
                f'{head_text}{date_html}</p>'
            )
            if tail:
                parts.append(f'<p style="{FONT}font-size:15px;color:{BODY};line-height:1.9;margin:0 0 12px;">{tail}</p>')
            else:
                parts.append(f'<p style="{FONT}font-size:15px;color:{BODY};line-height:1.9;margin:0 0 12px;">&nbsp;</p>')
            img_url = section_images[idx - 1] if section_images and idx - 1 < len(section_images) else None
            if img_url:
                parts.append(
                    f'<p style="margin:0 0 32px;text-align:center;">'
                    f'<img src="{img_url}" style="max-width:100%;border-radius:4px;border:1px solid {BORDER};" /></p>'
                )
            else:
                parts.append(f'<p style="margin:0 0 20px;">&nbsp;</p>')

    parts.append('</section>')

    # Trends
    if trends:
        parts.append(f'<section style="background:{BG};padding:8px {PAD} 0;">')
        parts.append(
            f'<p style="{FONT}font-size:18px;font-weight:bold;color:{TEXT};margin:0 0 20px;'
            f'padding-bottom:10px;border-bottom:1px solid {BORDER};">趋势观察</p>'
        )
        for trend in trends:
            trend = colorUpDown(trend)
            parts.append(f'<p style="{FONT}font-size:15px;color:{BODY};line-height:1.9;margin:0 0 16px;">{trend}</p>')
        parts.append('</section>')

    return "\n".join(parts)
