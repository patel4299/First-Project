from __future__ import annotations

from pathlib import Path


class SimplePDF:
    def __init__(self, title: str, lines: list[str]):
        self.title = title
        self.lines = lines

    def build(self) -> bytes:
        objects: list[bytes] = []
        header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
        text_lines = ["BT", "/F1 11 Tf", "50 760 Td"]
        for line in self.lines:
            safe_line = line.replace("(", "[").replace(")", "]")
            text_lines.append(f"({safe_line}) Tj")
            text_lines.append("0 -14 Td")
        text_lines.append("ET")
        text_stream = "\n".join(text_lines).encode("utf-8")
        objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        objects.append(
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        )
        objects.append(
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        )
        objects.append(
            b"4 0 obj\n<< /Length "
            + str(len(text_stream)).encode("utf-8")
            + b" >>\nstream\n"
            + text_stream
            + b"\nendstream\nendobj\n"
        )
        objects.append(
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        )
        xref_positions = [len(header)]
        body = b""
        for obj in objects:
            body += obj
            xref_positions.append(len(header) + len(body))
        xref = [b"xref\n0 6\n0000000000 65535 f \n"]
        for pos in xref_positions[:-1]:
            xref.append(f"{pos:010d} 00000 n \n".encode("utf-8"))
        xref_bytes = b"".join(xref)
        trailer = (
            b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
            + str(len(header) + len(body)).encode("utf-8")
            + b"\n%%EOF\n"
        )
        return header + body + xref_bytes + trailer


def write_invoice_pdf(path: Path, title: str, lines: list[str]) -> None:
    pdf = SimplePDF(title, lines).build()
    path.write_bytes(pdf)
