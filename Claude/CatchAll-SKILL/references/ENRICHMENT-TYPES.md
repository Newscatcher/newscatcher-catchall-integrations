# Enrichment Types Reference

Enrichments are custom fields that the CatchAll system extracts from each
validated article. When submitting a job, each enrichment requires three fields:

```json
{
  "name": "deal_value",
  "description": "Estimated deal value in USD",
  "type": "number"
}
```

## Available types

| Type | Returns | Best for | Example |
|---|---|---|---|
| `text` | Free-form string | Summaries, names, descriptions | `"strategic_rationale"`: why a deal happened |
| `number` | Numeric value | Quantities, percentages, scores | `"deal_value"`: deal amount in USD |
| `date` | ISO 8601 date string | Event dates, deadlines | `"deal_date"`: when the deal was announced |
| `option` | One value from a set | Categories, statuses | `"deal_type"`: acquisition, merger, licensing |
| `url` | Valid URL | Source links, related pages | `"filing_url"`: link to the SEC filing |
| `company` | Company name string | Entity extraction | `"acquiring_company"`: name of the acquirer |

## Guidelines for writing enrichment descriptions

The `description` field is critical — it tells the AI what to extract. Good
descriptions are specific and unambiguous.

**Good descriptions:**

- `"Estimated total deal value in USD, including cash and stock components"`
- `"Name of the company being acquired or merged"`
- `"Current regulatory approval status (e.g. pending, approved, blocked)"`

**Poor descriptions:**

- `"Value"` — too vague, could mean anything
- `"Company"` — which company? There are always at least two in M&A
- `"Status"` — status of what?

## Real-world enrichment sets

### M&A tracking

```json
[
  { "name": "acquiring_company", "description": "Name of the acquiring company", "type": "company" },
  { "name": "acquired_company", "description": "Name of the company being acquired", "type": "company" },
  { "name": "deal_value", "description": "Estimated deal value in USD", "type": "number" },
  { "name": "deal_type", "description": "Type of deal: acquisition, merger, licensing, or asset purchase", "type": "option" },
  { "name": "deal_date", "description": "Date the deal was announced", "type": "date" },
  { "name": "deal_status", "description": "Current status: announced, pending, completed, or blocked", "type": "option" },
  { "name": "regulatory_status", "description": "Regulatory approval status and relevant bodies", "type": "text" },
  { "name": "strategic_rationale", "description": "Why the acquiring company is pursuing this deal", "type": "text" }
]
```

### Funding rounds

```json
[
  { "name": "company_name", "description": "Name of the company that raised funding", "type": "company" },
  { "name": "round_type", "description": "Funding round type: seed, Series A, Series B, etc.", "type": "option" },
  { "name": "amount_raised", "description": "Total amount raised in USD", "type": "number" },
  { "name": "lead_investor", "description": "Name of the lead investor", "type": "company" },
  { "name": "valuation", "description": "Post-money valuation in USD if disclosed", "type": "number" },
  { "name": "funding_date", "description": "Date the funding was announced", "type": "date" }
]
```

### Product launches

```json
[
  { "name": "company_name", "description": "Company launching the product", "type": "company" },
  { "name": "product_name", "description": "Name of the product being launched", "type": "text" },
  { "name": "launch_date", "description": "Announced or actual launch date", "type": "date" },
  { "name": "target_market", "description": "Geographic or demographic target market", "type": "text" },
  { "name": "product_category", "description": "Product category or industry vertical", "type": "option" }
]
```

## Confidence field

Every enrichment result includes an automatic `confidence` field (`"high"`,
`"medium"`, or `"low"`) indicating how reliably the value was extracted from the
source articles. This is not something you define — the system adds it.