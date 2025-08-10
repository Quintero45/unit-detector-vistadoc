# main.py
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os

from detector import detect_units
from draw_boxes import draw_boxes

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/detect-units", methods=["POST"])
def detect_units_endpoint():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    filename = secure_filename(file.filename)
    in_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(in_path)

    try:
        boxes = detect_units(in_path)
        out_path = os.path.join(OUTPUT_FOLDER, f"boxed_{os.path.splitext(filename)[0]}.png")
        draw_boxes(in_path, boxes, out_path, rotated=True, number=True)
        return jsonify({
            "count": len(boxes),
            "units": boxes,
            "image_with_boxes": f"/download/{os.path.basename(out_path)}"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download/<name>", methods=["GET"])
def download(name):
    path = os.path.join(OUTPUT_FOLDER, name)
    if not os.path.exists(path):
        return jsonify({"error": "Archivo no encontrado"}), 404
    return send_file(path, mimetype="image/png")

if __name__ == "__main__":
    app.run(port=5001, debug=True)
