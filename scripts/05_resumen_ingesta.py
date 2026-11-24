import csv, collections, pathlib
M = pathlib.Path("data/manifests")
rd = lambda n: list(csv.DictReader(open(M / n, encoding="utf-8")))
docs, sec, qa, img = rd("manifest_documentos.csv"), rd("secciones.csv"), rd("qa_ingesta.csv"), rd("imagenes.csv")

print(f"documentos: {len(docs)} | con error.txt: {len(list(pathlib.Path('data/markdown').glob('FDS_*/error.txt')))}")
print("estados de sección:", dict(collections.Counter(r["estado"] for r in sec)))
for e in ("FALLO_EXTRACCION", "AUSENTE_EN_ORIGINAL", "SOLO_EN_MD_REVISAR"):
    items = sorted({(r["id"], r["seccion"]) for r in sec if r["estado"] == e})
    print(f"  {e}: {len(items)} -> {items[:25]}")
print("páginas md != pdf:", [r["id"] for r in qa if r["paginas_coinciden"] != "True"])
fus = [(r["id"], int(r["filas_tabla_fusionadas"])) for r in qa if int(r["filas_tabla_fusionadas"]) > 0]
print(f"filas de tabla fusionadas: {sum(n for _, n in fus)} en {len(fus)} docs -> {fus[:30]}")
print("fabricantes:", dict(collections.Counter(r["fabricante"] for r in docs)))
print("fuente del fabricante:", dict(collections.Counter(r["fabricante_fuente"] for r in docs)))
sinv = [r["id"] for r in docs if not (r["version_archivo"] or r["version_texto"])]
sinf = [r["id"] for r in docs if not (r["fecha_emision"] or r["fecha_revision"] or r["fecha_actualizacion"])]
print(f"sin versión: {len(sinv)} | sin fecha: {len(sinf)} -> {sinf}")
print(f"imágenes únicas: {len(img)} | decorativas probables: {sum(r['decorativa_probable'] == 'True' for r in img)}")
print(f"tiempo total de conversión: {sum(float(r['tiempo_s']) for r in docs) / 60:.0f} min")
