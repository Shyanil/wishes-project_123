from groq import Groq
import pandas as pd
import os
import time
import re

API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=API_KEY)

df = pd.read_csv("topics.csv")
os.makedirs("pages", exist_ok=True)

# Track stats
skipped  = 0
generated = 0

for _, row in df.iterrows():
    category = row["category"]
    relation = row["relation"]
    tone     = row["tone"]
    keyword  = row["keyword"]

    filename = f"{category}-{relation}.html".replace(" ", "-")

    # ── SKIP IF ALREADY GENERATED ──
    if os.path.exists(f"pages/{filename}"):
        print(f"  ⏭  Skipping (already exists): {filename}")
        skipped += 1
        continue

    prompt = f"""
You are an expert SEO content writer for a popular greeting card website.
Write for the keyword: "{keyword}"

1. SEO Intro (60-80 words): warm, engaging, keyword-rich. Mention the occasion, the relationship, and the emotional value. No "I" or "we". Use words like "perfect", "heartfelt", "meaningful", "celebrate", "special".

2. A short "Why These Wishes Work" paragraph (40-50 words): explain what makes a great {category} message for a {relation}. No "I" or "we".

3. 15 {tone} {category} wishes for {relation}: numbered, max 20 words each, emotionally rich, no repetition, varied sentence structures.

4. A short "Tips for Sending" paragraph (40-50 words): practical advice on when/how to send these wishes. No "I" or "we".

Format EXACTLY like this:
INTRO:
[intro here]

WHY:
[why paragraph here]

WISHES:
1. [wish]
2. [wish]
...
15. [wish]

TIPS:
[tips paragraph here]
"""

    max_retries = 5
    retry_delay = 10
    content = ""

    for attempt in range(max_retries):
        try:
            print(f"Generating: {keyword} (Attempt {attempt + 1})...")
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.8
            )
            content = response.choices[0].message.content
            print(f"  Success!")
            break

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate_limit" in err_str.lower():
                match = re.search(r'try again in (\d+\.?\d*)s', err_str)
                wait = float(match.group(1)) + 2 if match else retry_delay
                print(f"  Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)
                retry_delay *= 2
            else:
                print(f"  Error: {e}")
                content = "ERROR: Could not generate content."
                break

    if not content:
        content = "ERROR: All retries failed."

    time.sleep(2)

    # Parse response
    intro  = ""
    why    = ""
    wishes = ""
    tips   = ""

    def extract_section(text, start_tag, end_tags):
        if start_tag not in text:
            return ""
        part = text.split(start_tag, 1)[1]
        for tag in end_tags:
            if tag in part:
                part = part.split(tag, 1)[0]
        return part.strip()

    intro  = extract_section(content, "INTRO:",  ["WHY:", "WISHES:", "TIPS:"])
    why    = extract_section(content, "WHY:",    ["WISHES:", "TIPS:"])
    tips   = extract_section(content, "TIPS:",   [])

    if "WISHES:" in content:
        wish_block = extract_section(content, "WISHES:", ["TIPS:"])
        wish_lines = wish_block.strip().split("\n")
        wish_items = ""
        for line in wish_lines:
            line = line.strip()
            if not line:
                continue
            text = line.split('. ', 1)[-1].strip()
            wish_items += f"""
                <li class="wish-item">
                    <span class="wish-icon">✦</span>
                    <span class="wish-text">{text}</span>
                    <button class="copy-btn" onclick="copyWish(this)" title="Copy wish">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                    </button>
                </li>"""
        wishes = f'<ol class="wishes-list">{wish_items}</ol>'
    else:
        wishes = f'<div class="error-box"><pre>{content}</pre></div>'

    # Generate breadcrumb-friendly title parts
    category_title = category.title()
    relation_title = relation.title()
    keyword_title  = keyword.title()
    
    # Word count estimate for schema
    word_count = len(intro.split()) + len(why.split()) + len(tips.split()) + (15 * 15)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{keyword_title} — Heartfelt & Unique Messages (2025)</title>
    <meta name="description" content="Discover 15 {tone} {keyword} that truly connect. Perfect heartfelt messages for your {relation} — copy, share, or send with a free greeting card today.">
    <meta name="keywords" content="{keyword}, {category} wishes for {relation}, {tone} {category} messages, best {keyword}, {relation} {category} quotes 2025">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="./{filename}">

    <!-- Open Graph -->
    <meta property="og:title" content="{keyword_title} — 15 Heartfelt Messages">
    <meta property="og:description" content="Find the perfect {keyword} — warm, unique, and ready to share. Browse 15 handpicked wishes.">
    <meta property="og:type" content="article">

    <!-- Schema.org Article -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{keyword_title}",
      "description": "15 {tone} {category} wishes for {relation} — heartfelt, unique, and ready to share.",
      "wordCount": {word_count},
      "keywords": "{keyword}, {category} wishes, {relation} messages",
      "publisher": {{
        "@type": "Organization",
        "name": "Wishes & Greetings"
      }}
    }}
    </script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Lora:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">

    <style>
        :root {{
            --cream:   #fdf8f3;
            --warm:    #f5ede0;
            --rose:    #c9605a;
            --rose-lt: #f0d4d2;
            --ink:     #2b1f1a;
            --ink-mid: #5c4a42;
            --ink-lt:  #9c8880;
            --gold:    #c8a96e;
            --gold-lt: #f5ecd8;
            --white:   #ffffff;
            --shadow:  rgba(43,31,26,0.10);
        }}

        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        html {{ scroll-behavior: smooth; }}

        body {{
            font-family: 'DM Sans', sans-serif;
            background: var(--cream);
            color: var(--ink);
            line-height: 1.7;
            font-size: 16px;
        }}

        /* ── TOP NAV ── */
        .topnav {{
            background: var(--white);
            border-bottom: 1px solid var(--warm);
            padding: 14px 24px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--ink-lt);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 12px var(--shadow);
        }}
        .topnav a {{ color: var(--rose); text-decoration: none; font-weight: 500; }}
        .topnav a:hover {{ text-decoration: underline; }}
        .topnav .sep {{ color: var(--ink-lt); }}
        .site-logo {{
            font-family: 'Playfair Display', serif;
            font-size: 18px;
            font-weight: 900;
            color: var(--ink);
            text-decoration: none !important;
            margin-right: auto;
        }}

        /* ── HERO ── */
        .hero {{
            background: linear-gradient(135deg, #2b1f1a 0%, #4a2e26 50%, #6b3a30 100%);
            color: var(--white);
            padding: 72px 24px 60px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            inset: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c9605a' fill-opacity='0.08'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.4;
        }}
        .hero-badge {{
            display: inline-block;
            background: var(--rose);
            color: var(--white);
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 2px;
            text-transform: uppercase;
            padding: 6px 16px;
            border-radius: 100px;
            margin-bottom: 20px;
        }}
        .hero h1 {{
            font-family: 'Playfair Display', serif;
            font-size: clamp(28px, 5vw, 52px);
            font-weight: 900;
            line-height: 1.15;
            margin-bottom: 16px;
            position: relative;
        }}
        .hero-sub {{
            font-size: 17px;
            color: rgba(255,255,255,0.75);
            max-width: 520px;
            margin: 0 auto 28px;
            font-family: 'Lora', serif;
            font-style: italic;
        }}
        .hero-stats {{
            display: flex;
            justify-content: center;
            gap: 32px;
            flex-wrap: wrap;
        }}
        .hero-stat {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
        }}
        .hero-stat strong {{
            font-size: 22px;
            font-weight: 700;
            color: var(--gold);
        }}
        .hero-stat span {{
            font-size: 12px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* ── LAYOUT ── */
        .container {{
            max-width: 780px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        /* ── ARTICLE BODY ── */
        .article-body {{
            padding: 56px 0 80px;
        }}

        /* ── SECTIONS ── */
        .section {{
            background: var(--white);
            border-radius: 16px;
            padding: 36px 40px;
            margin-bottom: 28px;
            box-shadow: 0 4px 24px var(--shadow);
            border: 1px solid rgba(201,96,90,0.08);
            animation: fadeUp 0.5s ease both;
        }}

        @keyframes fadeUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}

        .section:nth-child(2) {{ animation-delay: 0.1s; }}
        .section:nth-child(3) {{ animation-delay: 0.2s; }}
        .section:nth-child(4) {{ animation-delay: 0.3s; }}

        .section-label {{
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            color: var(--rose);
            margin-bottom: 10px;
        }}

        .section h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 26px;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 16px;
            line-height: 1.3;
        }}

        .section p {{
            font-family: 'Lora', serif;
            color: var(--ink-mid);
            font-size: 16px;
            line-height: 1.8;
        }}

        /* ── DIVIDER ── */
        .divider {{
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, var(--rose-lt), transparent);
            margin: 24px 0;
        }}

        /* ── WISHES LIST ── */
        .wishes-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 12px;
            counter-reset: wish-counter;
        }}

        .wish-item {{
            display: flex;
            align-items: flex-start;
            gap: 14px;
            background: var(--cream);
            border: 1px solid var(--warm);
            border-radius: 12px;
            padding: 16px 20px;
            transition: all 0.2s ease;
            counter-increment: wish-counter;
            position: relative;
        }}

        .wish-item:hover {{
            border-color: var(--rose);
            background: var(--gold-lt);
            transform: translateX(4px);
            box-shadow: 0 4px 16px var(--shadow);
        }}

        .wish-item::before {{
            content: counter(wish-counter);
            font-family: 'Playfair Display', serif;
            font-size: 13px;
            font-weight: 700;
            color: var(--rose);
            background: var(--rose-lt);
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            margin-top: 1px;
        }}

        .wish-icon {{ display: none; }}

        .wish-text {{
            font-family: 'Lora', serif;
            font-size: 15.5px;
            color: var(--ink);
            line-height: 1.6;
            flex: 1;
        }}

        .copy-btn {{
            background: none;
            border: 1px solid var(--warm);
            border-radius: 8px;
            padding: 6px 8px;
            cursor: pointer;
            color: var(--ink-lt);
            flex-shrink: 0;
            transition: all 0.2s;
            display: flex;
            align-items: center;
        }}
        .copy-btn:hover {{ background: var(--rose); color: white; border-color: var(--rose); }}
        .copy-btn.copied {{ background: #4caf50; color: white; border-color: #4caf50; }}

        /* ── CTA CARD ── */
        .cta-card {{
            background: linear-gradient(135deg, #2b1f1a, #6b3a30);
            border-radius: 20px;
            padding: 44px 40px;
            text-align: center;
            color: var(--white);
            margin-bottom: 28px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(43,31,26,0.25);
        }}
        .cta-card::before {{
            content: '💌';
            font-size: 64px;
            display: block;
            margin-bottom: 16px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        }}
        .cta-card h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 12px;
        }}
        .cta-card p {{
            color: rgba(255,255,255,0.75);
            font-family: 'Lora', serif;
            font-style: italic;
            margin-bottom: 28px;
            font-size: 16px;
        }}
        .cta-btn {{
            display: inline-block;
            background: var(--rose);
            color: white;
            text-decoration: none;
            padding: 14px 36px;
            border-radius: 100px;
            font-weight: 600;
            font-size: 15px;
            letter-spacing: 0.5px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 16px rgba(201,96,90,0.4);
        }}
        .cta-btn:hover {{
            background: #b84e48;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(201,96,90,0.5);
        }}

        /* ── TIPS BOX ── */
        .tips-box {{
            border-left: 4px solid var(--gold);
            background: var(--gold-lt);
            border-radius: 0 12px 12px 0;
            padding: 20px 24px;
            margin-top: 8px;
        }}
        .tips-box p {{
            font-size: 15px;
            color: var(--ink-mid);
        }}

        /* ── FOOTER ── */
        .site-footer {{
            background: var(--ink);
            color: rgba(255,255,255,0.5);
            text-align: center;
            padding: 32px 20px;
            font-size: 13px;
        }}
        .site-footer a {{ color: var(--rose); text-decoration: none; }}

        /* ── TOAST ── */
        .toast {{
            position: fixed;
            bottom: 32px;
            left: 50%;
            transform: translateX(-50%) translateY(80px);
            background: var(--ink);
            color: white;
            padding: 12px 24px;
            border-radius: 100px;
            font-size: 14px;
            font-weight: 500;
            transition: transform 0.3s ease;
            z-index: 999;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }}
        .toast.show {{ transform: translateX(-50%) translateY(0); }}

        /* ── RESPONSIVE ── */
        @media (max-width: 600px) {{
            .section {{ padding: 24px 20px; }}
            .cta-card {{ padding: 32px 20px; }}
            .hero {{ padding: 48px 20px 40px; }}
            .hero-stats {{ gap: 20px; }}
        }}
    </style>
</head>
<body>

<!-- NAV -->
<nav class="topnav">
    <a href="../index.html" class="site-logo">✦ WishesHub</a>
    <a href="../index.html">Home</a>
    <span class="sep">›</span>
    <span>{category_title}</span>
    <span class="sep">›</span>
    <span>{relation_title}</span>
</nav>

<!-- HERO -->
<header class="hero">
    <div class="hero-badge">{tone.title()} {category_title}</div>
    <h1>{keyword_title}</h1>
    <p class="hero-sub">Heartfelt messages your {relation} will truly cherish</p>
    <div class="hero-stats">
        <div class="hero-stat"><strong>15</strong><span>Wishes</span></div>
        <div class="hero-stat"><strong>100%</strong><span>Free</span></div>
        <div class="hero-stat"><strong>2025</strong><span>Updated</span></div>
    </div>
</header>

<!-- ARTICLE -->
<main class="container article-body">

    <!-- INTRO -->
    <section class="section" itemscope itemtype="https://schema.org/Article">
        <div class="section-label">About This Collection</div>
        <h2>The Perfect {keyword_title}</h2>
        <p itemprop="description">{intro}</p>
    </section>

    <!-- WHY IT WORKS -->
    {f'''<section class="section">
        <div class="section-label">Expert Insight</div>
        <h2>What Makes a Great {category_title} Message?</h2>
        <p>{why}</p>
    </section>''' if why else ''}

    <!-- WISHES -->
    <section class="section">
        <div class="section-label">Hand-Picked Collection</div>
        <h2>15 Best {keyword_title}</h2>
        <p style="margin-bottom:24px; font-size:14px; color:var(--ink-lt);">Click the copy icon on any wish to grab it instantly.</p>
        {wishes}
    </section>

    <!-- TIPS -->
    {f'''<section class="section">
        <div class="section-label">Pro Tips</div>
        <h2>Tips for Sending These Wishes</h2>
        <div class="tips-box"><p>{tips}</p></div>
    </section>''' if tips else ''}

    <!-- CTA -->
    <div class="cta-card">
        <h2>Send a Free Greeting Card</h2>
        <p>Pair your perfect message with a beautiful card — free to send, forever to treasure.</p>
        <a href="https://www.123greetings.com" target="_blank" rel="noopener" class="cta-btn">
            Browse Free Cards →
        </a>
    </div>

</main>

<!-- FOOTER -->
<footer class="site-footer">
    <p>© 2025 WishesHub · <a href="../index.html">All Categories</a> · Made with ♥ for every occasion</p>
</footer>

<!-- TOAST -->
<div class="toast" id="toast">✓ Copied to clipboard!</div>

<script>
    function copyWish(btn) {{
        const text = btn.closest('.wish-item').querySelector('.wish-text').innerText;
        navigator.clipboard.writeText(text).then(() => {{
            btn.classList.add('copied');
            setTimeout(() => btn.classList.remove('copied'), 2000);
            const toast = document.getElementById('toast');
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2500);
        }});
    }}
