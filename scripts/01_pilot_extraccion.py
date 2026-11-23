import sys, time, pathlib
import pymupdf4llm
from docling.document_converter import DocumentConverter

out = pathlib.Path("data/pilot"); out.mkdir(parents=True, exist_ok=True)
conv = DocumentConverter()
for p in sys.argv[1:]:
    stem = pathlib.Path(p).stem[:40].replace(" ", "_")
    t = time.time(); md = pymupdf4llm.to_markdown(p); t1 = time.time() - t
    (out / f"{stem}.pymupdf.md").write_text(md, encoding="utf-8")
    t = time.time(); md2 = conv.convert(p).document.export_to_markdown(); t2 = time.time() - t
    (out / f"{stem}.docling.md").write_text(md2, encoding="utf-8")
    print(f"{stem}: pymupdf4llm {t1:.1f}s | docling {t2:.1f}s")
