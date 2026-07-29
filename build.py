#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""Build the decision site from YYYY/*.yaml. Usage: ./build.py [outdir]"""

import html
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).parent
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "site")

SITE = "decisions.dabase.com"
SITE_FEEDBACK = "hendry@iki.fi"  # index page; each decision names its own
REPO = "https://github.com/kaihendry/decisions"  # rule 3: the audit trail

SLUG = re.compile(r"^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$")  # the filename is the slug

# Soft length budgets (chars). Over these, build.py warns but still succeeds —
# a nudge to keep a record consumable, not a wall of text. See RULES.md.
BUDGET = {"summary": 240, "context": 1200, "decision": 1500, "compliance": 800}

CSS = """
:root {
  color-scheme: light dark;
  --bg:     #fcfbf8;
  --fg:     #1b1a17;
  --dim:    #6d6a62;
  --rule:   #e4dfd4;
  --accent: #8a3324;
  --ok:     #1a7f37;
  --warn:   #9a6700;
  --serif:  Charter, "Bitstream Charter", "Iowan Old Style", Georgia, serif;
  --sans:   system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono:   ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg:     #161513;
    --fg:     #e6e3dc;
    --dim:    #9a958a;
    --rule:   #322f2a;
    --accent: #e08b7a;
    --ok:     #4ac26b;
    --warn:   #d4a72c;
  }
}

* { box-sizing: border-box; }

body {
  max-width: 38rem;
  margin: 0 auto;
  padding: 4rem 1.5rem 6rem;
  background: var(--bg);
  color: var(--fg);
  font: 1.0625rem/1.65 var(--serif);
  -webkit-text-size-adjust: 100%;
}

a { color: inherit; text-decoration-color: var(--rule); text-underline-offset: .15em; }
a:hover { text-decoration-color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }

/* ---- masthead ---- */

.up {
  font: .8125rem/1 var(--sans);
  letter-spacing: .02em;
  color: var(--dim);
  margin: 0 0 2.5rem;
}

h1 {
  font-size: 1.75rem;
  line-height: 1.25;
  font-weight: 600;
  letter-spacing: -.01em;
  margin: 0 0 .75rem;
  text-wrap: balance;
}

.byline {
  font: .8125rem/1.5 var(--sans);
  color: var(--dim);
  margin: 0 0 .5rem;
  display: flex;
  flex-wrap: wrap;
  gap: .5rem .75rem;
  align-items: center;
}

.canonical {
  margin: 0 0 2.5rem;
  padding: 0 0 2rem;
  border-bottom: 1px solid var(--rule);
}
.copy {
  font: 600 .6875rem/1 var(--sans);
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--accent);
  background: none;
  border: 1px solid var(--rule);
  border-radius: 2em;
  padding: .5em .9em .45em;
  cursor: pointer;
}
.copy:hover { border-color: var(--accent); }
.copy.copied { color: var(--ok); border-color: var(--ok); }

.summary {
  font: 1.25rem/1.5 var(--serif);
  margin: 0 0 2.5rem;
  padding: 0 0 2rem;
  border-bottom: 1px solid var(--rule);
  text-wrap: pretty;
}

.status {
  font: 600 .6875rem/1 var(--sans);
  text-transform: uppercase;
  letter-spacing: .07em;
  border: 1px solid currentColor;
  border-radius: 2em;
  padding: .35em .7em .3em;
  white-space: nowrap;
}
.Accepted   { color: var(--ok); }
.Proposed   { color: var(--warn); }
.Superseded { color: var(--dim); }

.superseded-by {
  border-left: 3px solid var(--warn);
  padding: .5rem 0 .5rem 1rem;
  margin: 0 0 2rem;
  font-size: .9375rem;
}

/* ---- sections ---- */

h2 {
  font: 600 .6875rem/1 var(--sans);
  text-transform: uppercase;
  letter-spacing: .11em;
  color: var(--dim);
  margin: 2.75rem 0 .85rem;
  scroll-margin-top: 2rem;
}
h2 .anchor {
  margin-left: .4em;
  color: var(--accent);
  text-decoration: none;
  opacity: 0;
  transition: opacity .12s;
}
h2:hover .anchor, h2 .anchor:focus-visible { opacity: 1; }

p { margin: 0 0 1.15rem; }

h3 {
  font: 600 .8125rem/1 var(--sans);
  color: var(--dim);
  margin: 1.5rem 0 .6rem;
}

ul { margin: 0 0 1.15rem; padding-left: 1.15rem; }
li { margin-bottom: .4rem; }
li::marker { color: var(--dim); }
.positive li::marker { content: "+  "; color: var(--ok); font-weight: 700; }
.negative li::marker { content: "\\2212  "; color: var(--accent); font-weight: 700; }
.positive, .negative { list-style: none; padding-left: 1.15rem; }

dl { margin: 0; font-size: .9375rem; }
dt {
  font: 600 .6875rem/1.4 var(--sans);
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--dim);
  margin-top: .85rem;
}
dd { margin: .15rem 0 0; word-break: break-word; }

/* ---- index ---- */

.adrs { list-style: none; margin: 0; padding: 0; }
.adrs li { margin: 0; border-bottom: 1px solid var(--rule); }
.adrs li:first-child { border-top: 1px solid var(--rule); }
.adrs li:last-child { border-bottom: 0; }  /* feedback block's top rule closes the list */
.adrs a {
  display: block;
  padding: 1.15rem 0;
  text-decoration: none;
}
.adrs a:hover .t { text-decoration: underline; text-decoration-color: var(--accent); }
.adrs .t { display: block; font-size: 1.0625rem; margin-bottom: .5rem; text-wrap: balance; }

.lede { color: var(--dim); font-size: .9375rem; margin: -.25rem 0 2.5rem; }

/* ---- footer ---- */

.feedback {
  margin: 4rem 0 0;
  padding-top: 1.25rem;
  border-top: 1px solid var(--rule);
  font: .875rem/1.6 var(--sans);
}
.feedback a { text-decoration-color: var(--accent); }
.feedback .note { display: block; margin-top: .4rem; color: var(--dim); font-size: .8125rem; }

@media print {
  :root { --bg: #fff; --fg: #000; --dim: #444; --rule: #bbb; }
  body { max-width: none; padding: 0; font-size: 11pt; }
  .up, .feedback a { text-decoration: none; }
  .canonical, h2 .anchor { display: none; }
  h2 { break-after: avoid; }
  li, p { break-inside: avoid; }
}
"""


