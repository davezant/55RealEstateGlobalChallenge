import os
import re
import uuid

from services.errors import UploadRejected

MAX_BYTES = 14 * 1024 * 1024

FILENAME_PATTERN = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")

def detect_image_extension(head: bytes) -> str | None:
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None

def save_upload(file_storage, upload_dir: str) -> str:
    if file_storage is None or not getattr(file_storage, "filename", ""):
        raise UploadRejected("arquivo_ausente", 400)

    data = file_storage.stream.read(MAX_BYTES + 1)

    if not data:
        raise UploadRejected("arquivo_ausente", 400)
    if len(data) > MAX_BYTES:
        raise UploadRejected("arquivo_grande", 413)

    extension = detect_image_extension(data[:16])

    if extension is None:
        raise UploadRejected("tipo_invalido", 415)

    filename = f"{uuid.uuid4().hex}{extension}"
    os.makedirs(upload_dir, exist_ok=True)

    with open(os.path.join(upload_dir, filename), "wb") as file:
        file.write(data)

    return filename

def remove_file(upload_dir: str, filename: str) -> None:
    if not FILENAME_PATTERN.match(filename):
        return
    try:
        os.remove(os.path.join(upload_dir, filename))
    except FileNotFoundError:
        pass
