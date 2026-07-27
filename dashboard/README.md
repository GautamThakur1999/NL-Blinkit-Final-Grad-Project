# Category Discovery Insights — Dashboard

Static visualisation of the Part 1 discovery-engine output.

## Why it is static

The page reads a pre-generated `dashboard.json`. There is no server, no API key
and no LLM call at view time, so nothing can rate-limit, cold-start or fall over
while it is being graded.

## Files

| File | Purpose |
|---|---|
| `index.html` | The dashboard (self-contained: no external CSS/JS/fonts) |
| `dashboard.json` | Build artifact produced by the pipeline |

## Regenerating the data

```bash
python -m pipeline.validation.dashboard_data
cp data/analysis/dashboard.json dashboard/dashboard.json
```

## Local preview

```bash
python -m http.server 4173 --directory dashboard
```

Then open <http://localhost:4173>.

## Deploying (Vercel)

Deploy this directory as a **static** project — framework preset "Other", no
build command, output directory `dashboard`. No environment variables are
required.

## What the dashboard deliberately shows

It reports its own limitations next to its findings, because hiding them would
misrepresent the research:

- the sample size against the population, with the random seed
- pre-registered hypotheses that found **zero** evidence, drawn as hatched
  zero-length bars rather than omitted
- weak-signal themes (below the ≥3-item / ≥2-source triangulation bar), labelled
  rather than promoted or dropped
- null findings — research questions the data could not answer
- the traceability audit result, including how many quotes lacked a source URL
