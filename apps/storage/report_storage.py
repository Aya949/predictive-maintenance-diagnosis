"""
File storage abstraction for generated reports.
Currently backed by local disk; swap the implementation later for
cloud/object storage (S3, etc.) without changing any calling code.
"""

import os
from datetime import datetime

# Storage root — adjust if you want it elsewhere
STORAGE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage")


class ReportStorage:
    @staticmethod
    def save(pdf_bytes: bytes, machine_code: str, reading_id: int) -> str:
        """
        Saves the PDF to disk under storage/reports/YYYY/MM/, returns the
        relative file path to store in the database.
        """
        now = datetime.utcnow()
        subdir = os.path.join("reports", str(now.year), f"{now.month:02d}")
        full_dir = os.path.join(STORAGE_ROOT, subdir)
        os.makedirs(full_dir, exist_ok=True)

        filename = f"{machine_code}_reading_{reading_id}.pdf"
        relative_path = os.path.join(subdir, filename)
        full_path = os.path.join(STORAGE_ROOT, relative_path)

        with open(full_path, "wb") as f:
            f.write(pdf_bytes)

        return relative_path.replace("\\", "/")  # normalize for consistent DB storage on Windows

    @staticmethod
    def read(relative_path: str) -> bytes:
        full_path = os.path.join(STORAGE_ROOT, relative_path)
        with open(full_path, "rb") as f:
            return f.read()

    @staticmethod
    def exists(relative_path: str) -> bool:
        return os.path.exists(os.path.join(STORAGE_ROOT, relative_path))