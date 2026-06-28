## Description

What does this PR add/change? (简要描述)

## Type

- [ ] New template
- [ ] Bug fix
- [ ] Documentation
- [ ] Other

## Checklist

- [ ] `composer.py` defines `compose_html(article_data, image_urls) -> str`
- [ ] Imports `colorUpDown` / `parse_item` from `_shared` (no duplication)
- [ ] `example.json` uses the unified format (style, title, sections, trends, vol)
- [ ] No footer / no hardcoded author name
- [ ] `python3 -m pyflakes templates/<your-style>/composer.py` passes with 0 warnings
- [ ] Tested with `python3 publish_generic.py templates/<your-style>/example.json` (dry run OK)
