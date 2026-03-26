import requests
import os
import json
from datetime import datetime, timedelta, timezone

USERNAME = os.environ["GH_USERNAME"]
TOKEN = os.environ["GH_TOKEN"]

# 查询过去一年的贡献数据
query = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            weekday
          }
        }
      }
    }
  }
}
"""

now = datetime.now(timezone.utc)
one_year_ago = now - timedelta(days=365)

variables = {
    "username": USERNAME,
    "from": one_year_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
}

resp = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": variables},
    headers={"Authorization": f"Bearer {TOKEN}"},
)
data = resp.json()
calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]
total = calendar["totalContributions"]

# SVG 参数
CELL = 11
GAP = 3
STEP = CELL + GAP
PADDING_LEFT = 28
PADDING_TOP = 30
PADDING_BOTTOM = 24
PADDING_RIGHT = 14

# 颜色主题通过 CSS 类 + prefers-color-scheme 媒体查询实现
# 亮色: #ebedf0, #9be9a8, #40c463, #30a14e, #216e39
# 暗色: #161b22, #0e4429, #006d32, #26a641, #39d353

num_weeks = len(weeks)
width = PADDING_LEFT + num_weeks * STEP + PADDING_RIGHT
height = PADDING_TOP + 7 * STEP - GAP + PADDING_BOTTOM

# 月份标签
month_labels = []
last_month = None
for wi, week in enumerate(weeks):
    for day in week["contributionDays"]:
        month = datetime.strptime(day["date"], "%Y-%m-%d").strftime("%b")
        if month != last_month:
            if wi > 0:
                month_labels.append((wi, month))
            last_month = month

# 星期标签
week_days = ["Mon", "Wed", "Fri"]
week_day_indices = [1, 3, 5]

cells = []
for wi, week in enumerate(weeks):
    for day in week["contributionDays"]:
        x = PADDING_LEFT + wi * STEP
        y = PADDING_TOP + day["weekday"] * STEP
        cnt = day["contributionCount"]
        if cnt == 0: level = 0
        elif cnt <= 3: level = 1
        elif cnt <= 6: level = 2
        elif cnt <= 9: level = 3
        else: level = 4
        title = f"{cnt} contributions on {day['date']}"
        cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" class="c{level}"><title>{title}</title></rect>')

month_svgs = []
for wi, label in month_labels:
    x = PADDING_LEFT + wi * STEP
    month_svgs.append(f'<text x="{x}" y="{PADDING_TOP - 6}" font-size="10" class="label" font-family="sans-serif">{label}</text>')

weekday_svgs = []
for label, idx in zip(week_days, week_day_indices):
    y = PADDING_TOP + idx * STEP + CELL - 1
    weekday_svgs.append(f'<text x="0" y="{y}" font-size="9" class="label" font-family="sans-serif">{label}</text>')

footer_y = height - 6
footer = f'<text x="{PADDING_LEFT}" y="{footer_y}" font-size="10" class="label" font-family="sans-serif">{total} contributions in the last year</text>'

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <style>
    .bg {{ fill: #ffffff; stroke: #e1e4e8; }}
    .label {{ fill: #767676; }}
    .c0 {{ fill: #ebedf0; }}
    .c1 {{ fill: #9be9a8; }}
    .c2 {{ fill: #40c463; }}
    .c3 {{ fill: #30a14e; }}
    .c4 {{ fill: #216e39; }}
    @media (prefers-color-scheme: dark) {{
      .bg {{ fill: #0d1117; stroke: #30363d; }}
      .label {{ fill: #8b949e; }}
      .c0 {{ fill: #161b22; }}
      .c1 {{ fill: #0e4429; }}
      .c2 {{ fill: #006d32; }}
      .c3 {{ fill: #26a641; }}
      .c4 {{ fill: #39d353; }}
    }}
  </style>
  <rect width="{width}" height="{height}" rx="6" class="bg" stroke-width="1"/>
  {''.join(month_svgs)}
  {''.join(weekday_svgs)}
  {''.join(cells)}
  {footer}
</svg>"""

with open("contributions.svg", "w") as f:
    f.write(svg)

print(f"Done! Total contributions: {total}")
