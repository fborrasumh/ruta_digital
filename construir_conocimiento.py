#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construir_conocimiento.py — genera el conocimiento.json de Ruta Digital.

Uso:
    pip install pdfplumber python-docx
    python3 construir_conocimiento.py fuentes/ -o conocimiento.json

Cada archivo de `fuentes/` se trocea en fragmentos. Los textos legales se cortan
por artículo; el resto, por párrafos hasta un tamaño máximo.

El buscador de la app NO usa embeddings: compara palabras de más de tres letras
contra el campo `tema` + `texto`. Por eso el `tema` decide si un fragmento se
recupera o no. Ponga ahí el vocabulario con el que la app pregunta: los títulos
y focos de los módulos (cadena de custodia, evidencia volátil, hash, primer
respondiente, conservación de datos, cooperación internacional, atribución…).

Ese vocabulario extra se declara en `fuentes/_temas.json`:

    {
      "ley5307.txt": {
        "nombre": "Ley 53-07",
        "claves": "conservación datos tráfico conexión operadora plazo noventa días competencia DICAT procuraduría"
      },
      "iso27037.txt": {
        "nombre": "ISO/IEC 27037",
        "claves": "adquisición preservación evidencia volátil bloqueador escritura hash primer respondiente"
      }
    }
"""

import argparse, json, re, sys, unicodedata
from datetime import date
from pathlib import Path

MAX_PALABRAS = 320   # techo por fragmento: se inyecta entero en el prompt
MIN_PALABRAS = 25    # por debajo de esto no aporta contexto

RE_ARTICULO = re.compile(
    r"^\s*(Art[íi]culo|Art\.)\s+(\d+\s*(?:bis|ter|qu[aá]ter)?)\s*[.\-–—:]?",
    re.IGNORECASE | re.MULTILINE)


# ---------------------------------------------------------------- lectura
def leer(ruta: Path) -> str:
    ext = ruta.suffix.lower()
    if ext in (".txt", ".md"):
        return ruta.read_text(encoding="utf-8", errors="replace")
    if ext == ".pdf":
        try:
            import pdfplumber
        except ImportError:
            sys.exit("Falta pdfplumber:  pip install pdfplumber")
        with pdfplumber.open(ruta) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    if ext == ".docx":
        try:
            import docx
        except ImportError:
            sys.exit("Falta python-docx:  pip install python-docx")
        return "\n".join(p.text for p in docx.Document(str(ruta)).paragraphs)
    return ""


def limpiar(t: str) -> str:
    t = t.replace("\u00ad", "")                       # guion blando
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)            # palabra partida al saltar línea
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\d{1,4}\s*\n", "\n", t)         # números de página sueltos
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# ---------------------------------------------------------------- troceado
def partir_largo(texto: str, tope: int = MAX_PALABRAS):
    """Parte un bloque demasiado largo por párrafos, sin cortar frases."""
    trozos, actual = [], []
    for parrafo in texto.split("\n"):
        if not parrafo.strip():
            continue
        if len(" ".join(actual + [parrafo]).split()) > tope and actual:
            trozos.append("\n".join(actual))
            actual = []
        actual.append(parrafo)
    if actual:
        trozos.append("\n".join(actual))
    return trozos


def trocear(texto: str):
    """Devuelve [(etiqueta, contenido)]. Corta por artículo si los hay."""
    marcas = list(RE_ARTICULO.finditer(texto))
    if len(marcas) >= 3:
        bloques = []
        for i, m in enumerate(marcas):
            fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
            bloques.append(("art. " + m.group(2).strip(), texto[m.start():fin].strip()))
        salida = []
        for etiqueta, cuerpo in bloques:
            partes = partir_largo(cuerpo)
            for j, p in enumerate(partes):
                salida.append((etiqueta if len(partes) == 1 else f"{etiqueta} ({j+1}/{len(partes)})", p))
        return salida
    return [("", p) for p in partir_largo(texto)]


def slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description="Construye el conocimiento.json de Ruta Digital.")
    ap.add_argument("carpeta", help="carpeta con los textos normativos verificados")
    ap.add_argument("-o", "--salida", default="conocimiento.json")
    ap.add_argument("--fuente", default="Compilación normativa verificada")
    args = ap.parse_args()

    base = Path(args.carpeta)
    if not base.is_dir():
        sys.exit(f"No existe la carpeta {base}")

    meta_path = base / "_temas.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if not meta:
        print("⚠  No hay _temas.json. Los fragmentos se recuperarán solo por su propio\n"
              "   texto, que es bastante peor. Léase la cabecera de este script.\n")

    chunks, avisos = [], []
    for ruta in sorted(base.iterdir()):
        if ruta.name.startswith("_") or ruta.suffix.lower() not in (".txt", ".md", ".pdf", ".docx"):
            continue
        crudo = limpiar(leer(ruta))
        if not crudo:
            avisos.append(f"{ruta.name}: no se pudo extraer texto (¿PDF escaneado? hará falta OCR)")
            continue

        info = meta.get(ruta.name, {})
        nombre = info.get("nombre") or ruta.stem.replace("_", " ")
        claves = info.get("claves", "")

        n = 0
        for etiqueta, cuerpo in trocear(crudo):
            palabras = len(cuerpo.split())
            if palabras < MIN_PALABRAS:
                continue
            n += 1
            chunks.append({
                "id": f"{slug(nombre)}-{n:03d}",
                "tema": " · ".join(x for x in (nombre, etiqueta, claves) if x),
                "texto": cuerpo,
            })
        print(f"  {ruta.name:38} → {n:4d} fragmentos" + ("" if claves else "   (sin claves)"))
        if not n:
            avisos.append(f"{ruta.name}: 0 fragmentos útiles")

    if not chunks:
        sys.exit("\nNo se generó ningún fragmento.")

    salida = {
        "fuente": args.fuente,
        "generado": date.today().isoformat(),
        "aviso": "Textos que deben haber sido verificados contra la fuente oficial "
                 "antes de incluirse aquí. Esta base es la única garantía de que la "
                 "aplicación no invente artículos.",
        "chunks": chunks,
    }
    Path(args.salida).write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")

    pal = sum(len(c["texto"].split()) for c in chunks)
    print(f"\n✅ {args.salida}: {len(chunks)} fragmentos · {pal:,} palabras · "
          f"{Path(args.salida).stat().st_size/1024:.0f} KB")
    print(f"   Media {pal//len(chunks)} palabras por fragmento "
          f"(la app inyecta hasta 4 por reto).")
    for a in avisos:
        print("⚠ ", a)


if __name__ == "__main__":
    main()
