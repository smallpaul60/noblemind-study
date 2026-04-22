#!/usr/bin/env python3
"""Scaffold three additional Test-This-Claim pages from the infant-baptism
template. The generated pages carry a noindex meta until Paul approves and
populates the doctrinal content.

Usage: python3 scaffold_ttc_pages.py
"""
import re
from pathlib import Path
from urllib.parse import quote

TTC_DIR = Path('/home/smallpaul/noblemind-study/test-this-claim')
TEMPLATE = TTC_DIR / 'infant-baptism-in-the-new-testament.html'

# Each page: (slug, question, short_description_for_meta,
#             claim_for_study_tool_preload, candidate_passages_note,
#             related: list of (slug, title))
PAGES = [
    (
        'baptism-sprinkling-pouring-or-immersion',
        'What does the Bible say about baptism — sprinkling, pouring, or immersion?',
        'An honest look at the mode of baptism in the New Testament — using the Noble Mind Study method.',
        'Sprinkling or pouring is a valid mode of New Testament baptism.',
        'Rom. 6:3–4; Col. 2:12; Acts 8:36–39; Matt. 3:13–17; John 3:23; the meaning of the Greek word baptizō.',
        [
            ('infant-baptism-in-the-new-testament.html', 'Is infant baptism in the New Testament?'),
            ('inherited-guilt-and-original-sin.html', 'Does the Bible teach inherited guilt (so-called "original sin")?'),
            ('is-the-sinners-prayer-in-the-bible.html', 'Is the "sinner\'s prayer" in the Bible?'),
        ],
    ),
    (
        'inherited-guilt-and-original-sin',
        'Does the Bible teach inherited guilt (so-called "original sin")?',
        'An honest look at whether Scripture teaches that guilt is passed from Adam to every person — using the Noble Mind Study method.',
        'Guilt is inherited from Adam — every person is born guilty of original sin.',
        'Ezek. 18:20; Deut. 24:16; Rom. 5:12; Ps. 51:5; Matt. 19:14; the distinction between inherited consequence and inherited guilt.',
        [
            ('infant-baptism-in-the-new-testament.html', 'Is infant baptism in the New Testament?'),
            ('baptism-sprinkling-pouring-or-immersion.html', 'What does the Bible say about baptism — sprinkling, pouring, or immersion?'),
            ('is-the-sinners-prayer-in-the-bible.html', 'Is the "sinner\'s prayer" in the Bible?'),
        ],
    ),
    (
        'is-the-sinners-prayer-in-the-bible',
        'Is the "sinner\'s prayer" in the Bible?',
        'An honest look at whether the New Testament records the "sinner\'s prayer" as a response to the gospel — using the Noble Mind Study method.',
        'Salvation comes by praying the sinner\'s prayer.',
        'Acts 2:37–38; Acts 8:35–38; Acts 16:30–33; Acts 22:16; Rom. 10:9–10, 13; what the NT records as the response to every gospel call.',
        [
            ('infant-baptism-in-the-new-testament.html', 'Is infant baptism in the New Testament?'),
            ('baptism-sprinkling-pouring-or-immersion.html', 'What does the Bible say about baptism — sprinkling, pouring, or immersion?'),
            ('inherited-guilt-and-original-sin.html', 'Does the Bible teach inherited guilt (so-called "original sin")?'),
        ],
    ),
    (
        'what-does-saint-mean-in-the-new-testament',
        'What does "saint" mean in the New Testament?',
        'An honest look at how the New Testament actually uses the word "saint" — using the Noble Mind Study method.',
        'A saint is a canonized deceased believer specially recognized by the church.',
        'Rom. 1:7; 1 Cor. 1:2; Eph. 1:1; Phil. 1:1; Col. 1:2; the NT\'s distributive use of "saints" for all Christians vs. post-apostolic canonization.',
        [
            ('infant-baptism-in-the-new-testament.html', 'Is infant baptism in the New Testament?'),
            ('is-the-sinners-prayer-in-the-bible.html', 'Is the "sinner\'s prayer" in the Bible?'),
            ('does-the-new-testament-authorize-instrumental-music.html', 'Does the New Testament authorize instrumental music in worship?'),
        ],
    ),
    (
        'does-the-new-testament-authorize-instrumental-music',
        'Does the New Testament authorize instrumental music in worship?',
        'An honest look at what the New Testament says — and does not say — about instruments in Christian worship. Using the Noble Mind Study method.',
        'The New Testament authorizes instrumental music in worship.',
        'Eph. 5:19; Col. 3:16; Heb. 13:15; 1 Cor. 14:15; Matt. 26:30 (hymn after Passover); the NT pattern of singing and the absence of any reference to instruments in corporate worship; later church practice is post-apostolic.',
        [
            ('baptism-sprinkling-pouring-or-immersion.html', 'What does the Bible say about baptism — sprinkling, pouring, or immersion?'),
            ('what-does-saint-mean-in-the-new-testament.html', 'What does "saint" mean in the New Testament?'),
            ('infant-baptism-in-the-new-testament.html', 'Is infant baptism in the New Testament?'),
        ],
    ),
]

