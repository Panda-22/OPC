import io
from typing import Optional
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        texts = []
        for page in reader.pages:
            try:
                t = page.extract_text()
                if t:
                    texts.append(t)
            except Exception:
                continue
        return "\n".join(texts)
    except Exception:
        return ""


def extract_text_from_txt(txt_bytes: bytes) -> str:
    try:
        return txt_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""
