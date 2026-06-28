"""Apple Minimalist — pure white, black/gray, Apple Newsroom style."""


def compose_html(article_data, image_urls):
    import time, re

    today = time.strftime("%Y年%m月%d日")
    sections = article_data.get("sections", [])
    trends = article_data.get("trends", [])
    PAD = "30px"

    def colorUpDown(text):
        text = re.sub(r'(\+[0-9.]+%)', r'<span style="color:#22C55E;font-weight:bold;">\1</span>', text)
        text = re.sub(r'(-[0-9.]+%)', r'<span style="color:#EF4444;font-weight:bold;">\1</span>', text)
        return text

    parts = []

    # Header: date only, small gray
    parts.append(
        f'<section style="background:#FFFFFF;padding:60px {PAD} 0;">'
        f'<p style="font-size:13px;color:#86868B;margin:0 0 40px;">{today}</p>'
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
            if "<br/>" in item:
                head_text, tail = item.split("<br/>", 1)
            else:
                head_text, tail = item, ""
            head_text = colorUpDown(head_text)
            if tail:
                tail = colorUpDown(tail)
            date_html = ""
            if tail:
                date_match = re.search(r'（\d+月\d+日）$', tail)
                if date_match:
                    date_label = date_match.group()
                    tail = tail[:date_match.start()].rstrip()
                    date_html = '<span style="color:#86868B;font-weight:400;font-size:12px;margin-left:8px;">' + date_label + '</span>'
            parts.append(
                f'<p style="font-size:16px;color:#1D1D1F;line-height:1.8;margin:0 0 8px;font-weight:600;">'
                f'{head_text}{date_html}</p>'
            )
            if tail:
                parts.append(f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 12px;">{tail}</p>')
            else:
                parts.append(f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 12px;">&nbsp;</p>')
            img_url = section_images[idx - 1] if section_images and idx - 1 < len(section_images) else None
            if img_url:
                parts.append(f'<p style="margin:0 0 32px;text-align:center;"><img src="{img_url}" style="max-width:100%;border-radius:8px;" /></p>')
            else:
                parts.append(f'<p style="margin:0 0 20px;">&nbsp;</p>')

    parts.append('</section>')

    # Trends
    if trends:
        parts.append(f'<section style="background:#FFFFFF;padding:8px {PAD} 0;">')
        parts.append(
            f'<p style="font-size:18px;font-weight:600;color:#1D1D1F;margin:0 0 20px;padding-bottom:10px;border-bottom:1px solid #E5E5E5;">趋势观察</p>'
        )
        for trend in trends:
            trend = colorUpDown(trend)
            parts.append(f'<p style="font-size:15px;color:#555555;line-height:1.8;margin:0 0 16px;">{trend}</p>')
        parts.append('</section>')

    return "\n".join(parts)
