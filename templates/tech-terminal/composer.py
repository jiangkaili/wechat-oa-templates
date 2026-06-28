"""tech-terminal composer — WeChat OA article template.

Renders an article as a dark "terminal" aesthetic: GitHub-dark background,
monospace font, green prompts, and per-section dark cards.

Only the Python standard library is required. All WeChat-safe CSS is inline
(no flex / grid / position, only <section> and <p> tags).
"""

# Palette -----------------------------------------------------------------
BG = "#0D1117"          # page background (GitHub dark)
CARD_BG = "#161B22"     # per-section card background
CARD_BORDER = "#30363D" # card border
GREEN = "#00FF41"       # terminal green (headers / prompts)
BORDER_GREEN = "#1a3a1a"  # subtle green tint for image borders
BODY = "#C9D1D9"        # body text
LABEL = "#8B949E"       # secondary / labels
UP = "#22C55E"          # positive %
DOWN = "#EF4444"        # negative %


def colorUpDown(text):
    """Color percentage changes green (up) or red (down)."""
    import re
    text = re.sub(r'(\+[0-9.]+%)', r'<span style="color:#22C55E;font-weight:bold;">\1</span>', text)
    text = re.sub(r'(-[0-9.]+%)', r'<span style="color:#EF4444;font-weight:bold;">\1</span>', text)
    return text