</script>

</body>
</html>"""

    with open(f"pages/{filename}", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ Saved: pages/{filename}")
    generated += 1

# ── SUMMARY ──
print(f"\n📊 Summary: {generated} generated, {skipped} skipped (already existed)")

# ── INDEX PAGE ──
links = ""
for _, row in pd.read_csv("topics.csv").iterrows():
    fname    = f"{row['category']}-{row['relation']}.html".replace(" ", "-")
    keyword  = row["keyword"]
    category = row["category"]
    tone     = row["tone"]
    links += f"""
        <li class="card">
            <a href="pages/{fname}">
                <span class="card-tag">{tone.title()} · {category.title()}</span>
                <span class="card-title">{keyword.title()}</span>
                <span class="card-arrow">→</span>
            </a>
        </li>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WishesHub — Heartfelt Wishes & Greetings for Every Occasion</title>
    <meta name="description" content="Find the perfect words for every occasion. Browse heartfelt birthday, anniversary, and holiday wishes — curated, copy-ready, and completely free.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --cream: #fdf8f3; --warm: #f5ede0; --rose: #c9605a;
            --rose-lt: #f0d4d2; --ink: #2b1f1a; --ink-mid: #5c4a42;
            --ink-lt: #9c8880; --gold: #c8a96e; --gold-lt: #f5ecd8;
            --shadow: rgba(43,31,26,0.10);
        }}
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'DM Sans', sans-serif; background: var(--cream); color: var(--ink); }}

        header {{
            background: linear-gradient(135deg, #2b1f1a 0%, #6b3a30 100%);
            color: white;
            text-align: center;
            padding: 80px 20px 64px;
        }}
        header h1 {{
            font-family: 'Playfair Display', serif;
            font-size: clamp(32px, 6vw, 60px);
            font-weight: 900;
            margin-bottom: 14px;
        }}
        header p {{
            color: rgba(255,255,255,0.7);
            font-size: 17px;
            max-width: 480px;
            margin: 0 auto;
            line-height: 1.6;
        }}
        .logo-mark {{ font-size: 40px; margin-bottom: 16px; }}

        main {{ max-width: 820px; margin: 0 auto; padding: 56px 20px 80px; }}

        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 24px;
            color: var(--ink);
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--rose-lt);
        }}

        .card-grid {{ list-style: none; display: grid; gap: 14px; }}

        .card a {{
            display: flex;
            align-items: center;
            gap: 14px;
            background: white;
            border: 1px solid var(--warm);
            border-radius: 14px;
            padding: 20px 24px;
            text-decoration: none;
            color: var(--ink);
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px var(--shadow);
        }}
        .card a:hover {{
            border-color: var(--rose);
            background: var(--gold-lt);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px var(--shadow);
        }}
        .card-tag {{
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--rose);
            background: var(--rose-lt);
            padding: 4px 10px;
            border-radius: 100px;
            white-space: nowrap;
            flex-shrink: 0;
        }}
        .card-title {{
            flex: 1;
            font-size: 16px;
            font-weight: 500;
        }}
        .card-arrow {{ color: var(--ink-lt); font-size: 18px; }}

        footer {{
            background: var(--ink);
            color: rgba(255,255,255,0.5);
            text-align: center;
            padding: 28px 20px;
            font-size: 13px;
        }}
    </style>
</head>
<body>

<header>
    <div class="logo-mark">✦</div>
    <h1>WishesHub</h1>
    <p>Heartfelt wishes and greetings for every occasion — curated, copy-ready, and free.</p>
</header>

<main>
    <h2 class="section-title">Browse All Collections</h2>
    <ul class="card-grid">
        {links}
    </ul>
</main>

<footer>
    <p>© 2025 WishesHub · Made with ♥ for every occasion</p>
</footer>

</body>
</html>""")

print("✅ Done! index.html updated.")