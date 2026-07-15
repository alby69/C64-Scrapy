import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pdf_processing.pdf2marker import PDF2MarkConverter


class TestPDF2MarkConverter:
    def test_init_default_output(self):
        conv = PDF2MarkConverter()
        assert conv.output_dir == "output"

    def test_init_custom_output(self):
        conv = PDF2MarkConverter("/tmp/test_pdf")
        assert conv.output_dir == "/tmp/test_pdf"

    def test_marker_availability(self):
        from pdf_processing.pdf2marker import MARKER_AVAILABLE

        assert MARKER_AVAILABLE is False  # In test env, marker-pdf is not installed

    def test_strip_markdown_bold(self):
        text = PDF2MarkConverter._strip_markdown("**bold** text")
        assert "bold" in text
        assert "**" not in text

    def test_strip_markdown_italic(self):
        text = PDF2MarkConverter._strip_markdown("_italic_ text")
        assert "italic" in text
        assert "_" not in text

    def test_strip_markdown_links(self):
        text = PDF2MarkConverter._strip_markdown("[text](url) link")
        assert "text" in text
        assert "url" not in text

    def test_strip_markdown_code_blocks(self):
        text = PDF2MarkConverter._strip_markdown("```code``` pas")
        assert "pas" in text

    def test_convert_with_fallback(self):
        import fitz

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = os.path.join(tmp, "test.pdf")
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "Hello World")
            doc.save(pdf_path)
            doc.close()

            conv = PDF2MarkConverter(tmp)
            result = conv.convert(pdf_path)
            assert result["status"] == "ok"
            assert os.path.exists(result["text"])
