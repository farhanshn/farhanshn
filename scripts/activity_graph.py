#!/usr/bin/env python3
"""Generates an animated contribution graph SVG (last 30 days) for a GitHub profile README."""
import datetime as dt
import json
import os
import random
import urllib.request

USER = os.environ.get("GH_USER", "farhanshn")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT", "dist/activity-graph.svg")
DAYS = 30

W, H = 1000, 340
L, R, T, B = 60, 30, 70, 55  # margins
CYAN = "#00d1ff"


def fetch_counts():
    today = dt.date.today()
    start = today - dt.timedelta(days=DAYS - 1)
    query = """query($login:String!,$from:DateTime!,$to:DateTime!){
      user(login:$login){contributionsCollection(from:$from,to:$to){
        contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    variables = {
        "login": USER,
        "from": f"{start}T00:00:00Z",
        "to": f"{today}T23:59:59Z",
    }
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    by_date = {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}
    days = [start + dt.timedelta(days=i) for i in range(DAYS)]
    return [(d, by_date.get(d.isoformat(), 0)) for d in days]


def demo_counts():
    sample = [0, 3, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 4, 0, 2, 1,
              0, 0, 0, 0, 0, 0, 0, 7, 6, 0]
    today = dt.date.today()
    return [(today - dt.timedelta(days=DAYS - 1 - i), c) for i, c in enumerate(sample)]


def smooth_path(pts):
    """Catmull-Rom -> cubic bezier, clamped so the curve never dips below the baseline."""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        base = H - B
        c1 = (c1[0], min(c1[1], base))
        c2 = (c2[0], min(c2[1], base))
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def build(counts):
    random.seed(7)
    n = len(counts)
    peak = max(max(c for _, c in counts), 4)
    ymax = peak + (peak % 2)  # even top value
    pw, ph = W - L - R, H - T - B
    xs = [L + pw * i / (n - 1) for i in range(n)]
    ys = [T + ph * (1 - c / ymax) for _, c in counts]
    pts = list(zip(xs, ys))
    line = smooth_path(pts)
    area = f"{line} L{xs[-1]:.1f},{H - B} L{xs[0]:.1f},{H - B} Z"
    dur = 9  # seconds for the ball to cross the graph

    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Animated contribution graph">')
    a(f'''<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#0a1a24"/>
  </linearGradient>
  <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{CYAN}" stop-opacity="0.35"/>
    <stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>
    <stop offset="0.5" stop-color="{CYAN}" stop-opacity="0.10"/>
    <stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="ball">
    <stop offset="0" stop-color="#ffffff"/><stop offset="0.45" stop-color="#9ff0ff"/>
    <stop offset="1" stop-color="{CYAN}"/>
  </radialGradient>
  <filter id="glow" x="-200%" y="-200%" width="500%" height="500%">
    <feGaussianBlur stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="plot"><rect x="{L}" y="{T - 10}" width="{pw}" height="{ph + 20}"/></clipPath>
</defs>''')
    a(f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>')

    # moving light sweep across the whole card
    a(f'<rect x="-300" y="0" width="300" height="{H}" fill="url(#sweep)">'
      f'<animate attributeName="x" from="-300" to="{W}" dur="7s" repeatCount="indefinite"/></rect>')

    # floating background particles
    for _ in range(38):
        x = random.uniform(10, W - 10)
        y = random.uniform(T - 20, H - 10)
        r = random.uniform(1, 3.2)
        t = random.uniform(5, 12)
        dy = random.uniform(30, 90)
        dx = random.uniform(-25, 25)
        begin = -random.uniform(0, t)
        op = random.uniform(0.25, 0.7)
        a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{CYAN}" opacity="0">'
          f'<animate attributeName="cy" values="{y:.1f};{y - dy:.1f}" dur="{t:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
          f'<animate attributeName="cx" values="{x:.1f};{x + dx:.1f};{x:.1f}" dur="{t:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0;{op:.2f};0" dur="{t:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/></circle>')

    # title
    a(f'<text x="{W / 2}" y="34" text-anchor="middle" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="18" font-weight="600" fill="{CYAN}">Farhan Shayan\'s Contribution Graph</text>')

    # grid + y labels
    for v in range(0, ymax + 1, max(1, ymax // 7 or 1)):
        y = T + ph * (1 - v / ymax)
        a(f'<line x1="{L}" y1="{y:.1f}" x2="{W - R}" y2="{y:.1f}" stroke="{CYAN}" stroke-opacity="0.12" stroke-dasharray="3 4"/>')
        a(f'<text x="{L - 12}" y="{y + 4:.1f}" text-anchor="end" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="600" fill="{CYAN}">{v}</text>')
    for i, (d, _) in enumerate(counts):
        a(f'<line x1="{xs[i]:.1f}" y1="{T}" x2="{xs[i]:.1f}" y2="{H - B}" stroke="{CYAN}" stroke-opacity="0.07" stroke-dasharray="2 5"/>')
        a(f'<text x="{xs[i]:.1f}" y="{H - B + 18}" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="600" fill="{CYAN}">{d.day}</text>')
    a(f'<text x="{W / 2}" y="{H - 10}" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="600" fill="{CYAN}">Days</text>')
    a(f'<text transform="translate(18 {T + ph / 2}) rotate(-90)" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="600" fill="{CYAN}">Contributions</text>')

    # area + line
    a('<g clip-path="url(#plot)">')
    a(f'<path d="{area}" fill="url(#fill)"/>')
    a(f'<path id="curve" d="{line}" fill="none" stroke="{CYAN}" stroke-width="3" stroke-linecap="round" filter="url(#glow)"/>')
    a(f'<path d="{line}" fill="none" stroke="#ffffff" stroke-opacity="0.75" stroke-width="1.5" stroke-linecap="round" '
      f'stroke-dasharray="6 60"><animate attributeName="stroke-dashoffset" from="0" to="-132" dur="2.4s" repeatCount="indefinite"/></path>')
    a('</g>')

    # data points (a ring pulses as the ball passes)
    for i, (x, y) in enumerate(pts):
        a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#ffffff"/>')
        begin = dur * i / (n - 1)
        a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="none" stroke="{CYAN}" stroke-width="2" opacity="0">'
          f'<animate attributeName="r" values="4;14;14" keyTimes="0;0.12;1" dur="{dur}s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0.9;0;0" keyTimes="0;0.12;1" dur="{dur}s" begin="{begin:.2f}s" repeatCount="indefinite"/></circle>')

    # the moving ball with a fading trail
    for k, (rad, op, lag) in enumerate([(3, 0.25, 0.30), (4.5, 0.45, 0.20), (6, 0.7, 0.10)]):
        a(f'<circle r="{rad}" fill="{CYAN}" opacity="{op}"><animateMotion dur="{dur}s" begin="-{lag}s" repeatCount="indefinite" rotate="auto">'
          f'<mpath xlink:href="#curve"/></animateMotion></circle>')
    a(f'<circle r="9" fill="url(#ball)" filter="url(#glow)"><animateMotion dur="{dur}s" repeatCount="indefinite">'
      f'<mpath xlink:href="#curve"/></animateMotion></circle>')

    a('</svg>')
    return "\n".join(o)


def main():
    try:
        if not TOKEN:
            raise RuntimeError("no token")
        counts = fetch_counts()
    except Exception as e:  # keep the workflow green, fall back to demo data
        print("Using demo data:", e)
        counts = demo_counts()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build(counts))
    print("written", OUT)


if __name__ == "__main__":
    main()