template = TEMPLATE.read_text(encoding='utf-8')

def build_page(slug, question, description, claim, candidates_note, related):
    out = template

    # --- 1. <title>
    out = re.sub(
        r'<title>[^<]*</title>',
        f'<title>{question} &mdash; Noble Mind Study</title>',
        out, count=1
    )

    # --- 2. meta description
    out = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{description}">',
        out, count=1
    )

    # --- 3. canonical
    out = re.sub(
        r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="https://noblemind.study/test-this-claim/{slug}.html">',
        out, count=1
    )

    # --- 4. Inject noindex robots meta right after the canonical link.
    #    Removed once the page's doctrinal content is approved.
    noindex = ('\n  <!-- TODO(content): remove this noindex once section 2-6 '
               'doctrinal content is approved and populated. -->\n'
               '  <meta name="robots" content="noindex, nofollow">')
    out = out.replace(
        f'<link rel="canonical" href="https://noblemind.study/test-this-claim/{slug}.html">',
        f'<link rel="canonical" href="https://noblemind.study/test-this-claim/{slug}.html">{noindex}',
        1
    )

    # --- 5. OG / Twitter: title, description, url
    out = re.sub(
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{question}">',
        out, count=1
    )
    out = re.sub(
        r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="{description}">',
        out, count=1
    )
    out = re.sub(
        r'<meta property="og:url" content="[^"]*">',
        f'<meta property="og:url" content="https://noblemind.study/test-this-claim/{slug}.html">',
        out, count=1
    )
    out = re.sub(
        r'<meta name="twitter:title" content="[^"]*">',
        f'<meta name="twitter:title" content="{question}">',
        out, count=1
    )
    out = re.sub(
        r'<meta name="twitter:description" content="[^"]*">',
        f'<meta name="twitter:description" content="{description}">',
        out, count=1
    )

    # --- 6. JSON-LD: update Question.name / .text / acceptedAnswer.url,
    #    set acceptedAnswer.text to TODO.
    jsonld_pat = re.compile(
        r'("name":\s*)"[^"]*"(.*?"text":\s*)"[^"]*"(.*?"acceptedAnswer":\s*\{[^}]*"text":\s*)"[^"]*"(.*?"url":\s*)"[^"]*"',
        re.DOTALL
    )
    out = jsonld_pat.sub(
        lambda m: (
            f'{m.group(1)}"{question.replace(chr(34), chr(92) + chr(34))}"'
            f'{m.group(2)}"{question.replace(chr(34), chr(92) + chr(34))}"'
            f'{m.group(3)}"TODO: one-sentence answer — awaiting content approval."'
            f'{m.group(4)}"https://noblemind.study/test-this-claim/{slug}.html"'
        ),
        out, count=1
    )

    # --- 7. H1 headline
    out = re.sub(
        r'<h1>[^<]*</h1>',
        f'<h1>{question}</h1>',
        out, count=1
    )

    # --- 8. Section 2 — reset to TODO placeholder
    section2_new = (
        '<p class="lead-answer">\n'
        '        <em style="color: var(--text-muted);">One-sentence answer coming soon &mdash; awaiting content approval. See <a href="../principles.html">the principles</a> for the method, and use the <strong>Berean Prompt</strong> below to examine this yourself.</em>\n'
        '      </p>'
    )
    out = re.sub(
        r'<p class="lead-answer">.*?</p>',
        section2_new,
        out, count=1, flags=re.DOTALL
    )

    # --- 9. Sections 3-6: reset to TODO cards by rebuilding the whole block
    #    from the <!-- 3. --> comment through the end of the </div> after section 6.
    sections_3_to_6_new = f'''<!-- 3. What does the text actually say? -->
      <h2>What does the text actually say?</h2>
      <div class="section-card todo">
        <p class="todo-note">
          <strong>TODO (content):</strong> Quote the direct NASB passages that bear on this question. Render inline within running prose, with citations in the form <em>(Book Ch:vv, NASB)</em>. Candidate passages: {candidates_note} Awaiting Paul's approval.
        </p>
      </div>

      <!-- 4. The Three Questions -->
      <h2>The Three Questions</h2>
      <div class="section-card todo">
        <p class="todo-note">
          <strong>TODO (content):</strong> Brief pass through <em>Who is speaking? To whom? Under what circumstances?</em> for each passage above. Keep it tight &mdash; context shapes meaning. Awaiting Paul's approval.
        </p>
      </div>

      <!-- 5. Cross-references -->
      <h2>Cross-references</h2>
      <div class="section-card todo">
        <p class="todo-note">
          <strong>TODO (content):</strong> Other Scriptures on the same subject, each cited as <em>Book Ch:vv (NASB)</em>. Let clear passages illuminate difficult ones. Awaiting Paul's approval.
        </p>
      </div>

      <!-- 6. Conclusion -->
      <h2>Conclusion</h2>
      <div class="section-card todo">
        <p class="todo-note">
          <strong>TODO (content):</strong> What the text establishes, what it does not address, and what is inference vs. explicit statement. Use the &ldquo;text explicitly states&rdquo; / &ldquo;text necessarily implies&rdquo; distinction from the principles. Awaiting Paul's approval.
        </p>
      </div>'''

    # Match from the <!-- 3. --> comment through the closing </div> of section 6,
    # immediately before <!-- 7. Examine this yourself -->.
    out = re.sub(
        r'<!-- 3\. What does the text actually say\? -->.*?(?=<!-- 7\. Examine this yourself -->)',
        sections_3_to_6_new + '\n\n      ',
        out, count=1, flags=re.DOTALL
    )

    # --- 10. Section 7: update the ?claim= preload with this page's claim
    claim_enc = quote(claim, safe='')
    # Also pick a reasonable passage-preload starter — use the first passage from candidates_note
    first_passage_match = re.match(r'[^;]*', candidates_note)
    first_passage = first_passage_match.group(0).strip().rstrip(';').strip()
    passage_enc = quote(first_passage, safe='')

    # Replace the two Audit / Passage links in section 7 with new ones
    out = re.sub(
        r'<a href="\.\./Noble_Mind_Study_Tool_v2\.html\?claim=[^"]*">📋 Audit this claim in the study tool</a>[^<]*',
        f'<a href="../Noble_Mind_Study_Tool_v2.html?claim={claim_enc}">📋 Audit this claim in the study tool</a> &mdash; opens the study tool with the Berean Claim Audit prompt preloaded, ready to copy into any AI chat.',
        out, count=1
    )
    out = re.sub(
        r'<a href="\.\./Noble_Mind_Study_Tool_v2\.html\?passage=[^"]*">✝️ Open [^<]*</a>[^<]*',
        f'<a href="../Noble_Mind_Study_Tool_v2.html?passage={passage_enc}">✝️ Open {first_passage} in the study tool</a> &mdash; a concrete starting point.',
        out, count=1
    )

    # --- 11. Section 8: rebuild related-studies list from the provided tuples
    rel_items = '\n'.join(
        f'          <li><a href="{rel_slug}">{rel_title}</a></li>'
        for rel_slug, rel_title in related
    )
    new_rel_block = f'''<div class="related-studies">
        <ul>
{rel_items}
        </ul>
        <p class="note"><em>Some of these companion studies are forthcoming &mdash; links may 404 until each is published.</em></p>
      </div>'''
    out = re.sub(
        r'<div class="related-studies">.*?</div>',
        new_rel_block,
        out, count=1, flags=re.DOTALL
    )

    return out


for slug, question, description, claim, candidates_note, related in PAGES:
    out_path = TTC_DIR / f'{slug}.html'
    out_path.write_text(
        build_page(slug, question, description, claim, candidates_note, related),
        encoding='utf-8'
    )
    print(f'Wrote {out_path.relative_to(TTC_DIR.parent)} ({out_path.stat().st_size:,} bytes)')
