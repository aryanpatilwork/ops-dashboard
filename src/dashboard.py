"""
dashboard.py
Ops Dashboard — Project Health & Risk Scoring Engine

Loads project data from CSV, computes RAG status and risk scores,
and outputs a formatted CLI summary. Optionally launches a Flask
web dashboard with Plotly charts.

Author: Aryan Patil

Usage:
    python src/dashboard.py --projects data/projects.csv
    python src/dashboard.py --projects data/projects.csv --web
"""

import argparse
import csv
import os
from datetime import datetime, date


# ── Data Loading ──────────────────────────────────────────────────────────────

def load_projects(csv_path: str) -> list:
    """
    Loads project records from a CSV file into a list of dictionaries.
    Expected columns: name, owner, start_date, end_date, budget, spent,
                      milestones_total, milestones_complete, risks, dependencies.

    @param  csv_path    str     Path to the projects CSV file
    @return list                List of project dicts; empty list if file not found
    """
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return []

    projects = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects.append(row)
    print(f"Loaded {len(projects)} projects from {csv_path}")
    return projects


# ── Scoring ───────────────────────────────────────────────────────────────────

def compute_on_time_rate(project: dict) -> float:
    """
    Computes the milestone completion rate as a percentage.
    Used as a proxy for on-time delivery performance.

    @param  project     dict    Project record with 'milestones_total' and
                                'milestones_complete' fields (as strings)
    @return float               Completion rate between 0.0 and 100.0;
                                returns 0.0 if milestones_total is zero or missing
    """
    try:
        total    = int(project.get("milestones_total", 0))
        complete = int(project.get("milestones_complete", 0))
        if total == 0:
            return 0.0
        return round((complete / total) * 100, 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def compute_budget_variance(project: dict) -> float:
    """
    Computes budget variance as a percentage of total budget.
    Positive variance = underspend. Negative variance = overspend.

    @param  project     dict    Project record with 'budget' and 'spent' fields (as strings)
    @return float               Budget variance percentage, e.g. -12.5 means 12.5% over budget;
                                returns 0.0 if budget is zero or fields are missing/invalid
    """
    try:
        budget = float(project.get("budget", 0))
        spent  = float(project.get("spent", 0))
        if budget == 0:
            return 0.0
        return round(((budget - spent) / budget) * 100, 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def compute_risk_score(project: dict) -> int:
    """
    Computes a weighted risk score (0–100) based on schedule health,
    budget variance, dependency count, and open risk count.
    Higher scores indicate higher risk.

    Scoring weights:
      - Schedule (on-time rate below 70%): +40 points
      - Budget variance below -10%:        +30 points
      - Dependencies >= 5:                 +20 points
      - Open risks >= 3:                   +10 points

    @param  project     dict    Project record with delivery metrics
    @return int                 Risk score between 0 and 100
    """
    score = 0

    on_time = compute_on_time_rate(project)
    if on_time < 70:
        score += 40
    elif on_time < 85:
        score += 20

    budget_var = compute_budget_variance(project)
    if budget_var < -10:
        score += 30
    elif budget_var < 0:
        score += 15

    try:
        deps = int(project.get("dependencies", 0))
        if deps >= 5:
            score += 20
        elif deps >= 2:
            score += 10
    except ValueError:
        pass

    try:
        risks = int(project.get("risks", 0))
        if risks >= 3:
            score += 10
        elif risks >= 1:
            score += 5
    except ValueError:
        pass

    return min(score, 100)


def compute_rag_status(risk_score: int, on_time_rate: float) -> str:
    """
    Derives a RAG (Red / Amber / Green) status from the risk score
    and on-time delivery rate.

    RAG logic:
      GREEN  — risk score < 30 and on-time rate >= 85%
      AMBER  — risk score 30–59, or on-time rate 70–84%
      RED    — risk score >= 60, or on-time rate < 70%

    @param  risk_score      int     Computed risk score (0–100)
    @param  on_time_rate    float   Milestone completion rate (0.0–100.0)
    @return str                     One of: "GREEN", "AMBER", "RED"
    """
    if risk_score >= 60 or on_time_rate < 70:
        return "RED"
    elif risk_score >= 30 or on_time_rate < 85:
        return "AMBER"
    else:
        return "GREEN"


def enrich_projects(projects: list) -> list:
    """
    Runs all scoring functions against each project and attaches
    computed fields: on_time_rate, budget_variance, risk_score, rag_status.

    @param  projects    list    Raw project dicts loaded from CSV
    @return list                Same list with computed fields added to each dict
    """
    for p in projects:
        p["on_time_rate"]    = compute_on_time_rate(p)
        p["budget_variance"] = compute_budget_variance(p)
        p["risk_score"]      = compute_risk_score(p)
        p["rag_status"]      = compute_rag_status(p["risk_score"], p["on_time_rate"])
    return projects


# ── CLI Output ────────────────────────────────────────────────────────────────

def rag_icon(status: str) -> str:
    """
    Returns a coloured circle emoji for a RAG status string.

    @param  status  str     One of: "GREEN", "AMBER", "RED"
    @return str             Emoji icon: 🟢, 🟡, or 🔴
    """
    return {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}.get(status, "⚪")


def print_dashboard(projects: list) -> None:
    """
    Renders the project dashboard as a formatted CLI table.
    Sorts projects by risk score descending (highest risk first).

    @param  projects    list    Enriched project dicts with computed metrics
    @return None                Prints directly to stdout
    """
    projects = sorted(projects, key=lambda p: p["risk_score"], reverse=True)

    red   = sum(1 for p in projects if p["rag_status"] == "RED")
    amber = sum(1 for p in projects if p["rag_status"] == "AMBER")
    green = sum(1 for p in projects if p["rag_status"] == "GREEN")

    print("\n" + "═" * 75)
    print(f"  OPS DASHBOARD  |  {datetime.now().strftime('%d %b %Y %H:%M')}  |  Projects: {len(projects)}")
    print(f"  🔴 Red: {red}   🟡 Amber: {amber}   🟢 Green: {green}")
    print("═" * 75)
    print(f"{'Project':<22} {'Owner':<15} {'Status':<8} {'Risk':>5} {'On-Time':>8} {'Budget Var':>11}")
    print("─" * 75)

    for p in projects:
        icon   = rag_icon(p["rag_status"])
        name   = p.get("name", "Unknown")[:21]
        owner  = p.get("owner", "—")[:14]
        risk   = p["risk_score"]
        ot     = p["on_time_rate"]
        bv     = p["budget_variance"]
        bv_str = f"{'+' if bv >= 0 else ''}{bv}%"
        print(f"{name:<22} {owner:<15} {icon:<8} {risk:>5} {ot:>7}%  {bv_str:>10}")

    print("─" * 75)
    print(f"  Tip: Projects sorted by risk score. Address 🔴 RED items first.")
    print("═" * 75 + "\n")


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ops Dashboard — Project Health & Risk Scoring")
    parser.add_argument("--projects", required=True, help="Path to projects CSV file")
    parser.add_argument("--web",      action="store_true", help="Launch web dashboard")
    args = parser.parse_args()

    projects = load_projects(args.projects)
    if not projects:
        print("No projects loaded. Check your CSV path and format.")
        return

    projects = enrich_projects(projects)
    print_dashboard(projects)


if __name__ == "__main__":
    main()
