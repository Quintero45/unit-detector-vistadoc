# draw_boxes.py
import cv2
import numpy as np

def draw_boxes(image_path, units, output_path, rotated=True, number=True):
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError("No se pudo cargar la imagen para dibujar")

    for i, u in enumerate(units, start=1):
        if rotated and "polygon" in u:
            pts = np.array(u["polygon"], dtype=np.int32)
            cv2.polylines(img, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            if number:
                cx, cy = int(u["center"]["x"]), int(u["center"]["y"])
                cv2.putText(img, str(i), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1, cv2.LINE_AA)
        else:
            x, y = int(u["x"]), int(u["y"])
            w, h = int(u["width"]), int(u["height"])
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            if number:
                cv2.putText(img, str(i), (x + 3, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1, cv2.LINE_AA)

    cv2.imwrite(output_path, img)
    return output_path
