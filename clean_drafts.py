#!/usr/bin/env python3
"""Batch delete all drafts from WeChat Official Account.

Usage: python3 clean_drafts.py
"""
import json, sys
import publish_generic as p


def main():
    token = p.get_token()
    print("=== 批量清理草稿 ===", file=sys.stderr)

    # List all drafts
    offset = 0
    deleted = 0
    while True:
        import urllib.request
        url = f"{p.BASE}/draft/batchget?access_token={token}"
        req = urllib.request.Request(url,
            data=json.dumps({"offset": offset, "count": 20, "no_content": 1}).encode(),
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())

        items = data.get("item", [])
        if not items:
            break

        for item in items:
            media_id = item["media_id"]
            title = item.get("content", {}).get("news_item", [{}])[0].get("title", "?")
            # Delete
            del_url = f"{p.BASE}/draft/delete?access_token={token}"
            del_req = urllib.request.Request(del_url,
                data=json.dumps({"media_id": media_id}).encode(),
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(del_req, timeout=10)
            print(f"  删除: {title}", file=sys.stderr)
            deleted += 1

        offset += data.get("article_count", 0)
        if offset >= data.get("total_count", 0):
            break

    print(json.dumps({"success": True, "deleted": deleted}, ensure_ascii=False))


if __name__ == "__main__":
    main()
