#!/usr/bin/env python3
"""Task journal for an agent working with a human author: one row per significant task, written at the retro.

  journal.py add --project P --area A --task "..." --rounds N [--causes "c1; c2"] [--changes "skill:x ...; hook:y"] [--date YYYY-MM-DD]
  journal.py list [--project P] [--area A] [--limit N]
  journal.py stats [--project P] [--by month|week]

rounds  = how many times the human had to send the work back (0 = accepted as first shown).
causes  = why each round happened, ';'-separated ("did not look at the scene myself; wrong camera axis").
changes = what the retro changed so it does not repeat, ';'-separated, prefixed by kind
          (skill:<name> <what>, rule:..., hook:..., tool:..., memory:...). Empty changes = the retro is not done.

`stats` shows rounds per area over time, the most common causes, and for every recorded change the mean rounds of
the same area before and after it - which changes preceded fewer rounds. It is correlation on small numbers,
not proof; read it as "worth keeping / worth a second look".

DB: $AGENT_JOURNAL_DB or ~/.claude/agent-journal.sqlite. Python 3 standard library only.
"""

import argparse
import datetime as dt
import os
import sqlite3
import sys
from collections import Counter, defaultdict

DB = os.environ.get("AGENT_JOURNAL_DB") or os.path.join(os.path.expanduser("~"), ".claude", "agent-journal.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date    TEXT NOT NULL,
    project TEXT NOT NULL,
    area    TEXT NOT NULL,
    task    TEXT NOT NULL,
    rounds  INTEGER NOT NULL,
    causes  TEXT NOT NULL DEFAULT '',
    changes TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS tasks_area ON tasks(project, area, date);
"""


def connect():
    os.makedirs(os.path.dirname(os.path.abspath(DB)), exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def items(text):
    return [s.strip() for s in (text or "").split(";") if s.strip()]


def where(args, fields=("project", "area")):
    sql, params = [], []
    for f in fields:
        value = getattr(args, f, None)
        if value:
            sql.append(f"{f} = ?")
            params.append(value)
    return (" WHERE " + " AND ".join(sql)) if sql else "", params


def cmd_add(args):
    date = args.date or dt.date.today().isoformat()
    dt.date.fromisoformat(date)  # validate
    if args.rounds < 0:
        sys.exit("rounds must be >= 0")
    with connect() as con:
        cur = con.execute(
            "INSERT INTO tasks(date, project, area, task, rounds, causes, changes) VALUES (?,?,?,?,?,?,?)",
            (date, args.project, args.area, args.task, args.rounds, "; ".join(items(args.causes)),
             "; ".join(items(args.changes))))
    print(f"#{cur.lastrowid} {date} {args.project}/{args.area} rounds={args.rounds}", flush=True)
    if args.rounds > 0 and not items(args.changes):
        print("warning: no changes recorded - a retro that changes nothing will repeat the same rounds", file=sys.stderr)


def cmd_list(args):
    clause, params = where(args)
    with connect() as con:
        rows = con.execute(f"SELECT * FROM tasks{clause} ORDER BY date DESC, id DESC LIMIT ?",
                           params + [args.limit]).fetchall()
    if not rows:
        print("no tasks")
        return
    for r in rows:
        print(f'#{r["id"]} {r["date"]} {r["project"]}/{r["area"]} rounds={r["rounds"]}  {r["task"]}')
        for c in items(r["causes"]):
            print(f"    cause:  {c}")
        for c in items(r["changes"]):
            print(f"    change: {c}")


def period(date, by):
    d = dt.date.fromisoformat(date)
    if by == "week":
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"
    return date[:7]


def mean(values):
    return sum(values) / len(values) if values else None


def fmt(x):
    return "  -  " if x is None else f"{x:5.2f}"


def cmd_stats(args):
    clause, params = where(args, ("project",))
    with connect() as con:
        rows = con.execute(f"SELECT * FROM tasks{clause} ORDER BY date, id", params).fetchall()
    if not rows:
        print("no tasks")
        return

    # 1. Rounds per area over time.
    periods = sorted({period(r["date"], args.by) for r in rows})
    table = defaultdict(lambda: defaultdict(list))
    for r in rows:
        table[f'{r["project"]}/{r["area"]}'][period(r["date"], args.by)].append(r["rounds"])
    width = max(len(a) for a in table)
    print(f"Mean rounds per task, by {args.by} (n = tasks)")
    print(" " * width + "  " + "  ".join(f"{p:>12}" for p in periods) + "   overall")
    for area in sorted(table):
        cells = []
        for p in periods:
            v = table[area].get(p)
            cells.append(f"{fmt(mean(v))} (n={len(v)})".rjust(12) if v else " " * 12)
        all_v = [x for v in table[area].values() for x in v]
        print(f"{area:<{width}}  " + "  ".join(cells) + f"   {fmt(mean(all_v))} (n={len(all_v)})")

    # 2. Most common causes.
    causes = Counter(c.lower() for r in rows for c in items(r["causes"]))
    if causes:
        print("\nMost common causes of rounds")
        for c, n in causes.most_common(10):
            print(f"  {n:3d}  {c}")

    # 3. Each change: rounds in its area before vs after it.
    print("\nChanges and the rounds of their area before / after (same project+area; 'before' includes the task that prompted it)")
    any_change = False
    for r in rows:
        for change in items(r["changes"]):
            any_change = True
            same = [x for x in rows if x["project"] == r["project"] and x["area"] == r["area"]]
            before = [x["rounds"] for x in same if (x["date"], x["id"]) <= (r["date"], r["id"])]
            after = [x["rounds"] for x in same if (x["date"], x["id"]) > (r["date"], r["id"])]
            b, a = mean(before), mean(after)
            verdict = ("not enough data" if a is None or len(after) < 2 else
                       "fewer rounds after" if a < b else "no improvement - revisit")
            print(f'  {r["date"]} {r["project"]}/{r["area"]}: {change}')
            print(f"      before {fmt(b)} (n={len(before)})  after {fmt(a)} (n={len(after)})  -> {verdict}")
    if not any_change:
        print("  none recorded")
    missing = sum(1 for r in rows if r["rounds"] > 0 and not items(r["changes"]))
    if missing:
        print(f"\n{missing} task(s) with rounds > 0 and no change recorded - retros not finished")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="record a finished task")
    a.add_argument("--project", required=True)
    a.add_argument("--area", required=True, help="e.g. ui, cinematics, networking, build, docs")
    a.add_argument("--task", required=True)
    a.add_argument("--rounds", type=int, required=True, help="times the human sent the work back")
    a.add_argument("--causes", default="", help="';'-separated reasons for the rounds")
    a.add_argument("--changes", default="", help="';'-separated changes made by the retro (skill:/rule:/hook:/tool:)")
    a.add_argument("--date", help="YYYY-MM-DD, default today")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list", help="show recorded tasks")
    l.add_argument("--project")
    l.add_argument("--area")
    l.add_argument("--limit", type=int, default=30)
    l.set_defaults(func=cmd_list)

    s = sub.add_parser("stats", help="rounds per area over time; which changes preceded fewer rounds")
    s.add_argument("--project")
    s.add_argument("--by", choices=("month", "week"), default="month")
    s.set_defaults(func=cmd_stats)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
