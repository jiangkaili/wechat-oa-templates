# gradient-header

A vibrant, modern WeChat OA article template with a colorful gradient hero and
accent-bordered content items — eye-catching and energetic.

## Description

`gradient-header` opens with a full-width indigo-to-purple gradient hero showing
the volume, title, date and subtitle in white. Below, each section uses an
accent-colored header with an underline, and every item is marked by a thin
accent left-border. The vivid header plus restrained body keeps the layout
striking yet readable.

## Key design features

- White body canvas `#FFFFFF`
- Gradient hero: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`, white text
- Hero title: white bold `20px`; date / vol / subtitle in muted white
- Section headers: `18px` bold `#667eea` with accent underline
- Each item: `border-left: 3px solid #667eea`, `padding-left: 16px`
- Item title: `16px` bold `#1D1D1F` · body: `15px` `#555555` · `line-height: 1.8`
- Inline images: `border-radius: 8px`
- Trends: accent-color heading, plain-text body
- Finance-aware: `+x%` green / `-x%` red via `colorUpDown`
- Date auto-extracted from end of body (`（6月27日）`) and shown as a muted tag
- Self-contained: only Python stdlib used inside `compose_html`

## Color palette

| Token           | Hex       | Usage                          |
| --------------- | --------- | ------------------------------ |
| White           | `#FFFFFF` | Page background                |
| Accent          | `#667eea` | Section headers, item borders  |
| Gradient start  | `#667eea` | Hero gradient (indigo)         |
| Gradient end    | `#764ba2` | Hero gradient (purple)         |
| Primary text    | `#1D1D1F` | Item titles                    |
| Body text       | `#555555` | Body copy & trends             |
| Secondary text  | `#999999` | Date tags                      |
| Up (positive)   | `#22C55E` | `+x%` finance figures          |
| Down (negative) | `#EF4444` | `-x%` finance figures          |

## Files

- `composer.py` — `compose_html(article_data, image_urls)` renderer
- `example.json` — sample article (set `"style": "gradient-header"`)
- `README.md` — this file
