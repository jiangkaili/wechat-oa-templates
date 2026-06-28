"""Shared utilities for all template composers.

Imported by each templates/<style>/composer.py via a sys.path insert.
Provides colorUpDown (finance % coloring) and parse_item (split title/body/date).
"""

import re


UP = "#22C55E"   # green for positive %
DOWN = "#EF4444"  # red for negative %


def colorUpDown(text):
    """Wrap +X.XX% in green and -X.XX% in red bold spans."""
    text = re.sub(r'(\+[0-9.]+%)', r'<span style="color:%s;font-weight:bold;">\1</span>' % UP, text)
    text = re.sub(r'(-[0-9.]+%)', r'<span style="color:%s;font-weight:bold;">\1</span>' % DOWN, text)
    return text


def parse_item(raw):
    """Split an item string into (head, body, date_str).

    Item format: 'Title<br/>Body text（6月27日）'
    Returns:
        head:    title text, colorUpDown applied
        body:    body text without trailing date, colorUpDown applied (or '')
        date_str: raw date like '（6月27日）' or '' if none found
    """
    if "<br/>" in raw:
        head, tail = raw.split("<br/>", 1)
    else:
        head, tail = raw, ""

    head = colorUpDown(head)
    date_str = ""

    if tail:
        tail = colorUpDown(tail)
        m = re.search(r'（\d+月\d+日）$', tail)
        if m:
            date_str = m.group()
            tail = tail[:m.start()].rstrip()

    return head, tail, date_str
