import cv2

def draw_boxes(image_path, boxes, output_path, rotated=False):
    image = cv2.imread(image_path)

    for i, box in enumerate(boxes):
        # Dibujar rectángulos rotados
        rect = (
            (int(box["center"][0]), int(box["center"][1])),
            (int(box["width"]), int(box["height"])),
            float(box["angle"])
        )
        box_points = cv2.boxPoints(rect)
        box_points = box_points.astype(int)
        cv2.drawContours(image, [box_points], 0, (0, 255, 0), 2)

        # Etiqueta numérica
        cv2.putText(image, str(i+1), (int(box["center"][0]), int(box["center"][1])),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    cv2.imwrite(output_path, image)
