# card-layout

A clean, modular WeChat OA article template. Every news item sits inside its own
rounded card with a soft shadow on a pure white canvas — Apple Newsroom–inspired,
modern and easy to scan.

## Description

`card-layout` wraps each item in a self-contained rounded card so readers can
treat every snippet as an independent unit. Section headers are centered, cards
carry a subtle drop shadow, and inline images get rounded corners inside the
card. The result is a structured, "card grid" feel without using flex/grid
(which WeChat strips out).

## Key design features

- Pure white canvas `#FFFFFF`
- Rounded item cards: `#F5F5F7`, `border-radius: 12px`, `padding: 20px`, `margin-bottom: 20px`
- Soft drop shadow `box-shadow: 0 2px 8px rgba(0,0,0,0.06)`
- Section headers: `18px` bold `#1D1D1F`, centered
- Card title: `16px` bold `#1D1D1F` · body: `15px` `#555555` · `line-height: 1.8`
- Inline images: `border-radius: 8px`
- Each trend rendered in its own small card
- Finance-aware: `+x%` green / `-x%` red via `colorUpDown`
- Date auto-extracted from end of body (`（6月27日）`) and shown as a muted tag
- Self-contained: only Python stdlib used inside `compose_html`

## Color palette

| Token           | Hex                  | Usage                          |
| --------------- | -------------------- | ------------------------------ |
| White           | `#FFFFFF`            | Page background                |
| Card gray       | `#F5F5F7`            | Card background                |
| Primary text    | `#1D1D1F`            | Headings & card titles         |
| Body text       | `#555555`            | Body copy                      |
| Secondary text  | `#86868B`            | Date tags, vol, meta           |
| Up (positive)   | `#22C55E`            | `+x%` finance figures          |
| Down (negative) | `#EF4444`            | `-x%` finance figures          |
| Shadow          | `rgba(0,0,0,0.06)`   | Card drop shadow               |

## Files

- `composer.py` — `compose_html(article_data, image_urls)` renderer
- `example.json` — sample article (set `"style": "card-layout"`)
- `README.md` — this file
