#!/usr/bin/env python3
"""Встраивает data.json в dashboard.html и собирает docs/index.html для GitHub Pages."""
import json, re, pathlib
d = pathlib.Path(__file__).parent
data = json.dumps(json.load(open(d / "data.json")), ensure_ascii=False).replace("</", "<\\/")
html = (d / "dashboard.html").read_text()
html, n = re.subn(r'(<script type="application/json" id="budget-data">).*?(</script>)',
                  lambda m: m.group(1) + data + m.group(2), html, count=1, flags=re.S)
assert n == 1, "data block not found"
(d / "dashboard.html").write_text(html)
page = ('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="robots" content="noindex, nofollow">\n'
        '<meta name="theme-color" content="#F3F4FA" media="(prefers-color-scheme: light)">\n'
        '<meta name="theme-color" content="#0E1122" media="(prefers-color-scheme: dark)">\n'
        '</head>\n<body>\n' + html + '\n</body>\n</html>\n')
(d / "docs").mkdir(exist_ok=True)
(d / "docs" / "index.html").write_text(page)
(d / "docs" / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
print("ok", json.loads(data.replace("<\\/", "</"))["expenses"].__len__(), "expenses")
