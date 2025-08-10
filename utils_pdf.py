import fitz  # PyMuPDF
from PIL import Image
import numpy as np
import os

def pdf_first_page_to_image(pdf_path: str, out_path: str, dpi: int = 200) -> str:
    """
    Renderiza la primera página del PDF a PNG y devuelve la ruta.
    """
    doc = fitz.open(pdf_path)
    if doc.page_count == 0:
        raise ValueError("PDF sin páginas")

    page = doc.load_page(0)
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(out_path)
    doc.close()
    return out_path


def ensure_raster(input_path: str, output_dir: str) -> str:
    """
    Si es PDF -> renderiza primera página a PNG dentro de output_dir.
    Si ya es imagen -> copia/salva a PNG y devuelve la ruta.
    """
    ext = os.path.splitext(input_path.lower())[1]
    out_name = os.path.splitext(os.path.basename(input_path))[0] + ".png"
    out_path = os.path.join(output_dir, out_name)

    if ext == ".pdf":
        return pdf_first_page_to_image(input_path, out_path, dpi=220)
    else:
        # abrir con PIL y guardar como PNG para normalizar
        img = Image.open(input_path).convert("RGB")
        img.save(out_path)
        return out_path