SCRIPT = """
for (const b of document.querySelectorAll('.copy')) {
  b.addEventListener('click', () => {
    navigator.clipboard.writeText(b.dataset.copy);
    b.textContent = 'Copied';
    b.classList.add('copied');
    setTimeout(() => { b.textContent = 'Copy link'; b.classList.remove('copied'); }, 1500);
  });
}
"""


def esc(s):
    return html.escape(str(s))


def link(url, text=None):
    return f'<a href="{esc(url)}">{esc(text or url)}</a>'


def heading(text):
    """<h2> with a hover anchor, so any section can be deep-linked."""
    slug = text.lower()
    return (
        f'<h2 id="{slug}">{esc(text)}'
        f' <a class="anchor" href="#{slug}" aria-label="Link to {esc(text)}">#</a></h2>'
    )


def age(iso):
    """Human age of a decision, relative to the build date."""
    days = (date.today() - date.fromisoformat(iso)).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 14:
        return f"{days} days ago"
    if days < 60:
        return f"{days // 7} weeks ago"
    if days < 730:
        return f"{days // 30} months ago"
    return f"{days // 365} years ago"


def page(title, body, script=""):
    """Assemble a full document. body is a list of lines, indented one level."""
    doc = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{esc(title)}</title>",
        "  <style>",
        *[f"  {ln}" if ln.strip() else "" for ln in CSS.strip().splitlines()],
        "  </style>",
        "</head>",
        "<body>",
        *[f"  {ln}" if ln.strip() else "" for ln in body],
    ]
    if script:
        doc += [
            "  <script>",
            *[f"  {ln}" if ln.strip() else "" for ln in script.strip().splitlines()],
            "  </script>",
        ]
    doc += ["</body>", "</html>", ""]
    return "\n".join(doc)


def paras(text):
    """Prose block -> <p> lines, keeping the source's line breaks for readability."""
    out = []
    for block in text.strip().split("\n\n"):
        lines = [esc(ln.strip()) for ln in block.strip().splitlines() if ln.strip()]
        if not lines:
            continue
        if len(lines) == 1:
            out.append(f"<p>{lines[0]}</p>")
        else:
            out += ["<p>", *[f"  {ln}" for ln in lines], "</p>"]
    return out


