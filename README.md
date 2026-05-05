# Ops Dashboard

A lightweight Python operations dashboard for tracking project delivery, scoring risk, and visualising team metrics. Built for programme managers and ops leads who want a fast, no-nonsense view of what's on track and what isn't.

## Features
- Project health scoring (RAG status — Red / Amber / Green)
- Risk matrix with weighted scoring
- Delivery metrics: on-time rate, budget variance, dependency count
- CSV import/export
- CLI and web dashboard (Flask)

## Stack
Python · Pandas · Flask · Plotly · CSV

## Quickstart
```bash
pip install -r requirements.txt
python src/dashboard.py --projects data/projects.csv
```

## Screenshot
```
┌─────────────────────────────────────────────────┐
│  OPS DASHBOARD                   Projects: 8    │
├────────────────┬────────┬────────┬──────────────┤
│ Project        │ Status │ Risk   │ On-Time Rate │
├────────────────┼────────┼────────┼──────────────┤
│ IAM Migration  │  🟢    │  Low   │    94%       │
│ CRM Rollout    │  🟡    │  Med   │    78%       │
│ Portal Launch  │  🔴    │  High  │    52%       │
└────────────────┴────────┴────────┴──────────────┘
```
