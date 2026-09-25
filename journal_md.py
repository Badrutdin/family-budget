"""Собирает журнал периода (markdown) из data.json той же логикой, что и дашборд."""
import datetime

EMO = {"good": "🟢", "warn": "🟡", "bad": "🔴", "neutral": "⚪"}


def f(n, dec=False):
    if dec and round(n, 2) != round(n):
        return f"{n:,.2f}".replace(",", " ").replace(".", ",")
    return f"{round(n):,}".replace(",", " ")


def day(s):
    return datetime.date.fromisoformat(s).toordinal()


def dm(n):
    return datetime.date.fromordinal(n).strftime("%d.%m")


def build(d, today=None):
    c, exp = d["config"], [e for e in d["expenses"] if e["period"] == d["config"]["period"]]
    start, end = day(c["start"]), day(c["end"])
    days = end - start + 1
    t = min(max((today or datetime.date.today()).toordinal(), start - 1), end)
    el = max(0, t - start + 1)
    frac = el / days

    def env_exp(e):
        a, b = day(e["from"]), day(e["to"])
        if t < a: return 0
        if t >= b: return e["amount"]
        return e["amount"] * (t - a + 1) / (b - a + 1)

    envs = []
    for e in c["envelopes"]:
        sp = sum(x["amount"] for x in exp if x.get("envelope") == e["key"])
        envs.append({**e, "spent": sp, "exp": env_exp(e), "cur": day(e["from"]) <= t <= day(e["to"])})
    week = next((e for e in envs if e["kind"] == "week" and e["cur"]), None)
    snack = sum(x["amount"] for x in exp if week and x["category"] == "products" and x.get("sub") == c["snackSub"]
                and day(week["from"]) <= day(x["date"]) <= day(week["to"]))
    snack_norm = c["snackWeekly"] * ((day(week["to"]) - day(week["from"]) + 1) / 7 if week else 1)

    cats = []
    for k in c["categories"]:
        sp = sum(x["amount"] for x in exp if x["category"] == k["key"])
        ex = sum(e["exp"] for e in envs) if k["kind"] == "envelopes" else k["limit"] * frac
        st, lab = "good", "в норме"
        if k["kind"] == "other":
            ex = 0
            if sp > 0: st, lab = "bad", "есть траты"
        elif sp > k["limit"]: st, lab = "bad", "лимит превышен"
        elif k["kind"] == "fixed": st, lab = ("neutral", "ждём платёж") if sp == 0 else ("good", "оплачено")
        elif k["kind"] == "accum":
            if sp == 0: st, lab = "neutral", "копится"
        elif sp == 0: st, lab = "neutral", "нет трат"
        else:
            dd = (sp - ex) / k["limit"]
            if dd > 0.2: st, lab = "bad", "обгон плана"
            elif dd > 0.1: st, lab = "warn", "обгон плана"
        if k["key"] == "products" and snack > snack_norm and st == "good": st, lab = "warn", "снеки сверх нормы"
        cats.append({**k, "spent": sp, "exp": ex, "st": st, "lab": lab})
    total = sum(x["amount"] for x in exp)
    lim = sum(k["limit"] for k in cats)

    L = [f"# Траты: {dm(start)} - {dm(end)}.{c['end'][:4]}", "",
         f"Файл собирается автоматически из `data.json` скриптом `update_dashboard.py`, руками не править. Правила: [plan.md](plan.md).", "",
         f"Период **{days} дней**, одна месячная сумма. Цель на период: план **{f(c['goal'])} ₽**. Планка 160 000 ₽ с ноября.", "",
         f"Прошло дней: **{el} из {days}**. Потрачено **{f(total)} ₽**, осталось **{f(c['goal']-total)} ₽**.", "",
         "## Сводка по категориям", "",
         "Норма на сегодня: лимит × прошедшие дни / длина периода. Продукты сравниваются с конвертами.", "",
         "| Категория | Лимит | В день | Потрачено | Остаток | Норма на сегодня | Статус |",
         "|---|---:|---:|---:|---:|---:|---|"]
    for k in cats:
        per = f(k["limit"] / days) if k["kind"] in ("daily", "envelopes") else ""
        norm = {"fixed": "по факту платежа", "accum": "копится", "other": "0"}.get(k["kind"], f(k["exp"]))
        L.append(f"| {k['name']} | {f(k['limit'])} | {per} | {f(k['spent'])} | {f(k['limit']-k['spent'])} | {norm} | {EMO[k['st']]} {k['lab']} |")
    L += [f"| **Итого** | **{f(lim)}** | **{f(lim/days)}** | **{f(total)}** | **{f(lim-total)}** | | |", "",
          "## Продуктовые конверты", "",
          "| Конверт | Даты | Сумма | Потрачено | Остаток | Статус |", "|---|---|---:|---:|---:|---|"]
    for e in envs:
        dd = (e["spent"] - e["exp"]) / e["amount"]
        st = ("bad", "пуст") if e["spent"] > e["amount"] else ("neutral", "впереди") if e["spent"] == 0 and e["exp"] == 0 else \
             ("bad", "быстро") if dd > 0.2 else ("warn", "быстро") if dd > 0.1 else ("good", "норма")
        L.append(f"| {e['name']}{' (сейчас)' if e['cur'] else ''} | {dm(day(e['from']))} - {dm(day(e['to']))} | {f(e['amount'])} | {f(e['spent'])} | {f(e['amount']-e['spent'])} | {EMO[st[0]]} {st[1]} |")
    ea, es = sum(e["amount"] for e in envs), sum(e["spent"] for e in envs)
    L += [f"| **Итого** | | **{f(ea)}** | **{f(es)}** | **{f(ea-es)}** | |", "",
          f"Снеки и пиво на текущей неделе: {f(snack)} из {f(snack_norm)} ₽.", ""]
    n = d.get("notes") or {}
    L += ["## Темп и оценка", ""]
    if n.get("headline"): L += [f"**{n.get('updated','')}:** {n['headline']}", ""]
    for i in n.get("items", []): L.append(f"- {EMO.get(i['level'],'⚪')} {i['text']}")
    a = d.get("advice") or {}
    if a.get("groups"):
        L += ["", "## Экономия и рекомендации", ""]
        if a.get("target"): L += [f"Цель: {a['target']}.", ""]
        for g in a["groups"]:
            L.append(f"**{g['title']}**")
            for i in g["items"]:
                L.append(f"- {i['text']}" + (f" **−{f(i['save'])} ₽{i.get('per','')}**" if i.get("save") else ""))
            L.append("")
    mem = {}
    for x in exp: mem[x["member"]] = mem.get(x["member"], 0) + x["amount"]
    L += ["## Сводка по членам семьи", "", "| Кому | Потрачено |", "|---|---:|"]
    for m in ["Я", "Жена", "Ребёнок", "Семья"] + [m for m in mem if m not in ("Я", "Жена", "Ребёнок", "Семья")]:
        L.append(f"| {m} | {f(mem.get(m,0))} |")
    L += ["", "## Одежда и развлечения", "", "| Подкатегория | Я | Жена | Ребёнок |", "|---|---:|---:|---:|"]
    for sname in ("Одежда", "Развлечения"):
        L.append(f"| {sname} | " + " | ".join(f(sum(x["amount"] for x in exp if x.get("sub") == sname and x["member"] == m)) for m in ("Я", "Жена", "Ребёнок")) + " |")
    subs = {}
    for x in exp:
        if x["category"] == "products": subs[x.get("sub") or "Другое"] = subs.get(x.get("sub") or "Другое", 0) + x["amount"]
    ps = sum(subs.values())
    L += ["", "## Продукты: разбивка", "", "| Подкатегория | Потрачено | Доля |", "|---|---:|---:|"]
    for sname, v in sorted(subs.items(), key=lambda kv: -kv[1]): L.append(f"| {sname} | {f(v)} | {round(v/ps*100)}% |")
    if ps: L.append(f"| **Итого** | **{f(ps)}** | |")
    names = {k["key"]: k["name"] for k in c["categories"]}
    L += ["", "## Журнал трат", "", "| № | Дата | Категория | Подкатегория | Кому | Что | Сумма ₽ | Оплата | Примечание |",
          "|---:|---|---|---|---|---|---:|---|---|"]
    for x in sorted(exp, key=lambda x: (x["date"], x["n"])):
        L.append(f"| {x['n']} | {dm(day(x['date']))} | {names.get(x['category'], x['category'])} | {x.get('sub','')} | {x['member']} | {x['item']} | {f(x['amount'], True)} | {x.get('pay','')} | {x.get('note','')} |")
    grp = lambda k: 0 if k == "products" else 1 if k in ("me", "wife") else 2 if k in ("kid", "kindergarten") else 3
    byd = {}
    for x in exp: byd.setdefault(x["date"], [0, 0, 0, 0])[grp(x["category"])] += x["amount"]
    L += ["", "## По дням", "", "Личное = я + жена, Ребёнок = ребёнок + садик.", "",
          "| Дата | Продукты | Личное | Ребёнок | Остальное | Итого за день |", "|---|---:|---:|---:|---:|---:|"]
    for dt in sorted(byd): v = byd[dt]; L.append(f"| {dm(day(dt))} | " + " | ".join(f(x) for x in v) + f" | {f(sum(v))} |")
    return "\n".join(L) + "\n"
