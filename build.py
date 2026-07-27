#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""Build the decision site from YYYY/*.yaml. Usage: ./build.py [outdir]"""

import html
import shutil
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).parent
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "site")

CSS = """
:root { color-scheme: light dark; --fg: #1a1a1a; --dim: #666; --line: #ddd; }
@media (prefers-color-scheme: dark) {
  :root { --fg: #e8e8e8; --dim: #999; --line: #333; }
}
body { max-width: 42rem; margin: 3rem auto; padding: 0 1.5rem; color: var(--fg);
       font: 1rem/1.6 system-ui, sans-serif; }
h1 { font-size: 1.6rem; margin-bottom: .25rem; }
h2 { font-size: .8rem; text-transform: uppercase; letter-spacing: .08em;
     color: var(--dim); margin: 2rem 0 .5rem; }
a { color: inherit; }
ul.adrs { list-style: none; padding: 0; }
ul.adrs li { border-bottom: 1px solid var(--line); padding: .75rem 0; }
.meta { color: var(--dim); font-size: .85rem; }
.status { font-size: .75rem; text-transform: uppercase; letter-spacing: .05em;
          border: 1px solid currentColor; border-radius: 2em; padding: .1em .6em; }
.Accepted { color: #1a7f37; } .Proposed { color: #9a6700; } .Superseded { color: #888; }
dl { margin: 0; } dt { font-weight: 600; } dd { margin: 0 0 .5rem; }
.feedback { border-top: 1px solid var(--line); margin-top: 3rem; padding-top: 1rem;
            font-size: .9rem; }
"""

SITE_FEEDBACK = "hendry@iki.fi"  # index page; each decision names its own
REPO = "https://github.com/kaihendry/decisions"  # rule 3: the audit trail


def feedback_block(to, source=None):
    href = to if to.startswith("http") else f"mailto:{to}"
    hist = f"{REPO}/commits/main/{source}" if source else f"{REPO}/commits/main"
    what = "this record" if source else "every record"
    return (
        f'<p class=feedback>Disagree, or spot something wrong? '
        f'<a href="{html.escape(href)}">{html.escape(to)}</a><br>'
        f'<span class=meta>Records change by being superseded, so say so and '
        f'it gets a new one. '
        f'Every change to {what} is in the '
        f'<a href="{html.escape(hist)}">commit history</a>.</span></p>'
    )


def page(title, body):
    return (
        f"<!doctype html><html lang=en><meta charset=utf-8>"
        f'<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style>{body}"
    )


def paras(text):
    return "".join(
        f"<p>{html.escape(b.strip())}</p>" for b in text.strip().split("\n\n") if b.strip()
    )


def items(xs):
    return "<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in xs) + "</ul>"


def load():
    schema = yaml.safe_load((ROOT / "adr.schema.yaml").read_text())
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    adrs, seen = [], {}
    for path in sorted(ROOT.glob("[0-9][0-9][0-9][0-9]/*.yaml")):
        adr = yaml.safe_load(path.read_text())
        errors = sorted(validator.iter_errors(adr), key=lambda e: e.path)
        for e in errors:
            print(f"{path}: {'.'.join(map(str, e.path)) or '(root)'}: {e.message}")
        if errors:
            sys.exit(1)
        if not adr["date"].startswith(path.parent.name):
            sys.exit(f"{path}: date {adr['date']} does not match directory")
        if adr["slug"] != path.stem:
            sys.exit(f"{path}: slug {adr['slug']} does not match filename")
        url = f"{adr['date']}/{adr['slug']}"
        if url in seen:
            sys.exit(f"{path}: {url} already taken by {seen[url]}")
        seen[url] = path
        adr["source"] = str(path.relative_to(ROOT))  # added after validation
        adrs.append(adr)
    return adrs


def render(adr):
    n = adr["notes"]
    parts = [
        '<p class=meta><a href="../../">Decisions</a></p>',
        f'<h1>{html.escape(adr["title"])}</h1>',
        f'<p class=meta><span class="status {adr["status"]}">{adr["status"]}</span> '
        f'&middot; {adr["date"]} &middot; {html.escape(n["owner"])}</p>',
    ]
    if sb := adr.get("supersededBy"):
        parts.append(f'<p>Superseded by <a href="{html.escape(sb)}">{html.escape(sb)}</a>.</p>')
    parts += [
        "<h2>Context</h2>", paras(adr["context"]),
        "<h2>Decision</h2>", paras(adr["decision"]),
        "<h2>Consequences</h2>",
        "<p>Positive</p>", items(adr["consequences"]["positive"]),
        "<p>Negative</p>", items(adr["consequences"]["negative"]),
        "<h2>Compliance</h2>", paras(adr["compliance"]),
        "<h2>Notes</h2>", "<dl>",
    ]
    for k, v in n.items():
        v = ", ".join(v) if isinstance(v, list) else str(v)
        v = html.escape(v)
        if v.startswith("http"):
            v = f'<a href="{v}">{v}</a>'
        parts.append(f"<dt>{html.escape(k)}</dt><dd>{v}</dd>")
    parts.append("</dl>")
    parts.append(feedback_block(adr["feedback"], adr["source"]))
    return page(adr["title"], "".join(parts))


def index(adrs):
    rows = []
    for adr in sorted(adrs, key=lambda a: (a["date"], a["slug"]), reverse=True):
        href = f'{adr["date"]}/{adr["slug"]}/'
        rows.append(
            f'<li><a href="{href}">{html.escape(adr["title"])}</a>'
            f'<div class=meta><span class="status {adr["status"]}">{adr["status"]}</span> '
            f'&middot; {adr["date"]} &middot; {html.escape(adr["notes"]["owner"])}</div></li>'
        )
    return page(
        "Decisions",
        f"<h1>Decisions</h1><ul class=adrs>{''.join(rows)}</ul>"
        + feedback_block(SITE_FEEDBACK),
    )


adrs = load()
shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir(parents=True)
(OUT / "index.html").write_text(index(adrs))
for adr in adrs:
    d = OUT / adr["date"] / adr["slug"]
    d.mkdir(parents=True)
    (d / "index.html").write_text(render(adr))
print(f"{len(adrs)} decisions -> {OUT}")
