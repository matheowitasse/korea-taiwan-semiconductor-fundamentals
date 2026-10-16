"""Plain-text extraction for Korean government documents: HWP (v5), HWPX and PDF.

HWP 5.0 is an OLE compound file. Body text lives in BodyText/Section{n} streams, usually raw-deflate
compressed, as a sequence of records. Paragraph text is in HWPTAG_PARA_TEXT records (UTF-16LE with
embedded control characters). Table cells are paragraphs too, so tables come out as consecutive lines.
"""

import re
import struct
import zipfile
import zlib
from pathlib import Path

import olefile
from pypdf import PdfReader

HWPTAG_PARA_TEXT = 67
# Control characters that occupy 8 UTF-16 code units (the char + 7 units of payload)
EXTENDED_CTRL = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}


def _para_text(data: bytes) -> str:
    units = struct.unpack(f"<{len(data) // 2}H", data[: len(data) // 2 * 2])
    kept, i = [], 0
    while i < len(units):
        c = units[i]
        if c in EXTENDED_CTRL:
            i += 8
            continue
        if c in (10, 13):
            kept.append(10)
        elif c >= 32:
            kept.append(c)
        i += 1
    # Decode as a whole so surrogate pairs (characters outside the BMP) are combined correctly
    return struct.pack(f"<{len(kept)}H", *kept).decode("utf-16-le", errors="replace")


def hwp_text(path: Path) -> str:
    ole = olefile.OleFileIO(str(path))
    header = ole.openstream("FileHeader").read()
    compressed = bool(struct.unpack("<I", header[36:40])[0] & 1)
    sections = sorted((s for s in ole.listdir() if s[0] == "BodyText"), key=lambda s: int(s[1].replace("Section", "")))
    lines = []
    for s in sections:
        raw = ole.openstream(s).read()
        data = zlib.decompress(raw, -15) if compressed else raw
        pos = 0
        while pos + 4 <= len(data):
            (h,) = struct.unpack("<I", data[pos : pos + 4])
            tag, size = h & 0x3FF, (h >> 20) & 0xFFF
            pos += 4
            if size == 0xFFF:
                (size,) = struct.unpack("<I", data[pos : pos + 4])
                pos += 4
            if tag == HWPTAG_PARA_TEXT:
                lines.append(_para_text(data[pos : pos + size]))
            pos += size
    ole.close()
    return "\n".join(lines)


def hwpx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        names = sorted((n for n in z.namelist() if re.match(r"Contents/section\d+\.xml", n)),
                       key=lambda n: int(re.findall(r"\d+", n)[-1]))
        paras = []
        for n in names:
            xml = z.read(n).decode("utf-8")
            for p in re.findall(r"<hp:p\b.*?</hp:p>", xml, flags=re.S):
                paras.append("".join(re.findall(r"<hp:t\b[^>]*>(.*?)</hp:t>", p, flags=re.S)))
    return "\n".join(paras)


def pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def document_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".hwp":
        return hwp_text(path)
    if ext == ".hwpx":
        return hwpx_text(path)
    if ext == ".pdf":
        return pdf_text(path)
    raise ValueError(f"unsupported file type: {path}")
