#!/usr/bin/env python3
"""Generate a single Eloquenta B2 FCE Speaking deck HTML from a topic JSON."""
import json, re, os, argparse

BASE = r"C:\Users\irieb\Documents\William's Projects\workspace\esl-sites\eloquenta\b2-fce-speaking"

def load_template():
    with open(os.path.join(BASE, '_template.html'), encoding='utf-8') as f:
        return f.read()

def tooltipify(text, vocab):
    for word, definition in vocab.items():
        text = re.sub(
            r'(?i)\b(' + re.escape(word) + r')\b',
            lambda m: "<span class='tooltip' data-def='" + definition + "'>" + m.group(1) + "</span>",
            text
        )
    return text

def render_slide(title, body_html):
    return f'<section class="slide" data-slide="{{{{SLIDE_NUM}}}}">\n  <div class="card glass">\n    <div class="part-badge">{title}</div>\n    {body_html}\n  </div>\n</section>'

def build(data):
    template = load_template()
    slides = []
    vocab = data.get('vocab', {})

    # Part 1
    p1 = data['part1']
    body = '<h2 class="glow-text">Part 1 — Interview</h2>\n'
    body += '<p style="color:var(--cs-text-muted);font-size:.85rem;margin-bottom:14px">Answer these questions. Spend about 20 seconds on each.</p>\n'
    for i, q in enumerate(p1['questions']):
        body += f'<div class="question">• {tooltipify(q, vocab)}</div>\n'
        body += f'<button class="reveal-btn">Show answer</button>\n'
        body += f'<div class="hidden-answer">{tooltipify(p1["answers"][i], vocab)}</div>\n'
    if 'phrases' in data:
        body += '<div style="margin-top:18px"><strong style="color:var(--cs-accent)">Useful phrases:</strong><br>'
        for ph in data['phrases']:
            body += f'<span class="phrase-chip">{ph}</span>'
        body += '</div>\n'
    slides.append(render_slide('Part 1 — Interview', body))

    # Part 2
    p2 = data['part2']
    body = '<h2 class="glow-text">Part 2 — Photo Comparison</h2>\n'
    body += '<p style="color:var(--cs-text-muted);font-size:.85rem;margin-bottom:14px">Talk for 1 minute. Compare the photos and answer the question.</p>\n'
    body += f'<div class="question">{tooltipify(p2["question"], vocab)}</div>\n'
    body += '<div class="photo-grid">'
    body += f'<div class="photo-box">Photo A:<br>{p2["photoA"]}</div>'
    body += f'<div class="photo-box">Photo B:<br>{p2["photoB"]}</div>'
    body += '</div>\n'
    body += f'<button class="reveal-btn">Show model answer</button>\n'
    body += f'<div class="hidden-answer">{tooltipify(p2["model"], vocab)}</div>\n'
    slides.append(render_slide('Part 2 — Long Turn', body))

    # Part 3
    p3 = data['part3']
    body = '<h2 class="glow-text">Part 3 — Collaborative Task</h2>\n'
    body += '<p style="color:var(--cs-text-muted);font-size:.85rem;margin-bottom:14px">Discuss with your partner for 2–3 minutes, then decide.</p>\n'
    body += f'<div class="question">{tooltipify(p3["task"], vocab)}</div>\n'
    body += '<ul style="margin:12px 0 16px 18px;color:var(--cs-text-muted);font-size:.95rem">'
    for opt in p3['options']:
        body += f'<li>{opt}</li>'
    body += '</ul>\n'
    body += f'<button class="reveal-btn">Show model discussion</button>\n'
    body += f'<div class="hidden-answer">{tooltipify(p3["model"], vocab).replace(chr(10), "<br>")}</div>\n'
    slides.append(render_slide('Part 3 — Discussion', body))

    # Part 4
    p4 = data['part4']
    body = '<h2 class="glow-text">Part 4 — Follow-up Discussion</h2>\n'
    body += '<p style="color:var(--cs-text-muted);font-size:.85rem;margin-bottom:14px">Answer these deeper questions.</p>\n'
    for i, q in enumerate(p4['questions']):
        body += f'<div class="question">• {tooltipify(q, vocab)}</div>\n'
        body += f'<button class="reveal-btn">Show answer</button>\n'
        body += f'<div class="hidden-answer">{tooltipify(p4["answers"][i], vocab)}</div>\n'
    slides.append(render_slide('Part 4 — Extension', body))

    # Vocab slide
    body = '<h2 class="glow-text">Vocabulary & Phrases</h2>\n'
    for word, definition in vocab.items():
        body += f'<p><strong style="color:var(--cs-accent)">{word}</strong> — {definition}</p>\n'
    slides.append(render_slide('Vocabulary', body))

    # Homework
    hw = data['homework']
    hw_html = '<div class="question">Reading</div>\n'
    hw_html += f'<p>{hw["reading"]}</p>\n'
    hw_html += '<div class="question" style="margin-top:14px">Listening</div>\n'
    hw_html += f'<p>{hw["listening"]}</p>\n'
    hw_html += '<div class="question" style="margin-top:14px">Writing</div>\n'
    hw_html += f'<p>{hw["writing"]}</p>\n'

    out = template.replace('{{TITLE}}', data['title'])
    out = out.replace('{{SLIDES}}', '\n'.join(slides))
    out = out.replace('{{HOMEWORK}}', hw_html)
    total = 1 + len(slides) + 1
    out = out.replace('{{TOTAL}}', str(total))
    out = out.replace('{{FILE_KEY}}', data['file_key'])

    # Assign slide numbers to content slides (1..total-2)
    counter = iter(range(1, total - 1))
    out = re.sub(r'data-slide="\{\{SLIDE_NUM\}\}"', lambda m: f'data-slide="{next(counter)}"', out)
    out = out.replace('data-slide="{{LAST}}"', f'data-slide="{total - 1}"')

    # Add background images to slides if provided
    bg = data.get('bg')
    if bg:
        bg_style = f' style="background-image: url(\'{bg}\')"'
        out = out.replace('<section class="slide active" data-slide="0">',
                          '<section class="slide active" data-slide="0"' + bg_style + '>')
        out = out.replace(f'<section class="slide" data-slide="{total - 1}">',
                          f'<section class="slide" data-slide="{total - 1}"' + bg_style + '>')
        for n in range(1, total - 1):
            old = f'<section class="slide" data-slide="{n}">'
            new = f'<section class="slide" data-slide="{n}"' + bg_style + '>'
            out = out.replace(old, new)

    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('json')
    parser.add_argument('-o', '--out', required=True)
    args = parser.parse_args()
    with open(args.json, encoding='utf-8') as f:
        data = json.load(f)
    html = build(data)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Wrote', args.out)