def items(xs, cls):
    return [f'<ul class="{cls}">', *[f"  <li>{esc(x)}</li>" for x in xs], "</ul>"]


def status_badge(s):
    return f'<span class="status {s}">{esc(s)}</span>'


def feedback_block(to, source=None):
    href = to if to.startswith("http") else f"mailto:{to}"
    hist = f"{REPO}/commits/main/{source}" if source else f"{REPO}/commits/main"
    what = "this record" if source else "every record"
    return [
        '<p class="feedback">',
        f"  Disagree, or spot something wrong? {link(href, to)}",
        '  <span class="note">',
        "    Records change by being superseded, so say so and it gets a new one.",
        f"    Every change to {what} is in the {link(hist, 'commit history')}.",
        "  </span>",
        "</p>",
    ]


def load():
    schema = yaml.safe_load((ROOT / "adr.schema.yaml").read_text())
    validator = jsonschema.Draft202012Validator(schema)
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
        if not SLUG.match(path.stem):
            sys.exit(f"{path}: filename {path.name} is not a valid slug ({SLUG.pattern})")
        adr["slug"] = path.stem  # identity is the filename
        adr["source"] = str(path.relative_to(ROOT))  # both added after validation
        url = f"{adr['date']}/{adr['slug']}"
        if url in seen:
            sys.exit(f"{path}: {url} already taken by {seen[url]}")
        seen[url] = path
        for field, limit in BUDGET.items():
            n = len(adr[field].strip())
            if n > limit:
                print(f"warning: {path}: {field} is {n} chars, over the {limit} budget", file=sys.stderr)
        adrs.append(adr)
    return adrs


def render(adr):
    n = adr["notes"]
    url = f"{SITE}/{adr['date']}/{adr['slug']}"
    body = [
        '<p class="up"><a href="../../">&larr; Decisions</a></p>',
        f"<h1>{esc(adr['title'])}</h1>",
        '<p class="byline">',
        f"  {status_badge(adr['status'])}",
        f"  <span>{esc(adr['date'])}</span>",
        f"  <span>{esc(n['owner'])}</span>",
        "</p>",
        '<p class="canonical">',
        f'  <button class="copy" type="button" data-copy="https://{esc(url)}">Copy link</button>',
        "</p>",
        f'<p class="summary">{esc(adr["summary"])}</p>',
    ]
    if sb := adr.get("supersededBy"):
        body += [
            '<p class="superseded-by">',
            f"  This decision has been superseded by {link(sb)}.",
            "</p>",
        ]
    body += [
        heading("Context"),
        *paras(adr["context"]),
        heading("Decision"),
        *paras(adr["decision"]),
        heading("Consequences"),
        "<h3>Positive</h3>",
        *items(adr["consequences"]["positive"], "positive"),
        "<h3>Negative</h3>",
        *items(adr["consequences"]["negative"], "negative"),
        heading("Compliance"),
        *paras(adr["compliance"]),
        heading("Notes"),
        "<dl>",
    ]
    for k, v in n.items():
        v = ", ".join(v) if isinstance(v, list) else str(v)
        v = link(v) if v.startswith("http") else esc(v)
        body += [f"  <dt>{esc(k)}</dt>", f"  <dd>{v}</dd>"]
    body += ["</dl>", *feedback_block(adr["feedback"], adr["source"])]
    return page(adr["title"], body, SCRIPT)


def index(adrs):
    rows = []
    for adr in newest_first(adrs):
        rows += [
            "  <li>",
            f'    <a href="{esc(adr["date"])}/{esc(adr["slug"])}/">',
            f'      <span class="t">{esc(adr["title"])}</span>',
            '      <span class="byline">',
            f"        {status_badge(adr['status'])}",
            f"        <span>{esc(adr['date'])} &middot; {esc(age(adr['date']))}</span>",
            f"        <span>{esc(adr['notes']['owner'])}</span>",
            "      </span>",
            "    </a>",
            "  </li>",
        ]
    body = [
        "<h1>Decisions</h1>",
        '<p class="lede">',
        f"  Every decision made here has one record at {SITE}/YYYY-MM-DD/decision-name.",
        "  Anything else said about a decision links back to its record.",
        "</p>",
        '<ul class="adrs">',
        *rows,
        "</ul>",
        *feedback_block(SITE_FEEDBACK),
    ]
    return page("Decisions", body)


