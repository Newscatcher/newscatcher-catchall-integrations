# Next Steps Footer Reference

End every chat output with the **More with CatchAll** footer — a heading
plus one line of quick links, a discreet utility bar, not a promo block.
Render it **last**, after the results, separated from the body by a
horizontal rule.

## The footer (render verbatim)

```
---
## More with CatchAll
[Run this on a schedule with Monitors](https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/monitors) · [Docs](https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart) · [Book a demo](https://www.newscatcherapi.com/book-a-demo) · Questions? support@newscatcherapi.com
```

**Watchlist runs only** — insert the Company Watchlists link in second
position (omit it on every other run):

```
---
## More with CatchAll
[Run this on a schedule with Monitors](https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/monitors) · [Learn about Company Watchlists](https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/company-search) · [Docs](https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart) · [Book a demo](https://www.newscatcherapi.com/book-a-demo) · Questions? support@newscatcherapi.com
```

Rules:

- **Copy the heading + line character-for-character.** Never compose your
  own footer, reword the links, or describe next steps in your own prose —
  if this file isn't in front of you when you write the footer, read it
  again first.
- **Heading** `## More with CatchAll` — exactly those three words, as an H2.
- **`·` separator** between links, one space on each side.
- **Always render it**, every run, as the last line.
- **Markdown links** for the three URLs (real external links — clickable in
  Claude Code, Cursor, claude.ai). The support email is **plain text**
  (`Questions? support@newscatcherapi.com`) — no `mailto:`, no link wrapper;
  chat renderers strip email links anyway.
- Do not add links beyond these four — extra links make it feel promotional.

## The links

| Link | For |
|---|---|
| Run this on a schedule with Monitors | Turn this one-off run into a recurring Monitor with webhook delivery |
| Docs | CatchAll Quickstart — API reference, integrations, troubleshooting |
| Book a demo | Talk to a human at NewsCatcher |
| Questions? support@newscatcherapi.com | Direct support contact (plain text) |

## URL stability

If a URL moves, update it here; do not hardcode URLs into `SKILL.md`.

| Anchor | URL |
|---|---|
| Monitors docs | `https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/monitors` |
| Company Watchlists docs (watchlist runs) | `https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/company-search` |
| Quickstart docs | `https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart` |
| Book a demo | `https://www.newscatcherapi.com/book-a-demo` |
| Support email (plain text) | `support@newscatcherapi.com` |