def compose_html(article_data, image_urls):
    """Returns HTML string for WeChat article body.

    article_data keys:
        title, digest, vol, sections (list of {heading, items, images}), trends
    image_urls:
        dict with 'cover' key (and any per-section image URLs already uploaded)
    items format: 'Title<br/>Body text（6月27日）'
    """
    import html as _html

    title = article_data.get("title", "")
    vol = article_data.get("vol", "")
    digest = article_data.get("digest", "")
    sections = article_data.get("sections", []) or []
    trends = article_data.get("trends", []) or []
    cover = (image_urls or {}).get("cover", "")

    out = []

    # --- Root wrapper (terminal window) ---------------------------------
    out.append(
        '<section style="background-color:%s;padding:16px 14px;'
        'border-radius:8px;border:1px solid %s;'
        'font-family:\'Courier New\',monospace;color:%s;'
        'font-size:15px;line-height:1.7;letter-spacing:0.3px;word-break:break-all;">'
        % (BG, CARD_BORDER, BODY)
    )

    # --- Title bar (window chrome dots + vol) ---------------------------
    out.append(
        '<section style="background-color:%s;border-radius:6px 6px 0 0;'
        'padding:8px 12px;border:1px solid %s;border-bottom:none;">'
        '<span style="color:#FF5F56;">●</span>&nbsp;'
        '<span style="color:#FFBD2E;">●</span>&nbsp;'
        '<span style="color:#27C93F;">●</span>&nbsp;&nbsp;'
        '<span style="color:%s;font-size:13px;">~/ai-frontline/vol_%s</span>'
        '</section>' % (CARD_BG, CARD_BORDER, LABEL, _html.escape(str(vol)))
    )

    # --- Header block (title + digest) ----------------------------------
    out.append(
        '<section style="background-color:%s;border:1px solid %s;border-top:none;'
        'border-radius:0 0 6px 6px;padding:16px 14px;margin-bottom:14px;">'
        % (CARD_BG, CARD_BORDER)
    )
    out.append(
        '<p style="margin:0 0 6px 0;font-size:13px;color:%s;">'
        '<span style="color:%s;font-weight:bold;">$</span> cat headline.md'
        '</p>' % (LABEL, GREEN)
    )
    out.append(
        '<p style="margin:0 0 8px 0;font-size:20px;font-weight:bold;color:%s;'
        'line-height:1.4;">%s</p>' % (GREEN, _html.escape(str(title)))
    )
    if digest:
        out.append(
            '<p style="margin:0;font-size:13px;color:%s;line-height:1.6;">'
            '<span style="color:%s;">#</span> %s'
            '</p>' % (LABEL, LABEL, _html.escape(str(digest)))
        )
    out.append('</section>')

    # --- Sections --------------------------------------------------------
    for sec in sections:
        heading = sec.get("heading", "")
        items = sec.get("items", []) or []
        images = sec.get("images", []) or []

        # Section card open
        out.append(
            '<section style="background-color:%s;border:1px solid %s;'
            'border-radius:6px;padding:14px;margin-bottom:14px;">'
            % (CARD_BG, CARD_BORDER)
        )

        # Section header (prompt style: $ heading)
        out.append(
            '<p style="margin:0 0 12px 0;font-size:16px;font-weight:bold;color:%s;'
            'border-bottom:1px solid %s;padding-bottom:8px;">'
            '<span style="color:%s;">$</span>&nbsp;%s'
            '</p>' % (GREEN, BORDER_GREEN, GREEN, _html.escape(str(heading)))
        )

        # Items
        for idx, raw in enumerate(items, 1):
            raw = str(raw)
            # Split "Title<br/>Body"
            if "<br/>" in raw or "<br>" in raw:
                sep = "<br/>" if "<br/>" in raw else "<br>"
                parts = raw.split(sep, 1)
                item_title = parts[0].strip()
                item_body = parts[1].strip() if len(parts) > 1 else ""
            else:
                item_title = raw.strip()
                item_body = ""

            # Item index label
            out.append(
                '<p style="margin:0 0 2px 0;font-size:12px;color:%s;">'
                '[%02d]' % (LABEL, idx)
            )
            # Item title (green bold)
            out.append(
                ' <span style="color:%s;font-weight:bold;">%s</span>'
                '</p>' % (GREEN, _html.escape(item_title))
            )
            # Item body (light gray, monospace) with up/down coloring
            if item_body:
                body_html = colorUpDown(_html.escape(item_body))
                # Re-allow the <br/> we escaped; items use literal <br/> as separator
                body_html = body_html.replace("&lt;br/&gt;", "<br/>").replace("&lt;br&gt;", "<br/>")
                out.append(
                    '<p style="margin:0 0 12px 0;padding-left:28px;font-size:14px;'
                    'color:%s;line-height:1.7;">%s</p>' % (BODY, body_html)
                )

        # Section images
        for img in images:
            src = img if isinstance(img, str) else img.get("url", "")
            if not src:
                continue
            out.append(
                '<p style="margin:8px 0 0 0;text-align:center;">'
                '<img src="%s" style="max-width:100%%;border-radius:4px;'
                'border:1px solid %s;display:block;margin:0 auto;" />'
                '</p>' % (_html.escape(src), BORDER_GREEN)
            )

        out.append('</section>')  # section card close

    # --- Trends ----------------------------------------------------------
    if trends:
        out.append(
            '<section style="background-color:%s;border:1px solid %s;'
            'border-radius:6px;padding:14px;margin-bottom:14px;">'
            % (CARD_BG, CARD_BORDER)
        )
        out.append(
            '<p style="margin:0 0 12px 0;font-size:16px;font-weight:bold;color:%s;'
            'border-bottom:1px solid %s;padding-bottom:8px;">'
            '<span style="color:%s;">$</span>&nbsp;TRENDS'
            '</p>' % (GREEN, BORDER_GREEN, GREEN)
        )
        for idx, t in enumerate(trends, 1):
            t = str(t)
            t_html = colorUpDown(_html.escape(t))
            t_html = t_html.replace("&lt;br/&gt;", "<br/>").replace("&lt;br&gt;", "<br/>")
            out.append(
                '<p style="margin:0 0 8px 0;padding-left:8px;font-size:14px;color:%s;'
                'line-height:1.7;"><span style="color:%s;">→</span>&nbsp;%s</p>'
                % (BODY, GREEN, t_html)
            )
        out.append('</section>')

    # --- Footer (prompt cursor) -----------------------------------------
    out.append(
        '<section style="background-color:%s;border:1px solid %s;border-radius:6px;'
        'padding:12px 14px;">'
        '<p style="margin:0;font-size:13px;color:%s;">'
        '<span style="color:%s;font-weight:bold;">$</span>&nbsp;_<span style="display:inline-block;'
        'width:8px;height:14px;background-color:%s;margin-left:2px;vertical-align:middle;"></span>'
        '</p>'
        '<p style="margin:6px 0 0 0;font-size:11px;color:%s;text-align:right;">'
        'AI前哨 · Vol.%s'
        '</p>'
        '</section>' % (CARD_BG, CARD_BORDER, BODY, GREEN, GREEN, LABEL, _html.escape(str(vol)))
    )

    # --- Cover image (optional, top-of-article banner) ------------------
    if cover:
        out.append(
            '<p style="margin:0 0 14px 0;text-align:center;">'
            '<img src="%s" style="max-width:100%%;border-radius:6px;'
            'border:1px solid %s;display:block;margin:0 auto;" />'
            '</p>' % (_html.escape(cover), BORDER_GREEN)
        )

    out.append('</section>')  # root close
    return "".join(out)
