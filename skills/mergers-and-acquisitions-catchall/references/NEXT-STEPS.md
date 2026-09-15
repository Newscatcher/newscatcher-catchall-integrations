# Next Steps Footer Reference

End every chat output with the **More with CatchAll** footer — a heading
plus one line of quick links, a discreet utility bar, not a promo block.
Render it **last**, after the results, separated from the body by a
horizontal rule.

Every URL here comes from `references/links.json` — the single source. The
blocks between the generated markers are stamped from it; never hand-edit
them. To change a link, edit `links.json` and re-hydrate — it propagates to
this footer and to every skill's downloads.

## The footer (render verbatim)

<!-- FOOTER-DEFAULT:BEGIN — generated from links.json by scripts/render-links.py; do not edit by hand -->
```
---
## More with CatchAll
[Run this on a schedule with Monitors](https://www.newscatcherapi.com/docs/web-search-api/concepts/monitors) · [Docs](https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart) · [Book a demo](https://www.newscatcherapi.com/book-a-demo) · Questions? support@newscatcherapi.com
```
<!-- FOOTER-DEFAULT:END -->

**Watchlist runs only** — insert the Company Watchlists link in second
position (omit it on every other run):

<!-- FOOTER-WATCHLIST:BEGIN — generated from links.json by scripts/render-links.py; do not edit by hand -->
```
---
## More with CatchAll
[Run this on a schedule with Monitors](https://www.newscatcherapi.com/docs/web-search-api/concepts/monitors) · [Learn about Company Watchlists](https://www.newscatcherapi.com/docs/web-search-api/concepts/company-search) · [Docs](https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart) · [Book a demo](https://www.newscatcherapi.com/book-a-demo) · Questions? support@newscatcherapi.com
```
<!-- FOOTER-WATCHLIST:END -->

Rules:

- **Copy the heading + line character-for-character.** Never compose your
  own footer, reword the links, or describe next steps in your own prose —
  if this file isn't in front of you when you write the footer, read it
  again first.
- **Heading** `## More with CatchAll` — exactly those three words, as an H2.
- **`·` separator** between links, one space on each side.
- **Always render it**, every run, as the last line.
- **Markdown links** for the URLs (real external links — clickable in
  Claude Code, Cursor, claude.ai). The support email is **plain text**
  (`Questions? support@newscatcherapi.com`) — no `mailto:`, no link wrapper;
  chat renderers strip email links anyway.
- Do not add links beyond these — extra links make it feel promotional.

## The links

| Link | For |
|---|---|
| Run this on a schedule with Monitors | Turn this one-off run into a recurring Monitor with webhook delivery |
| Learn about Company Watchlists | Scope future runs to a saved list of companies (watchlist runs only) |
| Docs | CatchAll Quickstart — API reference, integrations, troubleshooting |
| Book a demo | Talk to a human at NewsCatcher |
| Questions? support@newscatcherapi.com | Direct support contact (plain text) |

## URL stability

Every URL lives in `references/links.json` — the single source. If a URL
moves, edit it there and re-hydrate; it propagates to this footer, to the
xlsx builders (`build_downloads.py`, `render.py`), and to the report skills'
Overview footer. Never hardcode a URL in `SKILL.md` or a script.
