import cv2
import numpy as np
import os

DEBUG_DIR = "outputs"

def _ensure_dir(d):
    os.makedirs(d, exist_ok=True)

def _save(name, img):
    _ensure_dir(DEBUG_DIR)
    cv2.imwrite(os.path.join(DEBUG_DIR, name), img)

def _to_rotated_box(min_rect):
    (cx, cy), (w, h), angle = min_rect
    box = cv2.boxPoints(min_rect)
    box = np.int32(box).tolist()
    return {
        "center": {"x": float(cx), "y": float(cy)},
        "width":  float(max(w, 1e-6)),
        "height": float(max(h, 1e-6)),
        "angle":  float(angle),
        "polygon": box
    }

def _pipeline(gray, thr=0, use_otsu=True, dilate_i=1, close_i=1, erode_i=1):
    # 1) binarizar: líneas blancas = 255
    if use_otsu:
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, th = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)
    _save(f"debug_1_thresh.png", th)

    # 2) engrosar paredes para cerrar huecos
    k = np.ones((3,3), np.uint8)
    th_thick = cv2.dilate(th, k, iterations=dilate_i)
    th_thick = cv2.morphologyEx(th_thick, cv2.MORPH_CLOSE, k, iterations=close_i)
    _save(f"debug_2_lines_thick.png", th_thick)

    # 3) invertir: interiores + fondo = blanco, líneas = negro
    inv = 255 - th_thick
    _save(f"debug_3_inverted.png", inv)

    # 4) flood-fill desde borde para quitar SOLO fondo exterior
    ff = inv.copy()
    h, w = ff.shape
    mask = np.zeros((h+2, w+2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 0)  # pone a 0 el exterior
    _save(f"debug_4_floodfilled.png", ff)

    # 5) adelgazar un poco (deja interiores separados de las líneas)
    ff = cv2.erode(ff, k, iterations=erode_i)
    ff = cv2.morphologyEx(ff, cv2.MORPH_OPEN, k, iterations=1)
    _save(f"debug_5_interiors.png", ff)

    # 6) contornos de interiores
    contours, _ = cv2.findContours(ff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours, ff

def detect_units(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError("No se pudo cargar la imagen")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Aumentar contraste (ayuda si el trazo es fino)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    _save("debug_0_gray.png", gray)

    # Primer intento (suave)
    contours, ff = _pipeline(gray, use_otsu=True, dilate_i=1, close_i=1, erode_i=1)

    # Si no encontró nada, reintento engrosando más
    if len(contours) == 0:
        contours, ff = _pipeline(gray, use_otsu=True, dilate_i=2, close_i=2, erode_i=1)

    # Si aún nada, reintento sin OTSU con umbral alto
    if len(contours) == 0:
        contours, ff = _pipeline(gray, thr=210, use_otsu=False, dilate_i=2, close_i=2, erode_i=1)

    h, w = gray.shape
    img_area = float(h * w)
    min_area = img_area * 0.00025   # ~70 px en 540x520
    max_area = img_area * 0.02      # evita bloques gigantes

    boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue

        rect = cv2.minAreaRect(cnt)
        (rw, rh) = rect[1]
        if rw <= 6 or rh <= 6:
            continue

        ratio = max(rw, rh) / max(1.0, min(rw, rh))
        if ratio > 6.0:
            continue

        boxes.append(_to_rotated_box(rect))

    # ordenar por área ascendente (opcional)
    boxes.sort(key=lambda b: b["width"] * b["height"])

    import math

    def _area(b):
        return b["width"] * b["height"]

    def _bbox(b):
        # caja axis-aligned para pruebas rápidas de inclusión/IoU
        xs = [p[0] for p in b["polygon"]]
        ys = [p[1] for p in b["polygon"]]
        return (min(xs), min(ys), max(xs), max(ys))

    def _iou(a, b):
        ax1, ay1, ax2, ay2 = _bbox(a)
        bx1, by1, bx2, by2 = _bbox(b)
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
        inter = iw * ih
        if inter == 0: return 0.0
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        return inter / float(area_a + area_b - inter + 1e-6)

    def _is_inside(small, big, tol=0.9):
        # small mayormente contenido en big?
        sx1, sy1, sx2, sy2 = _bbox(small)
        bx1, by1, bx2, by2 = _bbox(big)
        w = max(1, sx2 - sx1);
        h = max(1, sy2 - sy1)
        cover_w = max(0, min(sx2, bx2) - max(sx1, bx1))
        cover_h = max(0, min(sy2, by2) - max(sy1, by1))
        covered = (cover_w * cover_h) / float(w * h)
        return covered >= tol

    # ---------- POST-FILTRO ----------
    img_area = float(h * w)
    MIN_AREA = img_area * 0.0015  # sube mucho el piso (antes era 0.00025)
    MAX_AREA = img_area * 0.03
    MIN_SIDE = 20  # píxeles
    MIN_AR, MAX_AR = 1.4, 4.8  # relación de aspecto típica de las unidades

    filtered = []
    for b in boxes:
        a = _area(b)
        if a < MIN_AREA or a > MAX_AREA:
            continue
        sw, sh = b["width"], b["height"]
        if sw < MIN_SIDE or sh < MIN_SIDE:
            continue

        ar = max(sw, sh) / max(1.0, min(sw, sh))
        if ar < MIN_AR or ar > MAX_AR:
            continue

        # ángulos extremos suelen ser ruido
        ang = abs(b["angle"])
        if ang > 92:
            continue

        filtered.append(b)

    # quitar anidadas (keep outer)
    filtered.sort(key=lambda x: _area(x), reverse=True)
    final_boxes = []
    for b in filtered:
        if any(_is_inside(b, k) for k in final_boxes):
            continue
        # también elimina casi duplicadas
        if any(_iou(b, k) > 0.7 for k in final_boxes):
            continue
        final_boxes.append(b)

    boxes = final_boxes

    return boxes
