import json, collections, re
bank=json.load(open('questions_img.json'))
qs=bank['questions']

def im(e): return [e['file'], e['w'], e['h']]

out=[]
for q in qs:
    r={'i':q['id'],
       'c':q['chapter']['number'],
       's':q['topic']['section'],           # null for chapter-review questions
       't':'mc' if q['question_type']=='multiple_choice' else 'eoc',
       'q':q['stem'],
       'o':q['choices'],
       'a':q['answer'],
       'b':q['bloom_taxonomy'],
       'p':q['source_page']}
    if q['images']:        r['f']=[im(e) for e in q['images']]
    if q['shared_images']: r['g']=[im(e) for e in q['shared_images']]
    if q['choice_images']: r['m']={k:im(v) for k,v in q['choice_images'].items()}
    out.append(r)

chapters=collections.OrderedDict()
for q in qs:
    cn=q['chapter']['number']
    c=chapters.setdefault(cn,{'n':cn,'t':q['chapter']['title'],'secs':collections.Counter()})
    c['secs'][q['topic']['section'] or 'review']+=1
def seckey(s):
    if s=='review': return (1, 0, 0, '')
    m=re.match(r'(\d+)\.(\d+)', s)
    return (0, int(m.group(1)), int(m.group(2)), s) if m else (0, 999, 999, s)

chap=[{'n':c['n'],'t':c['t'],
       'secs':[{'s':k,'n':v} for k,v in sorted(c['secs'].items(), key=lambda kv: seckey(kv[0]))]}
      for c in chapters.values()]

payload={'chapters':chap,'questions':out}
with open('questions_site.js','w',encoding='utf-8') as f:
    f.write('window.BANK=')
    json.dump(payload,f,ensure_ascii=False,separators=(',',':'))
    f.write(';')
print("questions:",len(out),"chapters:",len(chap))
print("with figures:",sum(1 for r in out if 'f' in r or 'g' in r),
      " with choice-images:",sum(1 for r in out if 'm' in r))
