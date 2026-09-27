#!/usr/bin/env python3
"""Встраивает data.json в dashboard.html, собирает docs/index.html для GitHub Pages и журнал периода .md."""
import json, re, pathlib
from journal_md import build
d = pathlib.Path(__file__).parent
data = json.dumps(json.load(open(d / "data.json")), ensure_ascii=False).replace("</", "<\\/")
html = (d / "dashboard.html").read_text()
html, n = re.subn(r'(<script type="application/json" id="budget-data">).*?(</script>)',
                  lambda m: m.group(1) + data + m.group(2), html, count=1, flags=re.S)
assert n == 1, "data block not found"
(d / "dashboard.html").write_text(html)
PAGES = [("home", "index.html", "Главная", ""),
         ("products", "products.html", "Продукты", "#plist{order:-1}"),
         ("menu", "menu.html", "Меню", ""),
         ("journal", "journal.html", "Журнал", "#journal{order:-1}"),
         ("savings", "savings.html", "Экономия", "#savings{order:-1}")]
(d / "docs").mkdir(exist_ok=True)
for key, fname, title, extra in PAGES:
    body = html.replace("<title>Семейный бюджет</title>", f"<title>Семейный бюджет · {title}</title>", 1)
    page = (f'<!doctype html>\n<html lang="ru" data-page="{key}">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="robots" content="noindex, nofollow">\n'
            '<meta name="theme-color" content="#F3F4FA" media="(prefers-color-scheme: light)">\n'
            '<meta name="theme-color" content="#0E1122" media="(prefers-color-scheme: dark)">\n'
            f'<style>.pg:not(.pg-{key}):not(.pg-all){{display:none!important}} .top,.jump{{order:-2}} {extra}</style>\n'
            '</head>\n<body>\n' + body + '\n</body>\n</html>\n')
    (d / "docs" / fname).write_text(page)
(d / (json.load(open(d / "data.json"))["config"]["period"] + ".md")).write_text(build(json.load(open(d / "data.json"))))
(d / "docs" / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
print("ok", json.loads(data.replace("<\\/", "</"))["expenses"].__len__(), "expenses")
