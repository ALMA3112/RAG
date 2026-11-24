import sys, time, pathlib, re
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import ImageRefMode

opts = PdfPipelineOptions()
opts.do_ocr = False
opts.do_table_structure = True
opts.generate_picture_images = True
opts.images_scale = 2.0
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})

out = pathlib.Path("data/pilot2"); out.mkdir(parents=True, exist_ok=True)
for p in sys.argv[1:]:
    stem = pathlib.Path(p).stem[:40].replace(" ", "_")
    t = time.time()
    doc = conv.convert(p).document
    md_path = out / f"{stem}.md"
    doc.save_as_markdown(md_path, artifacts_dir=pathlib.Path(f"{stem}_img"), image_mode=ImageRefMode.REFERENCED)
    dt = time.time() - t
    txt = md_path.read_text(encoding="utf-8")
    refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", txt)
    ok = sum(1 for r in refs if (out / r).exists())
    print(f"{stem}: {dt:.1f}s | imágenes referenciadas {len(refs)} | existen {ok} | ejemplo: {refs[0] if refs else None}")
