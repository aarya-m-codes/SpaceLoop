import os
import secrets
from pathlib import Path
from werkzeug.datastructures import FileStorage

BASE_DIR = Path(__file__).resolve().parents[3]
UPLOAD_FOLDER = BASE_DIR / "uploads"
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB upload limit


# Supported image format signatures (Magic Bytes)
IMAGE_SIGNATURES = {
    "jpeg": [(0, b"\xff\xd8\xff")],
    "png": [(0, b"\x89PNG\r\n\x1a\n")],
    "gif": [(0, b"GIF87a"), (0, b"GIF89a")],
}


def detect_image_type(header: bytes) -> str | None:
    """Detect image MIME type from binary magic bytes header."""
    if not header or len(header) < 12:
        return None

    # Check JPEG
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"

    # Check PNG
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    # Check GIF
    if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return "gif"

    # Check WEBP: starts with RIFF and bytes 8:12 are WEBP
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "webp"

    return None


class PhotoService:
    """Space photo upload handling with strict security & file-header verification."""

    @staticmethod
    def save_photo(file: FileStorage) -> tuple[str | None, str | None, int]:
        """Validate 5MB limit, verify file-header magic bytes, and persist photo.
        
        Returns:
            (public_url, error_message, http_status_code)
        """
        if not file or not file.filename:
            return None, "No photo file provided.", 400

        # Read file contents into memory to verify size and signature
        file_bytes = file.read()
        file_size = len(file_bytes)

        if file_size == 0:
            return None, "Uploaded file is empty.", 400

        # Enforce 5MB upload limit
        if file_size > MAX_FILE_SIZE_BYTES:
            return None, f"Photo exceeds the 5MB upload limit ({round(file_size / (1024*1024), 2)}MB).", 413

        # Header Magic Bytes validation (prevents disguised shell scripts or binaries)
        header = file_bytes[:16]
        detected_ext = detect_image_type(header)
        if not detected_ext:
            return None, "Invalid image format. Supported formats: JPEG, PNG, WEBP, and GIF.", 400

        # Persist to disk with secure random token
        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        filename = f"{secrets.token_hex(16)}.{detected_ext}"
        destination = UPLOAD_FOLDER / filename

        with open(destination, "wb") as f:
            f.write(file_bytes)

        public_url = f"/uploads/{filename}"
        return public_url, None, 201
