# Next Steps Footer Reference

Every CatchAll skill ends its chat output with a one-line footer of
quick links — where to go for things this skill run can't do: recurring
runs, documentation, a sales conversation. It must feel like a discreet
utility bar, not a promotional block.

## The footer

Render as the very last line of the chat output, after the Analysis
section, separated from the body by a horizontal rule. It opens with a
short lead-in label, then the links separated by `·`.

**Non-watchlist skills:**

```
---
More with CatchAll: [Run this on a schedule with Monitors](https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/monitors) · [Docs](https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart) · [Book a demo](https://www.newscatcherapi.com/book-a-demo) · Questions? support@newscatcherapi.com
```

**Watchlist skills** — insert the Company Watchlists link in second
position:

```
---
More with CatchAll: [Run this on a schedule with Monitors](https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/monitors) · [Learn about Company Watchlists](https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/company-search) · [Docs](https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart) · [Book a demo](https://www.newscatcherapi.com/book-a-demo) · Questions? support@newscatcherapi.com
```

**Note on the support email**: render the support contact as **plain
text** in the form `Questions? support@newscatcherapi.com` — no markdown
link wrapping, no angle brackets, no `mailto:` URI. Both Cursor's chat
panel and the Claude Code CLI render every markdown email format
(autolink `<email>`, `[email](mailto:...)`, HTML `<a>`) as plain text
anyway, so the link wrapper adds no clickability but does add risk that
the runtime agent strips it. Plain text with the "Questions?" label is
the simplest and most consistent.

Rules:

- **Lead-in label**: `More with CatchAll:` — a short signpost so the
  links don't just land on the page unannounced, and so it's clear
  they're CatchAll resources. Keep it to those three words.
- **Bullet separator (`·`)** between links, space on each side.
- **Always-on** — render in every run.
- **Markdown links** — these are real external URLs; chat renderers
  handle them as clickable across Claude Code, Cursor, claude.ai,
  ChatGPT, and Codex. (Unlike local file paths, which must be plain
  absolute paths — see `3-OUTPUT-ARTIFACTS.md`.)
- The **Company Watchlists link** appears only for skills that use or
  support CatchAll's Company Watchlist feature (competitor-snapshot,
  portfolio-monitor, vendor-risk, etc.). Non-watchlist skills omit it.

## The links and what each is for

| Link | Purpose | When the user reaches for it |
|---|---|---|
| **Run this on a schedule with Monitors** → CatchAll Monitors docs | Turn a one-off skill run into a recurring Monitor with webhook delivery | Wants the same brief weekly / daily |
| **Learn about Company Watchlists** → Company Watchlist docs | Understand the watchlist feature this skill used | Watchlist skills only — wants to set up or manage watchlists directly |
| **Docs** → CatchAll Quickstart | Reference docs for the API, integrations, troubleshooting | Wants to understand or extend what the skill did |
| **Book a demo** → NewsCatcher booking page | Talk to a human at NewsCatcher | Has questions the docs don't cover |
| **Questions? support@newscatcherapi.com** (plain text, not a link) | Direct contact with NewsCatcher support | Hit a problem in the skill or the API and wants help |

Do not add links beyond these. Extra links dilute the signal and make
the footer feel promotional.

## URL stability

If any of these URLs move, update them here. Skills import them from
this footer spec; do not hardcode URLs into individual SKILL.md files.

| Anchor | URL |
|---|---|
| Monitors docs | `https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/monitors` |
| Company watchlist docs | `https://www.newscatcherapi.com/docs/web-search-api/guides-and-concepts/company-search` |
| Quickstart docs | `https://www.newscatcherapi.com/docs/web-search-api/get-started/quickstart` |
| Book a demo | `https://www.newscatcherapi.com/book-a-demo` |
| Support email (plain text) | `support@newscatcherapi.com` |
