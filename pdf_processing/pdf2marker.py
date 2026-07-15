import os
import json
import logging
import re
import time
from pathlib import Path

log = logging.getLogger("pdf2mark")

try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False


class PDF2MarkConverter:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def convert(self, pdf_path: str, base_name: str = "") -> dict:
        if MARKER_AVAILABLE:
            return self._convert_with_marker(pdf_path, base_name)
        return self._convert_with_fitz(pdf_path, base_name)

    def _convert_with_marker(self, pdf_path: str, base_name: str) -> dict:
        start = time.time()
        converter = PdfConverter(artifact_dict=create_model_dict())
        rendered = converter(pdf_path)
        md_text, md_metadata, md_images = text_from_rendered(rendered)

        name = base_name or Path(pdf_path).stem
        md_path = os.path.join(self.output_dir, f"{name}.md")
        txt_path = os.path.join(self.output_dir, f"{name}.txt")
        meta_path = os.path.join(self.output_dir, f"{name}.meta.json")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "source": pdf_path,
                    "pages": md_metadata.get("page_stats", []),
                    "toc": md_metadata.get("table_of_contents", []),
                    "total_time": round(time.time() - start, 2),
                },
                f,
                indent=2,
            )

        plain_text = self._strip_markdown(md_text)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(plain_text)

        return {
            "status": "ok",
            "markdown": md_path,
            "text": txt_path,
            "metadata": meta_path,
            "engine": "marker-pdf",
            "total_time": round(time.time() - start, 2),
        }

    def _convert_with_fitz(self, pdf_path: str, base_name: str) -> dict:
        import fitz

        start = time.time()
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            blocks = page.get_text("blocks")
            block_text = "\n".join(b[4] for b in blocks)
            full_text += block_text + "\n\f"
        doc.close()

        name = base_name or Path(pdf_path).stem
        txt_path = os.path.join(self.output_dir, f"{name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        return {
            "status": "ok",
            "text": txt_path,
            "engine": "fitz (PyMuPDF)",
            "total_time": round(time.time() - start, 2),
        }

    @staticmethod
    def _strip_markdown(md_text: str) -> str:
        text = re.sub(r"```.*?```", "", md_text, flags=re.DOTALL)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]*)\]\(.*?\)", r"\1", text)
        text = re.sub(r"[#*_~`>|]{1,}", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def download_from_archive(self, identifier: str, output_dir: str = "") -> str:
        import requests

        dest = output_dir or self.output_dir
        os.makedirs(dest, exist_ok=True)
        pdf_path = os.path.join(dest, f"{identifier}.pdf")

        if os.path.exists(pdf_path):
            return pdf_path

        url = f"https://archive.org/download/{identifier}/{identifier}.pdf"
        log.info(f"  Downloading {url} ...")
        r = requests.get(url, stream=True, timeout=300)
        r.raise_for_status()
        with open(pdf_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return pdf_path

    def process(self, identifier: str) -> dict:
        pdf_path = self.download_from_archive(identifier)
        return self.convert(pdf_path, identifier)


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m pdf_processing.pdf2marker <input.pdf> <output>")
        print("  output: path without extension (produces .md, .txt, .meta.json)")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dest = sys.argv[2]

    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    conv = PDF2MarkConverter(output_dir=os.path.dirname(output_dest) or ".")
    result = conv.convert(pdf_path, Path(output_dest).stem)
    if result["status"] == "ok":
        print(f"[OK] {result['engine']} - {result['total_time']:.1f}s")
        for key in ("text", "markdown", "metadata"):
            if key in result:
                print(f"  {key}: {result[key]}")
    else:
        print(f"[ERR] {result.get('error', 'unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
