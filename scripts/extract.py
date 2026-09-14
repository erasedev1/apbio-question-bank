import pdfplumber, json, sys
pages=[]
with pdfplumber.open('/home/user/apbio-question-bank/vdoc.pub_campbell-biology-test-bank-11-edition.pdf') as pdf:
    for i,p in enumerate(pdf.pages):
        t=p.extract_text() or ''
        pages.append(t)
        if i%100==0: print('page',i,file=sys.stderr)
json.dump(pages,open('pages.json','w'))
print('done',len(pages),file=sys.stderr)
