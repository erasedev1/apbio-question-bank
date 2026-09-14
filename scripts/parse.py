import json, re, collections

pages = json.load(open('pages.json'))

# --- build page-aware line stream, stripping page furniture ---
stream = []   # (text, pdf_page_number_1based)
for pi, ptxt in enumerate(pages):
    plines = ptxt.split("\n")
    # strip trailing footer: copyright line and bare page-number line
    while plines:
        last = plines[-1].strip()
        if last.startswith("Copyright ©") or re.fullmatch(r'\d{1,4}', last):
            plines.pop()
        else:
            break
    for l in plines:
        if l.strip():
            stream.append((l.rstrip(), pi + 1))

RE_CH     = re.compile(r'^Chapter (\d+)\s+(.+?)\s*$')
RE_SUB    = re.compile(r'^(\d+)\.(\d+)\s+(Multiple[- ]Choice Questions|Student Edition End-of-Chapter Questions)\s*$')
RE_QSTART = re.compile(r'^(\d+)\)\s*(.*)$')
RE_CHOICE = re.compile(r'^([A-H])\)\s*(.*)$')
RE_ANS    = re.compile(r'^Answer:\s*(.+?)\s*$')
RE_BLOOM  = re.compile(r"^Bloom's Taxonomy:\s*(.+?)\s*$")
RE_SEC    = re.compile(r'^Section:\s*(.+?)\s*$')

questions = []
anomalies = []
chapter_no = chapter_title = None
qtype = None
expected = None
q = None
state = 'SEEK'

def flush():
    global q
    if q is not None:
        questions.append(q)
        q = None

for text, page in stream:
    s = text.strip()

    m = RE_CH.match(s)
    if m:
        flush(); state='SEEK'
        chapter_no = int(m.group(1)); chapter_title = m.group(2)
        qtype = None; expected = None
        continue

    m = RE_SUB.match(s)
    if m:
        flush(); state='SEEK'
        qtype = 'multiple_choice' if 'Multiple' in m.group(3) else 'end_of_chapter'
        expected = 1
        continue

    m = RE_QSTART.match(s)
    # a new question only if the number is the one we expect (guards against
    # numbered lists inside a stem or choice)
    if m and expected is not None and int(m.group(1)) == expected and state in ('SEEK','META','CHOICES'):
        flush()
        q = {'chapter_number': chapter_no, 'chapter_title': chapter_title,
             'question_type': qtype, 'number': expected,
             'stem_lines': [m.group(2)] if m.group(2) else [],
             'choices': collections.OrderedDict(), 'answer': None,
             'bloom': None, 'section': None, 'page': page}
        expected += 1
        state = 'STEM'
        continue

    if q is None:
        if s and chapter_no and not s.startswith('Copyright'):
            anomalies.append({'page': page, 'text': s[:120], 'reason': 'text outside any question'})
        continue

    m = RE_ANS.match(s)
    if m:
        q['answer'] = m.group(1); state='META'; continue
    m = RE_BLOOM.match(s)
    if m:
        q['bloom'] = m.group(1); state='META'; continue
    m = RE_SEC.match(s)
    if m:
        q['section'] = m.group(1); state='META'; continue

    m = RE_CHOICE.match(s)
    if m and state in ('STEM','CHOICES'):
        letter = m.group(1)
        # only treat as a new choice if it advances the sequence
        existing = list(q['choices'])
        nxt = chr(ord('A') + len(existing))
        if letter == nxt:
            q['choices'][letter] = [m.group(2)]
            state = 'CHOICES'
            continue

    # continuation line
    if state == 'STEM':
        q['stem_lines'].append(s)
    elif state == 'CHOICES' and q['choices']:
        q['choices'][list(q['choices'])[-1]].append(s)
    elif state == 'META':
        anomalies.append({'page': page, 'text': s[:120], 'reason': 'trailing text after metadata'})

flush()

# --- normalize ---
FIG = re.compile(r'\b(figure|graph|diagram|table|drawing|micrograph|pedigree|following image)\b', re.I)
out = []
for i, r in enumerate(questions, 1):
    stem = " ".join(" ".join(r['stem_lines']).split())
    choices = {k: " ".join(" ".join(v).split()) for k, v in r['choices'].items()}
    sec = r['section']
    rec = {
        'id': f"ch{r['chapter_number']:02d}-{'mc' if r['question_type']=='multiple_choice' else 'eoc'}-{r['number']:03d}",
        'chapter_number': r['chapter_number'],
        'chapter_title': r['chapter_title'],
        'topic_section': sec,
        'question_type': r['question_type'],
        'number_in_section': r['number'],
        'stem': stem,
        'choices': choices,
        'answer': r['answer'],
        'answer_text': choices.get(r['answer']),
        'bloom_taxonomy': r['bloom'],
        'references_figure': bool(FIG.search(stem)),
        'source_page': r['page'],
    }
    out.append(rec)

json.dump(out, open('questions_raw.json','w'), indent=1)
json.dump(anomalies, open('anomalies.json','w'), indent=1)
print("parsed questions:", len(out))
print("anomaly lines:", len(anomalies))
