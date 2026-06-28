"""tech-terminal composer — WeChat OA article template.

Renders an article as a dark "terminal" aesthetic: GitHub-dark background,
monospace font, green prompts, and per-section dark cards. WeChat-safe inline
CSS only (no flex/grid/position; only <section> and <p> tags).
"""

import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared import colorUpDown, parse_item

BG = "#0D1117"; CARD_BG = "#161B22"; CARD_BORDER = "#30363D"
GREEN = "#00FF41"; BORDER_GREEN = "#1a3a1a"; BODY = "#C9D1D9"; LABEL = "#8B949E"


def compose_html(article_data, image_urls):
    """Returns HTML string for WeChat article body.

    items format: 'Title<br/>Body text（6月27日）'. The cover image is set via
    thumb_media_id and is NOT rendered in the body. No footer.
    """
    today = time.strftime("%Y年%m月%d日")
    title = article_data.get("title", "")
    vol = article_data.get("vol", "")
    digest = article_data.get("digest", "")
    sections = article_data.get("sections", []) or []
    trends = article_data.get("trends", []) or []
    out = []

    # Root terminal window
    out.append(
        f'<section style="background-color:{BG};padding:16px 14px;border-radius:8px;'
        f'border:1px solid {CARD_BORDER};font-family:\'Courier New\',monospace;'
        f'color:{BODY};font-size:15px;line-height:1.7;letter-spacing:0.3px;word-break:break-all;">'
    )

    # Title bar (window chrome dots + vol)
    out.append(
        f'<section style="background-color:{CARD_BG};border-radius:6px 6px 0 0;padding:8px 12px;'
        f'border:1px solid {CARD_BORDER};border-bottom:none;">'
        f'<span style="color:#FF5F56;">●</span>&nbsp;'
        f'<span style="color:#FFBD2E;">●</span>&nbsp;'
        f'<span style="color:#27C93F;">●</span>&nbsp;&nbsp;'
        f'<span style="color:{LABEL};font-size:13px;">~/ai-frontline/vol_{vol}</span></section>'
    )

    # Header block (title + digest + date)
    out.append(
        f'<section style="background-color:{CARD_BG};border:1px solid {CARD_BORDER};border-top:none;'
        f'border-radius:0 0 6px 6px;padding:16px 14px;margin-bottom:14px;">'
        f'<p style="margin:0 0 6px 0;font-size:13px;color:{LABEL};">'
        f'<span style="color:{GREEN};font-weight:bold;">$</span> cat headline.md</p>'
        f'<p style="margin:0 0 8px 0;font-size:20px;font-weight:bold;color:{GREEN};line-height:1.4;">{title}</p>'
    )
    if digest:
        out.append(
            f'<p style="margin:0;font-size:13px;color:{LABEL};line-height:1.6;">'
            f'<span style="color:{LABEL};">#</span> {digest}</p>'
        )
    out.append(f'<p style="margin:6px 0 0 0;font-size:12px;color:{LABEL};">{today}</p></section>')

    # Sections
    for sec in sections:
        heading = sec.get("heading", "")
        items = sec.get("items", []) or []
        images = sec.get("images", []) or []
        out.append(
            f'<section style="background-color:{CARD_BG};border:1px solid {CARD_BORDER};'
            f'border-radius:6px;padding:14px;margin-bottom:14px;">'
            f'<p style="margin:0 0 12px 0;font-size:16px;font-weight:bold;color:{GREEN};'
            f'border-bottom:1px solid {BORDER_GREEN};padding-bottom:8px;">'
            f'<span style="color:{GREEN};">$</span>&nbsp;{heading}</p>'
        )
        for idx, raw in enumerate(items, 1):
            head, body, date_str = parse_item(raw)
            date_html = f' <span style="color:{LABEL};font-size:12px;">{date_str}</span>' if date_str else ""
            out.append(
                f'<p style="margin:0 0 2px 0;font-size:12px;color:{LABEL};">[{idx:02d}] '
                f'<span style="color:{GREEN};font-weight:bold;">{head}</span>{date_html}</p>'
            )
            if body:
                out.append(
                    f'<p style="margin:0 0 12px 0;padding-left:28px;font-size:14px;color:{BODY};'
                    f'line-height:1.7;">{body}</p>'
                )
        for img in images:
            src = img if isinstance(img, str) else img.get("url", "")
            if src:
                out.append(
                    f'<p style="margin:8px 0 0 0;text-align:center;">'
                    f'<img src="{src}" style="max-width:100%;border-radius:4px;'
                    f'border:1px solid {BORDER_GREEN};display:block;margin:0 auto;" /></p>'
                )
        out.append('</section>')

    # Trends
    if trends:
        out.append(
            f'<section style="background-color:{CARD_BG};border:1px solid {CARD_BORDER};'
            f'border-radius:6px;padding:14px;margin-bottom:14px;">'
            f'<p style="margin:0 0 12px 0;font-size:16px;font-weight:bold;color:{GREEN};'
            f'border-bottom:1px solid {BORDER_GREEN};padding-bottom:8px;">'
            f'<span style="color:{GREEN};">$</span>&nbsp;TRENDS</p>'
        )
        for t in trends:
            t = colorUpDown(t)
            out.append(
                f'<p style="margin:0 0 8px 0;padding-left:8px;font-size:14px;color:{BODY};'
                f'line-height:1.7;"><span style="color:{GREEN};">→</span>&nbsp;{t}</p>'
            )
        out.append('</section>')

        # Interaction question
        interaction = article_data.get("interaction", "")
        if interaction:
            out.append(
                f'<p style="margin:28px 0 0;padding-top:16px;border-top:1px solid #333333;'
                f'font-size:16px;color:#00FF41;line-height:1.8;font-weight:600;">{interaction}</p>'
            )

    out.append('</section>')

    return "".join(out)
