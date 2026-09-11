import pdfplumber, json, re, sys, collections
PDF='/home/user/apbio-question-bank/vdoc.pub_campbell-biology-test-bank-11-edition.pdf'

RE_CH     = re.compile(r'^Chapter (\d+)\s+(.+?)\s*$')
RE_SUB    = re.compile(r'^(\d+)\.(\d+)\s+(Multiple[- ]Choice Questions|Student Edition End-of-Chapter Questions)\s*$')
RE_QSTART = re.compile(r'^(\d+)\)\s*(.*)$')
RE_CHOICE = re.compile(r'^([A-H])\)\s*(.*)$')
RE_META   = re.compile(r"^(Answer|Bloom's Taxonomy|Section):")
NOISE     = "Campbell Biology, 11e (Urry)"

anchors=[]      # (page, top, kind, id)
images=[]
chapter=None; qtype=None; expected=None; state='SEEK'
stim_n=0; in_stim=False

with pdfplumber.open(PDF) as pdf:
    for pno, page in enumerate(pdf.pages, 1):
        for im in page.images:
            images.append({'page':pno,'x0':im['x0'],'top':im['top'],'x1':im['x1'],
                           'bottom':im['bottom'],'w':im['width'],'h':im['height']})
        for ln in page.extract_text_lines(layout=False):
            s = ln['text'].strip()
            if not s or s.startswith('Copyright ©') or re.fullmatch(r'\d{1,4}', s) or s.startswith(NOISE):
                continue
            m = RE_CH.match(s)
            if m:
                chapter=int(m.group(1)); qtype=None; expected=None; state='SEEK'; in_stim=False; continue
            m = RE_SUB.match(s)
            if m:
                qtype='mc' if 'Multiple' in m.group(3) else 'eoc'; expected=1; state='SEEK'; in_stim=False; continue
            m = RE_QSTART.match(s)
            if m and expected is not None and int(m.group(1))==expected and state in ('SEEK','META','CHOICES'):
                qid=f"ch{chapter:02d}-{qtype}-{expected:03d}"
                anchors.append((pno, ln['top'], 'question', qid))
                expected+=1; state='STEM'; in_stim=False; continue
            if RE_META.match(s):
                state='META'; continue
            mc = RE_CHOICE.match(s)
            if mc and state in ('STEM','CHOICES'):
                state='CHOICES'; continue
            # a non-question, non-choice, non-meta line while in META = stimulus preamble
            if state=='META':
                if not in_stim:
                    stim_n+=1; in_stim=True
                    anchors.append((pno, ln['top'], 'stimulus', f"stim-{stim_n:02d}"))
                continue
        if pno % 200 == 0: print('page',pno,file=sys.stderr)

json.dump({'anchors':anchors,'images':images}, open('layout.json','w'))
print("anchors:",len(anchors),"questions:",sum(1 for a in anchors if a[2]=='question'),
      "stimuli:",sum(1 for a in anchors if a[2]=='stimulus'),"images:",len(images))
