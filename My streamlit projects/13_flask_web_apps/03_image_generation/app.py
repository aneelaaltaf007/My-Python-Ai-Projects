# import libraries
import os
import uuid
import requests
from pathlib import Path
from urllib.parse import quote
from flask import Flask, render_template, request, send_from_directory
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # pip install tomli (older Python)
    except ImportError:
        tomllib = None


def get_api_key():
    """Look in .env / environment first, then in secrets.toml next to app.py."""
    key = os.getenv("POLLINATIONS_API_KEY")
    if key:
        return key.strip()
    secrets_file = BASE_DIR / "secrets.toml"
    if tomllib and secrets_file.is_file():
        with open(secrets_file, "rb") as f:
            return (tomllib.load(f).get("POLLINATIONS_API_KEY") or "").strip() or None
    return None


API_KEY = get_api_key()

app = Flask(__name__)

IMAGE_FOLDER = BASE_DIR / "static" / "generated"
IMAGE_FOLDER.mkdir(parents=True, exist_ok=True)

API_URL = "https://gen.pollinations.ai/image/"

SIZES = {
    "1024x1024": "Square (1024x1024)",
    "1280x720": "Landscape 16:9",
    "720x1280": "Portrait 9:16",
}
MODELS = {
    "flux": "FLUX",
}
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp"}
GALLERY_LIMIT = 12


def recent_images(limit=GALLERY_LIMIT):
    files = [f for f in IMAGE_FOLDER.iterdir() if f.suffix.lower() in ALLOWED_EXT]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [f.name for f in files[:limit]]


@app.route("/", methods=["GET", "POST"])
def index():
    form = {"prompt": "", "size": "1024x1024", "model": "flux"}
    image_filename = None
    error = None

    if request.method == "POST":
        form["prompt"] = request.form.get("prompt", "").strip()
        form["size"] = request.form.get("size", form["size"])
        form["model"] = request.form.get("model", form["model"])

        if not form["prompt"]:
            error = "Please enter an image prompt."
        elif len(form["prompt"]) > 1000:
            error = "Prompt is too long (max 1000 characters)."
        elif form["size"] not in SIZES or form["model"] not in MODELS:
            error = "Invalid option selected."
        elif not API_KEY:
            error = "API key missing. Add POLLINATIONS_API_KEY to your .env or secrets.toml file."
        else:
            try:
                width, height = form["size"].split("x")
                resp = requests.get(
                    API_URL + quote(form["prompt"], safe=""),
                    params={"model": form["model"], "width": width, "height": height},
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    timeout=120,
                )
                resp.raise_for_status()

                content_type = resp.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    raise ValueError(f"Unexpected response: {content_type}")

                ext = ".png" if "png" in content_type else ".webp" if "webp" in content_type else ".jpg"
                image_filename = f"{uuid.uuid4().hex}{ext}"
                (IMAGE_FOLDER / image_filename).write_bytes(resp.content)

            except Exception as e:
                app.logger.exception("Image generation failed")
                error = f"Image generation failed: {e}"

    return render_template(
        "index.html",
        form=form,
        sizes=SIZES,
        models=MODELS,
        image_filename=image_filename,
        gallery=recent_images(),
        error=error,
    )


@app.route("/download/<filename>")
def download_image(filename):
    if Path(filename).name != filename:
        return "Invalid filename", 400
    path = IMAGE_FOLDER / filename
    if not path.is_file() or path.suffix.lower() not in ALLOWED_EXT:
        return "Image not found", 404
    return send_from_directory(
        IMAGE_FOLDER, filename,
        as_attachment=True,
        download_name=f"generated_image{path.suffix}",
    )


if __name__ == "__main__":
    app.run(debug=True)