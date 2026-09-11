import json, collections
bank=json.load(open('questions.json'))
qs=bank['questions']
man=json.load(open('image_manifest.json'))
anchors=sorted([tuple(a) for a in json.load(open('layout.json'))['anchors']], key=lambda a:(a[0],a[1]))
qmap={q['id']:q for q in qs}
order={q['id']:i for i,q in enumerate(qs)}

def key(q): return (q['chapter']['number'], q['question_type'], q['topic']['section'])

def imgs_for(oid):
    return [{'file':e['file'],'w':e['w'],'h':e['h'],'page':e['page']}
            for e in sorted(man.get(oid,[]), key=lambda e:e['order'])]

shared=collections.defaultdict(list)   # qid -> images inherited from a stimulus block

# 1. propagate stimulus-block images forward over the questions they introduce
for i,(pno,top,kind,oid) in enumerate(anchors):
    if kind!='stimulus' or oid not in man: continue
    ims=imgs_for(oid)
    base=None
    for pno2,top2,kind2,oid2 in anchors[i+1:]:
        if kind2=='stimulus': break
        q=qmap.get(oid2)
        if q is None: continue
        if base is None: base=key(q)
        elif key(q)!=base: break
        shared[q['id']].extend(ims)

# 2. attach own images; split out image-answer-choices when counts line up
for q in qs:
    own=imgs_for(q['id'])
    q['choice_images']={}
    if q['flags']['choices_are_images'] and len(own)==len(q['choices']):
        for letter, im in zip(sorted(q['choices']), own):
            q['choice_images'][letter]=im
        own=[]
    q['images']=own

# 3. a question that names a figure but holds none inherits the nearest one above it
#    within the same chapter/type/section
for i,q in enumerate(qs):
    if q['images'] or q['choice_images'] or shared.get(q['id']): continue
    if not q['flags']['references_figure']: continue
    for prev in reversed(qs[:i]):
        if key(prev)!=key(q): break
        if prev['images']:
            shared[q['id']]=list(prev['images']); break

for q in qs:
    q['shared_images']=shared.get(q['id'],[])
    q['flags']['has_image']=bool(q['images'] or q['choice_images'] or q['shared_images'])
    q['flags']['image_inherited']=bool(q['shared_images']) and not q['images']

for s in bank['shared_stimuli']:
    s.pop('images',None)

bank['counts']['images']=sum(len(v) for v in man.values())
bank['counts']['questions_with_image']=sum(1 for q in qs if q['flags']['has_image'])
json.dump(bank, open('questions_img.json','w'), indent=1, ensure_ascii=False)

fig={q['id'] for q in qs if q['flags']['references_figure']}
cov={q['id'] for q in qs if q['flags']['has_image']}
print("questions with any image:",len(cov))
print("  own figures:",sum(1 for q in qs if q['images']))
print("  choice images:",sum(1 for q in qs if q['choice_images']))
print("  inherited/shared:",sum(1 for q in qs if q['shared_images']))
print("figure-referencing questions:",len(fig),"-> covered:",len(fig&cov),"still uncovered:",len(fig-cov))
print("image-choice questions covered:",
      sum(1 for q in qs if q['flags']['choices_are_images'] and q['flags']['has_image']),"/ 21")
