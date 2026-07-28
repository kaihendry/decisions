# Rules

1. An ADR must concern a **single architecture decision**, though it may (and usually does) concern multiple *forces* at play.
2. ADRs should be written in **plain text**, ideally using a text document format or simple markup.
3. ADRs should be **versioned** either in a VCS, a wiki or a similar system.
4. Each ADR must be stored in a **single file** or a single wiki page.
5. ADRs must be numbered **monotonic**ally.
6. Once an ADR has been accepted it must remain **immutable**. If parts or all of the decision change, a new ADR must be made *superseding* the original.

## How this repo enforces them

| Rule | Mechanism |
| --- | --- |
| 1 | Not machine-checkable. Review catches it — one `decision:` block, one call. |
| 2 | YAML source, no binary formats. |
| 3 | git, published at https://github.com/kaihendry/decisions. Every page links to its own file's commit history — that link *is* the immutability evidence for rule 6. |
| 4 | One decision per `YYYY/<slug>.yaml`; the filename *is* the slug, and `build.py` checks it is a valid slug and the directory matches `date`. |
| 5 | Partially. See below — the date orders records, `build.py` rejects duplicate `date/slug`. |
| 6 | The `status` enum plus the schema's conditional: `Superseded` requires `supersededBy`. |

Validation uses `pattern`, not `format`. JSON Schema `format` is advisory —
`jsonschema`'s `uri` checker is a silent no-op unless an extra package is
installed, so `feedback: ask around` validated clean until this was changed.

## Every record carries a reply address

`feedback:` is required on every record and rendered at the foot of every page
as a `mailto:` link. Not the owner's title — an address you can actually send
to.

This is the difference between a decision record and an announcement. A page
that states a decision and offers no way to argue with it trains people to
skim it, and once they skim it the canonical URL is worth nothing. The reply
path is also the intake for rule 6: disagreement doesn't edit the record, it
produces the next one.

Site-wide address for the index page lives in `SITE_FEEDBACK` in `build.py`.

## Naming: a decision, not a topic

Rule 1 says one ADR, one decision. The filename is where that either holds or
quietly rots, so name the slug after **what was decided**, verb first:

| Reads as a decision | Reads as a topic page |
| --- | --- |
| `approve-llm-assistants` | `ai-policy` |
| `move-to-monthly-releases` | `release-process` |
| `drop-ie11-support` | `browser-support` |

A topic-shaped name is an invitation to keep editing one page forever, which
is exactly what rule 6 forbids. A decision-shaped name has nowhere to grow:
the next decision on the same subject gets its own record and supersedes this
one. It also makes the URL self-describing in a town hall — you say
"see slash 2026-07-17 slash approve-llm-assistants" and people already know
what it says.

The slug pattern permits mixed case (`AI-policy` is legal) but lowercase is the
house style.

## Easy to consume: a summary, and a length budget

A record is only useful if people read it, and a wall of text gets skimmed.
Two things guard against that:

- Every record opens with a one-line `summary` — the decision distilled to a
  sentence, rendered as a standfirst above the prose. A reader gets what was
  decided before choosing how deep to go: title, then summary, then sections.
- `build.py` carries a soft length budget per field (`BUDGET`). Over budget it
  prints a warning but still builds — a nudge, not a gate, because the right
  length is a judgement call and a hard cap would invite gaming over clarity.

## Two frictions worth knowing

**Rule 5 is deliberately not followed to the letter.** There is no ADR number.
The identifier is the canonical URL — `2026-07-27/record-decisions` — and
nothing else. A second number would be a second identity to keep in sync, and
the one people actually cite is the URL.

What rule 5 is really asking for is a stable identifier and a defined order.
The date gives the order; `date/slug` gives the identity, and `build.py`
rejects a collision. What is genuinely lost: two decisions on the same day
have no defined order between them. That has not mattered in practice — if it
ever does, the answer is git history, not a counter.

**Rule 6 is not literally enforceable, so it is evidenced instead.** Marking an ADR superseded *is* an
edit to an accepted, supposedly immutable record. The working rule: once
accepted, the only permitted change is `status: Accepted -> Superseded` plus
adding `supersededBy`. Everything else requires a new ADR. Git history is
what proves nobody did otherwise, which is why rule 3 is load-bearing.
