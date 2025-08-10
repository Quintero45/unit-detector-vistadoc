import cv2
import pytesseract
import numpy as np
import re

# Ruta de Tesseract en Windows (ajústala si está en otro lugar)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def detect_units(image_path):
    # Cargar imagen
    image = cv2.imread(image_path)
    if image is None:
        raise Exception("No se pudo cargar la imagen")

    # Convertir a gris
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Mejorar contraste e invertir si fondo es negro
    if np.mean(gray) < 127:
        gray = cv2.bitwise_not(gray)

    # Preprocesamiento para OCR
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Extraer datos con Tesseract
    data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)

    boxes = []
    for i, text in enumerate(data['text']):
        clean_text = text.strip()
        # Filtrar solo números (201-278 por ejemplo)
        if re.fullmatch(r"\d{3}", clean_text):
            try:
                num = int(clean_text)
                if 200 <= num <= 300:  # Rango configurable
                    x = int(data['left'][i])
                    y = int(data['top'][i])
                    w = int(data['width'][i])
                    h = int(data['height'][i])

                    # Expandir la caja para cubrir todo el apartamento
                    pad_w = w * 3
                    pad_h = h * 3
                    center_x = x + w // 2
                    center_y = y + h // 2

                    boxes.append({
                        "center": [int(center_x), int(center_y)],
                        "width": int(pad_w),
                        "height": int(pad_h),
                        "angle": 0,
                        "text": clean_text
                    })
            except ValueError:
                continue

    return boxes
