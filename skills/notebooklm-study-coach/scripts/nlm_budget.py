"""Read-only budget check: estimated cost of a plan vs. remaining NotebookLM usage.

Usage:
  python3 -I nlm_budget.py                              # just show current usage
  python3 -I nlm_budget.py --pack standard --topics 3   # price a plan before any manifest exists
  python3 -I nlm_budget.py --manifest m.json [m2.json]  # price the pending work in one or more manifests
  python3 -I nlm_budget.py --questions 8 --reports 1 --slides 1
Chat questions are priced from measurement, not from the service's estimate (see MEASURED).
Packs (per topic):  lite     = 8 questions, mind map, plain guide, quiz, flashcards
                    standard = lite + comparison table + one infographic
                    full     = standard + one short slide deck
The cost estimates NotebookLM reports are a share of its "active window", which is the five-hour window.
The week is far larger: measured on 2026-11-17, four visuals moved the five-hour window by 3.80% and the
week by 0.18%, about a twentieth. WEEK_SHARE holds that ratio; it is one measurement, so treat the weekly
figure as rough.
Exit code: 0 PASS, 1 WARN, 2 STOP, 3 could not read usage.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _nlm import items, load_manifest, run  # noqa: E402

KIND = {  # manifest artifact kind -> usage action kind
    "study-guide": "reports", "briefing-doc": "reports", "blog-post": "reports", "custom-report": "reports",
    "quiz": "quiz", "flashcards": "flashcards", "mind-map": "mindmap", "data-table": "tables",
    "infographic": "infographic", "slide-deck": "slides", "slides": "slides",
    "audio": "audio_overview", "video": "video_overview",
}
FALLBACK = {"qna": 0.05, "reports": 1.39, "quiz": 0.67, "flashcards": 0.55, "mindmap": 0.13, "tables": 1.26,
            "infographic": 2.03, "slides": 11.65, "audio_overview": 9.73, "video_overview": 10.34,
            "slides_editing": 0.89}
# The service's own estimate for a chat question (0.05%) is wrong. Eight questions measured on 2026-11-17
# averaged 1.9% of a five-hour window (1.3% to 2.6%): one across a 29-source notebook, seven in a two-book one,
# so notebook size is not what drives it. A measured figure is used whenever it is higher than the service's.
MEASURED = {"qna": 2.0}
WEEK_SHARE = 0.05  # one five-hour window is about 1/20 of the week (single measurement, see above)
LITE = {"qna": 8, "mindmap": 1, "reports": 1, "quiz": 1, "flashcards": 1}
PACKS = {"lite": LITE, "standard": {**LITE, "tables": 1, "infographic": 1},
         "full": {**LITE, "tables": 1, "infographic": 1, "slides": 1}}
FLAGS = {"questions": "qna", "reports": "reports", "quiz": "quiz", "flashcards": "flashcards", "mindmap": "mindmap",
         "tables": "tables", "infographics": "infographic", "slides": "slides", "audio": "audio_overview",
         "video": "video_overview", "slide-fixes": "slides_editing"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", nargs="*", default=[])
    ap.add_argument("--pack", choices=sorted(PACKS))
    ap.add_argument("--topics", type=int, default=1, help="how many topics get the pack")
    for flag in FLAGS:
        ap.add_argument(f"--{flag}", type=int, default=0)
    ap.add_argument("--weekly-max", type=float, default=60)
    ap.add_argument("--five-hour-max", type=float, default=80)
    a = ap.parse_args()

    j, r = run(["usage", "--categories"], timeout=120)
    if not isinstance(j, dict) or "windows" not in j:
        print(f"Could not read usage: {r.stderr[-300:]}")
        sys.exit(3)
    win = {w["kind"]: w for w in items(j, "windows")}
    cost = dict(FALLBACK)
    cost.update({x["kind"]: x["estimated_cost_percent"] for x in items(j, "actions") if x.get("kind")})
    quoted = dict(cost)
    for k, v in MEASURED.items():
        cost[k] = max(cost.get(k, 0), v)

    plan = {k: getattr(a, flag.replace("-", "_")) for flag, k in FLAGS.items()}
    for k, n in PACKS.get(a.pack, {}).items():
        plan[k] += n * a.topics
    weekly_max, five_max = a.weekly_max, a.five_hour_max
    for mp in a.manifest:
        m = load_manifest(mp)
        plan["qna"] += sum(1 for q in m.get("questions", []) if q.get("status") != "done")
        for art in m.get("artifacts", []):
            if art.get("status") != "done":
                k = KIND.get(art.get("kind"), "reports")
                plan[k] = plan.get(k, 0) + 1
        b = m.get("budget", {})
        weekly_max = min(weekly_max, b.get("weekly_max_used", weekly_max))
        five_max = min(five_max, b.get("five_hour_max_used", five_max))

    est = sum(cost.get(k, 0) * n for k, n in plan.items())
    active = j.get("active_window") or "five_hour"  # the window the estimates are a share of
    est_fh, est_wk = (est, est * WEEK_SHARE) if active == "five_hour" else (est / WEEK_SHARE, est)
    wk, fh = win.get("weekly", {}), win.get("five_hour", {})
    wk_used, fh_used = wk.get("used_percent", 0), fh.get("used_percent", 0)
    print(f"Weekly used    {wk_used:6.2f}%  (resets {str(wk.get('resets_at', '?'))[:16]})")
    print(f"Five-hour used {fh_used:6.2f}%  (resets {str(fh.get('resets_at', '?'))[:16]})")
    if a.pack:
        print(f"Per topic, with the eight loop questions ({active.replace('_', '-')} window):  " + "  ".join(f"{name} {sum(cost.get(k, 0) * n for k, n in p.items()):.1f}%"
                                          for name, p in PACKS.items()))
    if est:
        print("Plan: " + ", ".join(f"{n}× {k} ({cost.get(k, 0):.2f}%)" for k, n in plan.items() if n))
        for k, n in plan.items():
            if n and cost.get(k, 0) > quoted.get(k, 0):
                print(f"  {k} is priced at the measured {cost[k]:.2f}% each; the service quotes {quoted.get(k, 0):.2f}%.")
        big = [f"{n}× {k}" for k, n in plan.items() if n and cost.get(k, 0) >= 5]
        if big:
            print(f"Costly items in this plan: {', '.join(big)}. Make sure the user asked for them.")
        print(f"Estimated cost: {est_fh:.2f}% of a five-hour window, roughly {est_wk:.2f}% of the week")
        print(f"After this plan: five-hour {fh_used + est_fh:.1f}% / limit {five_max}%, "
              f"weekly about {wk_used + est_wk:.1f}% / limit {weekly_max}%")
    if j.get("is_exhausted"):
        print("STOP: usage is exhausted right now."); sys.exit(2)
    if wk_used + est_wk > weekly_max or fh_used + est_fh > five_max:
        print("STOP: this plan would exceed the budget limits. Spread it over more than one five-hour window "
              "(--later, or fewer topics now), or use a smaller pack.")
        sys.exit(2)
    if wk_used + est_wk > weekly_max - 10 or fh_used + est_fh > five_max - 10:
        print("WARN: close to a limit. Consider --later for reports and visuals, or a smaller pack.")
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
