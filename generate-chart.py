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

# 颜色主题：亮色 + 暗色，分别生成两个 SVG 文件

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

footer_y = height - 6

# 主题配置
THEMES = {
    "light": {
        "bg_fill": "#ffffff", "bg_stroke": "#e1e4e8", "label": "#767676",
        "colors": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
    "dark": {
        "bg_fill": "#0d1117", "bg_stroke": "#30363d", "label": "#8b949e",
        "colors": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
}

for theme_name, t in THEMES.items():
    footer = f'<text x="{PADDING_LEFT}" y="{footer_y}" font-size="10" fill="{t["label"]}" font-family="sans-serif">{total} contributions in the last year</text>'
    m_svgs = [f'<text x="{PADDING_LEFT + wi * STEP}" y="{PADDING_TOP - 6}" font-size="10" fill="{t["label"]}" font-family="sans-serif">{label}</text>' for wi, label in month_labels]
    w_svgs = [f'<text x="0" y="{PADDING_TOP + idx * STEP + CELL - 1}" font-size="9" fill="{t["label"]}" font-family="sans-serif">{label}</text>' for label, idx in zip(week_days, week_day_indices)]
    c_svgs = []
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
            color = t["colors"][level]
            title = f"{cnt} contributions on {day['date']}"
            c_svgs.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"><title>{title}</title></rect>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="{width}" height="{height}" rx="6" fill="{t['bg_fill']}" stroke="{t['bg_stroke']}" stroke-width="1"/>
  {''.join(m_svgs)}
  {''.join(w_svgs)}
  {''.join(c_svgs)}
  {footer}
</svg>"""

    filename = "contributions.svg" if theme_name == "light" else "contributions-dark.svg"
    with open(filename, "w") as f:
        f.write(svg)

print(f"Done! Total contributions: {total}")
