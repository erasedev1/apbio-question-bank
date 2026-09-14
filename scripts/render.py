import json, os, io, collections, pypdfium2 as pdfium
PDF='/home/user/apbio-question-bank/vdoc.pub_campbell-biology-test-bank-11-edition.pdf'
OUT='render_out'; os.makedirs(OUT, exist_ok=True)
assign=json.load(open('assign.json'))
DPI=150; S=DPI/72.0; PAD=1

work=collections.defaultdict(list)
for key, ims in assign.items():
    oid=key.split(':',1)[1]
    ims=sorted(ims, key=lambda i:(i['top'], i['x0']))
    for n, im in enumerate(ims, 1):
        if im['page']==1: continue                      # cover page
        work[im['page']].append((oid, n, im, len(ims)))

def encode(crop):
    """Return (bytes, ext) choosing whichever of palette-PNG / JPEG is smaller."""
    rgb=crop.convert('RGB')
    cols=rgb.getcolors(maxcolors=65536)
    png=io.BytesIO()
    (rgb.convert('P', palette=1) if cols else rgb.quantize(colors=128, method=2)).save(
        png, format='PNG', optimize=True)
    if png.tell() <= 100_000:
        return png.getvalue(), 'png'
    jpg=io.BytesIO(); rgb.save(jpg, format='JPEG', quality=82, optimize=True, progressive=True)
    return (jpg.getvalue(), 'jpg') if jpg.tell() < png.tell() else (png.getvalue(), 'png')

pdf=pdfium.PdfDocument(PDF)
manifest=collections.defaultdict(list)
for pno in sorted(work):
    page=pdf[pno-1]
    bmp=page.render(scale=S).to_pil()
    for oid, n, im, total in work[pno]:
        x0=max(0,(im['x0']-PAD)*S); x1=min(bmp.width,(im['x1']+PAD)*S)
        y0=max(0,(im['top']-PAD)*S); y1=min(bmp.height,(im['bottom']+PAD)*S)
        if x1-x0<4 or y1-y0<4: continue
        crop=bmp.crop((int(x0),int(y0),int(x1),int(y1)))
        data, ext = encode(crop)
        name=f"{oid}-{n}.{ext}" if total>1 else f"{oid}.{ext}"
        open(os.path.join(OUT,name),'wb').write(data)
        manifest[oid].append({'file':name,'page':pno,'order':n,'w':crop.width,'h':crop.height})
    page.close()
json.dump(manifest, open('image_manifest.json','w'), indent=1)
print("rendered:",sum(len(v) for v in manifest.values()),"files for",len(manifest),"owners")
