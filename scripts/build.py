import json, re, collections, hashlib

qs = json.load(open('questions_raw.json'))
an = json.load(open('anomalies.json'))
NOISE = "Campbell Biology, 11e (Urry)"

# --- rebuild stimulus blocks from anomaly lines ---
blocks = []; cur = []; prev = None
for a in an:
    if a['text'].startswith(NOISE):
        continue
    if prev is not None and a['page'] - prev > 1:
        blocks.append(cur); cur = []
    cur.append(a); prev = a['page']
if cur: blocks.append(cur)

stimuli = []
for n, b in enumerate(blocks, 1):
    stimuli.append({
        'id': f'stim-{n:02d}',
        'source_page': b[0]['page'],
        'text': " ".join(" ".join(x['text'] for x in b).split()),
    })
start_pages = {s['source_page']: s['id'] for s in stimuli}

# --- link questions to stimuli (section-bounded, inferred) ---
link = {}
for s in stimuli:
    pg = s['source_page']
    idxs = [k for k, q in enumerate(qs) if q['source_page'] >= pg]
    if not idxs: continue
    i = idxs[0]; base = qs[i]
    for q in qs[i:]:
        if (q['chapter_number'] != base['chapter_number']
                or q['question_type'] != base['question_type']
                or q['topic_section'] != base['topic_section']):
            break
        if q['source_page'] > pg and q['source_page'] in start_pages:
            break
        link.setdefault(q['id'], s['id'])

# --- final records ---
out = []
for q in qs:
    imgs = all(not v for v in q['choices'].values())
    rec = {
        'id': q['id'],
        'chapter': {'number': q['chapter_number'], 'title': q['chapter_title']},
        'topic': {
            'section': q['topic_section'],
            'scope': 'section' if q['topic_section'] else 'chapter_review',
        },
        'question_type': q['question_type'],
        'number_in_section': q['number_in_section'],
        'stem': q['stem'],
        'choices': q['choices'],
        'answer': q['answer'],
        'answer_text': q['answer_text'] or None,
        'bloom_taxonomy': q['bloom_taxonomy'],
        'source_page': q['source_page'],
        'flags': {
            'references_figure': q['references_figure'],
            'choices_are_images': imgs,
            'shared_stimulus_id': link.get(q['id']),
            'shared_stimulus_link_inferred': bool(link.get(q['id'])),
        },
    }
    out.append(rec)

bank = {
    'source': {
        'file': 'vdoc.pub_campbell-biology-test-bank-11-edition.pdf',
        'title': 'Campbell Biology, 11e (Urry) — Test Bank',
        'pages': 1243,
        'copyright': 'Copyright © 2017 Pearson Education, Inc.',
    },
    'taxonomy': {
        'derivation': 'Chapter and topic tags are taken verbatim from the PDF\'s own structure.',
        'chapter': 'From "Chapter N <title>" headings in the PDF.',
        'topic': 'From each question\'s "Section: N.N" field (the textbook section). '
                 'Section TITLES do not appear anywhere in this test bank PDF, so topics are '
                 'identified by section number only.',
        'chapter_review': 'Questions under "Student Edition End-of-Chapter Questions" carry no '
                          'Section field in the source; their topic scope is "chapter_review".',
    },
    'counts': {
        'questions': len(out),
        'chapters': len(set(r['chapter']['number'] for r in out)),
        'topics': len(set(r['topic']['section'] for r in out if r['topic']['section'])),
    },
    'shared_stimuli': stimuli,
    'questions': out,
}
json.dump(bank, open('questions.json', 'w'), indent=1, ensure_ascii=False)

# --- chapter/topic index ---
idx = collections.OrderedDict()
for r in out:
    cn = r['chapter']['number']
    e = idx.setdefault(cn, {'chapter_number': cn, 'chapter_title': r['chapter']['title'],
                            'topics': collections.Counter(), 'total': 0,
                            'multiple_choice': 0, 'chapter_review': 0})
    e['total'] += 1
    e['topics'][r['topic']['section'] or 'chapter_review'] += 1
    e['multiple_choice' if r['question_type'] == 'multiple_choice' else 'chapter_review'] += 1
index = []
for cn in sorted(idx):
    e = idx[cn]
    index.append({'chapter_number': cn, 'chapter_title': e['chapter_title'],
                  'question_count': e['total'],
                  'multiple_choice': e['multiple_choice'],
                  'chapter_review': e['chapter_review'],
                  'topics': [{'section': k, 'question_count': v}
                             for k, v in sorted(e['topics'].items(),
                                                key=lambda kv: (kv[0] == 'chapter_review', kv[0]))]})
json.dump({'chapters': index}, open('chapters.json', 'w'), indent=1, ensure_ascii=False)

print("questions:", len(out))
print("chapters:", bank['counts']['chapters'], "topics:", bank['counts']['topics'])
print("linked to stimulus:", sum(1 for r in out if r['flags']['shared_stimulus_id']))
print("image-only choices:", sum(1 for r in out if r['flags']['choices_are_images']))
print("references figure:", sum(1 for r in out if r['flags']['references_figure']))
