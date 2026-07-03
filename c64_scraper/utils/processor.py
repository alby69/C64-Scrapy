import re
import trafilatura

class ContentProcessor:
    """Utility class to process and clean scraped content."""

    @staticmethod
    def extract_markdown(html: str, url: str) -> str:
        """Extracts markdown content from HTML using trafilatura."""
        return trafilatura.extract(
            html,
            url=url,
            output_format="markdown",
            include_links=True,
            include_images=True,
            include_tables=True,
            favor_recall=True,
        )

    @staticmethod
    def clean_title(title: str, site_suffix: str = "") -> str:
        """Cleans the page title by removing site-specific suffixes."""
        if not title:
            return ""
        if site_suffix and site_suffix in title:
            title = title.split(site_suffix)[0]
        return title.strip()

    @staticmethod
    def detect_language(code_text: str) -> str:
        """Heuristically detects if code is BASIC or Assembly."""
        code_lower = code_text.lower()
        basic_keywords = ["print", "goto", "if", "then", "poke", "peek", "next", "for", "data", "rem"]
        if any(re.search(rf"\b{k}\b", code_lower) for k in basic_keywords):
            return "basic"

        # Assembly 6502 mnemonics
        asm_keywords = [
            "lda", "sta", "ldx", "stx", "ldy", "sty", "jsr", "rts", "jmp",
            "beq", "bne", "cmp", "cpx", "cpy", "inc", "dec", "adc", "sbc"
        ]
        if any(re.search(rf"\b{k}\b", code_lower) for k in asm_keywords):
            return "asm"

        return ""
