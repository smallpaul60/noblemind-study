# NobleMind.Study Weekly Report — Week of [DATE]

*Fill in the bracketed fields. "Give me the weekly report" is meant to be a
one-shot command Paul runs — paste Search Console exports and the
noblemind-console dashboard numbers below, and Claude Code fills in the
analysis at the bottom.*

---

## Inputs (what Paul pastes in)

### Google Search Console — Performance tab, last 7 days
*Paste the summary numbers and top-query / top-page tables from the Performance tab.*

- Total impressions (last 7d): **[N]**
- Total clicks (last 7d): **[N]**
- Average CTR: **[N]%**
- Average position: **[N]**

**Top 10 queries by impressions** (paste table):
```
[query]                  [impressions]  [clicks]  [CTR]  [position]
...
```

**Top 5 queries by clicks** (paste table):
```
[query]                  [impressions]  [clicks]  [CTR]  [position]
...
```

**Top 5 pages by impressions** (paste table):
```
[page]                                            [impressions]  [clicks]
...
```

### Search Console — Coverage / Pages tab
*Paste only if anything changed from last week.*

- Indexed pages: **[N]** (prior week: [N])
- Not indexed (any new entries?): **[list slugs or "none"]**
- Any validation errors? **[yes/no — paste details if yes]**

### noblemind-console (self-hosted analytics at /console)
*Paste the week's summary from the dashboard.*

- Total pageviews: **[N]**
- Unique-visitor estimate (hashed IPs): **[N]**
- Top 5 pages by pageview: **[list]**
- PWA installs: **[N]**
- File downloads (PDFs, EPUBs): **[N]**
- Median time on page (any TTC page): **[N]s**

### Compared to last week
*Paste the prior week's numbers here so the analysis can compute deltas.*

- Last week impressions: **[N]**
- Last week clicks: **[N]**
- Last week pageviews: **[N]**

---

## Site health (Claude Code fills this in)

- [ ] Any 4xx or 5xx errors in nginx logs this week?
- [ ] Any pages dropped from /sitemap.xml?
- [ ] Any Lighthouse regression on the landing page or the 6 TTC pages?
- [ ] Any new pages that haven't been added to the sitemap's expected set?
- [ ] Any IPNS-publish failures in the last 7 days?

---

## Analysis (Claude Code fills this in)

### Trend
- **Impressions:** [up/down] [N]% vs. prior week
- **Clicks:** [up/down] [N]% vs. prior week
- **CTR:** [up/down] [N] pp vs. prior week

### New queries this week
*Queries that appear this week but were not in last week's top list.
These are leading indicators of what seekers are starting to find.*

- [query]
- [query]

### What's working
*Pages or queries outperforming the site baseline. Why might they be working?*

- [observation]

### What's not working
*Pages with high impressions but low CTR (title or description may not be
pulling the click), or pages that should be ranking for specific queries
but aren't appearing.*

- [observation]

### Recommendations for next week
*Specific, actionable. If there's nothing substantive, say so — do not
manufacture work.*

- [action item]
- [action item]

---

*Template established as part of the post-deploy 30-day plan. When the
pattern settles and the Search Console API is wired up, the Inputs section
can be replaced with an automated fetch. For the first few months,
copy-paste is fine.*
