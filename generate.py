import google.generativeai as genai
import pandas as pd
import os

API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

df = pd.read_csv("topics.csv")
os.makedirs("pages", exist_ok=True)

for _, row in df.iterrows():
    category = row["category"]
    relation = row["relation"]
    tone     = row["tone"]
    keyword  = row["keyword"]

    prompt = f"""
You are an expert content writer for a greeting card website.
Write for the keyword: "{keyword}"

1. SEO Intro (50-60 words): warm, helpful. No "I" or "we".
2. 15 {tone} {category} wishes for {relation}: numbered, max 15 words each, no repetition.

Format EXACTLY like this:
INTRO:
[intro here]

WISHES:
1. [wish]
2. [wish]
...
15. [wish]
"""

    print(f"Generating: {keyword}...")
    response = model.generate_content(prompt)
    content  = response.text

    intro  = ""
    wishes = ""

    if "INTRO:" in content and "WISHES:" in content:
        parts      = content.split("WISHES:")
        intro      = parts[0].replace("INTRO:", "").strip()
        wish_lines = parts[1].strip().split("\n")
        wish_items = "".join(
            f"<li>{line.split('. ', 1)[-1].strip()}</li>\n"
            for line in wish_lines if line.strip()
        )
        wishes = f"<ol>{wish_items}</ol>"
    else:
        wishes = f"<pre>{content}</pre>"

    filename = f"{category}-{relation}.html".replace(" ", "-")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{keyword.title()}</title>
    <meta name="description" content="Find the best {keyword} — heartfelt, unique, and ready to share.">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; color: #333; }}
        h1   {{ color: #2c3e50; }}
        ol   {{ line-height: 2; }}
        li   {{ margin-bottom: 8px; }}
        .card-box {{ background: #f0f4ff; padding: 20px; border-radius: 8px; margin-top: 40px; }}
    </style>
</head>
<body>
    <h1>{keyword.title()}</h1>
    <p>{intro}</p>
    <h2>Top 15 {keyword.title()}</h2>
    {wishes}
    <div class="card-box">
        <h2>Send a Free Card</h2>
        <p>Make it extra special — send one of these wishes with a beautiful card!</p>
        <a href="https://www.123greetings.com" target="_blank">Browse Cards on 123Greetings</a>
    </div>
</body>
</html>"""

    with open(f"pages/{filename}", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Saved: pages/{filename}")

# Auto-generate index.html
links = ""
for _, row in pd.read_csv("topics.csv").iterrows():
    fname = f"{row['category']}-{row['relation']}.html".replace(" ", "-")
    links += f'<li><a href="pages/{fname}">{row["keyword"].title()}</a></li>\n'

with open("index.html", "w") as f:
    f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Wishes & Greetings</title>
    <style>body{{font-family:Arial,sans-serif;max-width:600px;margin:40px auto;padding:0 20px}}</style>
</head>
<body>
    <h1>Wishes & Greetings</h1>
    <ul>{links}</ul>
</body>
</html>""")

print("Done! All pages + index.html generated.")