# decisions

Architecture decision records, published as a static site at
**https://decisions.dabase.com**.

One decision, one file, one URL. Everything else — the town hall, the video,
the newsletter, the email — links back to that URL rather than restating the
decision and drifting from it.

Format is [Michael Nygard's][nygard]: title, status, context, decision,
consequences, compliance, notes. The rules the format comes with, and how
much of each one this repo actually enforces, are in [RULES.md](RULES.md).

[nygard]: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions

## Adding a decision

Create `YYYY/<slug>.yaml`, where the year matches the decision's date and the
slug matches its filename:

```yaml
date: "2026-07-27"
slug: record-decisions
title: Record every decision at decisions.dabase.com/YYYY-MM-DD/decision-name
status: Accepted            # Proposed | Accepted | Superseded
feedback: hendry@iki.fi     # an address that accepts replies

context: |
  What forces lead to this decision?

decision: |
  What was decided, and why.

consequences:
  positive:
    - At least one.
  negative:
    - At least one. If this list is empty the section isn't doing its job.

compliance: |
  How will this be measured and enforced?

notes:
  owner: Head of Engineering
```

Name the **decision**, not the topic: `approve-llm-assistants`, not
`ai-policy`. A topic-shaped name invites perpetual editing; a decision-shaped
name has nowhere to grow, so the next decision gets its own record.

Then:

```sh
make view     # build + serve on http://localhost:8000/
make build    # validate and render to ./site
make deploy   # build, then publish to decisions.dabase.com
make clean    # remove ./site
```

`make build` fails loudly on a missing field, a bad status, a date that
disagrees with the directory, a slug that disagrees with the filename, a
duplicate URL, or a `Superseded` record with no `supersededBy`. A record that
doesn't validate never reaches the site.

## How it works

- `adr.schema.yaml` — JSON Schema (2020-12), written in YAML.
- `build.py` — the whole generator. A [uv][uv] inline script, so there is no
  virtualenv to create and no lockfile: `./build.py` just runs. Reads the
  YAML, validates it, writes static HTML.
- `wrangler.jsonc` — a static-assets-only Cloudflare Worker. `make deploy`
  needs `npx wrangler@4 login` once.

[uv]: https://docs.astral.sh/uv/

There is deliberately **no ADR number**. The canonical URL —
`2026-07-27/record-decisions` — is the identity, and a second identifier is
only something else to keep in sync. The date supplies the ordering.

Every published page carries a reply address and a link to its own file's
commit history. That history is the evidence for the immutability rule: a
record that was quietly rewritten instead of superseded would show it.