def canonical(adr):
    return f"https://{SITE}/{adr['date']}/{adr['slug']}/"


def newest_first(adrs):
    return sorted(adrs, key=lambda a: (a["date"], a["slug"]), reverse=True)


def md_record(adr):
    """One decision as Markdown — the body of llms-full.txt."""
    n = adr["notes"]
    out = [
        f"# {adr['title']}",
        "",
        canonical(adr),
        "",
        f"{adr['status']} · {adr['date']} · {n['owner']}",
        "",
        f"> {adr['summary'].strip()}",
        "",
    ]
    if sb := adr.get("supersededBy"):
        out += [f"**Superseded by {sb}**", ""]
    out += [
        "## Context", "", adr["context"].strip(), "",
        "## Decision", "", adr["decision"].strip(), "",
        "## Consequences", "",
        "### Positive", "",
        *[f"- {x}" for x in adr["consequences"]["positive"]], "",
        "### Negative", "",
        *[f"- {x}" for x in adr["consequences"]["negative"]], "",
        "## Compliance", "", adr["compliance"].strip(), "",
        "## Notes", "",
    ]
    for k, v in n.items():
        out.append(f"- {k}: {', '.join(v) if isinstance(v, list) else v}")
    return "\n".join(out)


HEADERS = """\
/*.txt
  Content-Type: text/plain; charset=utf-8

/adr.schema.yaml
  Content-Type: text/yaml; charset=utf-8
"""


def llms_txt(adrs):
    """An /llms.txt index: what the site is, then a link per decision."""
    lines = [
        "# Decisions",
        "",
        f"> Architecture decision records published at https://{SITE}. One "
        "decision, one record, one canonical URL — every other communication "
        "(email, town hall, deck, video) links back to the record instead of "
        "restating it.",
        "",
        "Records follow Michael Nygard's ADR format (context, decision, "
        "consequences, compliance) and are immutable once accepted: a reversed "
        "decision is superseded by a new record, never edited in place. Cite a "
        "decision by its canonical URL.",
        "",
        "## Decisions",
        "",
    ]
    for adr in newest_first(adrs):
        lines.append(
            f"- [{adr['title']}]({canonical(adr)}): "
            f"{adr['status']}, {adr['date']}. {adr['summary'].strip()}"
        )
    lines += [
        "",
        "## Optional",
        "",
        f"- [Full text of every decision](https://{SITE}/llms-full.txt): all "
        "records inline as one Markdown file.",
        f"- [Record schema](https://{SITE}/adr.schema.yaml): the JSON Schema "
        "every record validates against.",
        f"- [Source repository]({REPO}): YAML records and build; the commit "
        "history is the audit trail.",
        "",
    ]
    return "\n".join(lines)


def llms_full(adrs):
    """An /llms-full.txt: every record inline as Markdown, newest first."""
    parts = [
        "# Decisions — full text",
        "",
        f"> Every architecture decision record from https://{SITE}, inline as "
        "one Markdown file. The canonical URL under each title is the thing to "
        "cite, not this file.",
        "",
    ]
    for adr in newest_first(adrs):
        parts += ["---", "", md_record(adr), ""]
    return "\n".join(parts)


adrs = load()
shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir(parents=True)
(OUT / "index.html").write_text(index(adrs))
for adr in adrs:
    d = OUT / adr["date"] / adr["slug"]
    d.mkdir(parents=True)
    (d / "index.html").write_text(render(adr))
(OUT / "llms.txt").write_text(llms_txt(adrs) + "\n")
(OUT / "llms-full.txt").write_text(llms_full(adrs) + "\n")
shutil.copy(ROOT / "adr.schema.yaml", OUT / "adr.schema.yaml")
# Wrangler serves .txt and .yaml with no charset, and browsers then fall back
# to windows-1252 and mangle every em dash. The HTML is fine: it has a <meta>.
(OUT / "_headers").write_text(HEADERS)
print(f"{len(adrs)} decisions -> {OUT}")
