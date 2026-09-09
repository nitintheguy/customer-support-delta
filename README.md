# Delta Support Agent: Hiver SDE Intern Take-Home

An AI support agent for Delta Air Lines' Twitter customer support, built on the
[Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
dataset. The agent:

1. Classifies incoming customer messages into intents derived from the data.
2. Drafts replies grounded in how Delta has historically resolved similar issues.
3. Decides whether a message should be auto-handled or escalated to a human, with a stated reason.

## Repo structure

```
├── data/              # raw & filtered data (gitignored — see "Reproducing the data" below)
├── scripts/
│   └── filter_delta.py    # filters twcs.csv down to full Delta conversation threads
├── src/
│   ├── classify.py         # intent classification
│   ├── retrieve.py         # find similar historical resolutions
│   ├── draft_reply.py      # grounded reply generation
│   └── escalate.py         # auto-handle vs. escalate decision
├── eval/
│   ├── golden_set.jsonl    # 150–250 hand-labeled examples
│   ├── judge.py            # LLM-as-judge harness
│   └── metrics.py          # automated metrics
├── report/
│   └── report.md           # problem framing, results, failure analysis
└── decision_log.md         # non-obvious decisions and why
```

## Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Add your LLM API key to a `.env` file (not committed):
```
ANTHROPIC_API_KEY=your_key_here
```

## Reproducing the data

The raw dataset is not committed to this repo (too large). To regenerate it:

1. Download `twcs.csv` from [Kaggle](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
   and place it in `data/`.
2. Run:
   ```bash
   python scripts/filter_delta.py data/twcs.csv data/delta_threads.csv
   ```
   This filters the ~3M-row dataset down to full conversation threads involving `@Delta`.

## Reproducing headline results

*(TODO: fill in once pipeline is built — should take under 15 minutes end-to-end)*

```bash
python src/run_pipeline.py --input data/delta_threads.csv --output outputs/results.jsonl
python eval/judge.py --predictions outputs/results.jsonl --golden eval/golden_set.jsonl
```

## Evaluation

- **Golden set**: `eval/golden_set.jsonl` — hand-labeled examples with intent, reference resolution
  approach, and escalate/auto-handle decision + reason. See `report/report.md` for sampling methodology.
- **Metrics**: automated classification metrics + LLM-as-judge scoring for reply quality, validated
  against human agreement (see report).

## Report

See `report/report.md` for problem framing, baselines, failure analysis, and next steps.

## Decision log

See `decision_log.md` for a running list of non-obvious decisions made during development.