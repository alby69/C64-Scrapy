import re
import trafilatura

class ContentProcessor:
    """Utility class to process, clean, and classify scraped content."""

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

    @staticmethod
    def classify_document(html_text: str, body_md: str, url: str, title: str, spider_name: str = "") -> dict:
        """Enriches the document with semantic tags and categories."""
        text_lower = (title + " " + (body_md or "")).lower()
        url_lower = url.lower()

        # 1. Classify Category
        category = "reference"
        if spider_name == "dustlayer" or "tutorial" in url_lower or "tutorial" in text_lower or "beginner" in text_lower:
            category = "tutorial"
        elif spider_name == "github" or "disassembly" in url_lower or "source code" in text_lower or "source-code" in text_lower:
            category = "source-code"
        elif spider_name == "archiveorg" or "manual" in url_lower or "manual" in text_lower or "book" in text_lower:
            category = "manual"
        elif "deep_dives" in url_lower or "deep-dive" in url_lower or "deep dive" in text_lower:
            category = "deep-dive"
        elif "tool" in url_lower or "assembler" in text_lower or "emulator" in text_lower:
            category = "tool"
        elif spider_name == "bbcelite" and "index" in url_lower:
            category = "reference"
        elif "memory" in url_lower or "register" in url_lower or "memory map" in text_lower or "map" in url_lower:
            category = "reference"

        # 2. Detect Hardware and Topics
        topics = []
        hardware = []

        hardware_map = {
            "vic-ii": ["vic-ii", "vic2", "vic 2", "graphics chip", "d020", "d021", "raster", "sprite", "border color"],
            "sid": ["sid", "sound chip", "music", "audio", "voice", "d400", "waveform", "envelope"],
            "cia": ["cia", "complex interface adapter", "dc00", "dc01", "timer", "keyboard", "joystick"],
            "cpu": ["6502", "6510", "processor", "accumulator", "registers", "opcode"],
            "kernal": ["kernal", "rom", "chrout", "getin", "ffd2", "ffe4"],
            "basic rom": ["basic interpreter", "basic rom", "token", "a7ae", "e37b"]
        }

        for hw, kw_list in hardware_map.items():
            if any(kw in text_lower for kw in kw_list):
                hardware.append(hw.upper())

        topic_keywords = {
            "raster interrupts": ["raster interrupt", "raster line", "raster trigger", "d012", "irq", "interrupt handler"],
            "sprite programming": ["sprite", "multiplexer", "sprite collision", "d015", "pointer"],
            "graphics": ["multicolor", "hi-res", "high resolution", "bitmap", "screen memory", "character generator"],
            "sound generation": ["music player", "sid sound", "envelope", "frequency", "pulse width"],
            "input handling": ["joystick", "keyboard matrix", "dc00", "dc01", "fire button"],
            "memory management": ["memory configuration", "ram/rom", "bank switching", "0001", "zero page"],
            "assembly": ["assembly", "assembler", "lda", "sta", "jsr", "rts", "instruction set"],
            "basic": ["basic", "poke", "peek", "sys", "line number", "syntax"]
        }

        for topic, kw_list in topic_keywords.items():
            if any(kw in text_lower for kw in kw_list):
                topics.append(topic)

        # 3. Guess Difficulty
        difficulty = "intermediate"
        if any(kw in text_lower for kw in ["beginner", "first step", "simple", "easy", "for beginners", "introduction"]):
            difficulty = "beginner"
        elif any(kw in text_lower for kw in ["interrupt", "raster", "multiplexer", "illegal opcodes", "timing", "custom loader", "rasterlock"]):
            difficulty = "advanced"

        # 4. Language detection
        language = "none"
        has_basic = any(kw in text_lower for kw in ["poke", "peek", "sys", "rem", "goto", "gosub"])
        has_asm = any(kw in text_lower for kw in ["lda", "sta", "ldx", "stx", "jsr", "rts"])
        if has_basic and has_asm:
            language = "mixed"
        elif has_asm:
            language = "assembly"
        elif has_basic:
            language = "basic"

        # 5. Related
        related = []
        if "VIC-II" in hardware or "raster interrupts" in topics or "sprite programming" in topics:
            related.extend(["vic-ii-registers", "sprite-programming", "raster-interrupts"])
        if "SID" in hardware or "sound generation" in topics:
            related.extend(["sid-registers", "sound-programming", "music-player"])
        if "CIA" in hardware or "input handling" in topics:
            related.extend(["cia-registers", "keyboard-handling", "joystick-reading"])
        if "KERNAL" in hardware:
            related.extend(["kernal-routines", "memory-map"])
        related = list(set(related))

        return {
            "category": category,
            "topics": list(set(topics)),
            "difficulty": difficulty,
            "language": language,
            "hardware": list(set(hardware)),
            "related": related
        }

    @staticmethod
    def detect_assembly_dialect(code_text: str) -> str:
        """Heuristically detects the Assembly dialect/compiler used."""
        code_lower = code_text.lower()
        if any(kw in code_lower for kw in [".pc", ".var", ".filenamespace", ".label", ".const", "import"]):
            return "Kick Assembler"
        if any(kw in code_lower for kw in ["!to", "!zone", "!byte", "!src", "!fill"]):
            return "ACME"
        if any(kw in code_lower for kw in ["processor 6502", "org", "dc.b"]):
            return "DASM"
        if any(kw in code_lower for kw in ["* =", "*="]):
            return "Turbo Assembler / Generic"
        return "Generic Assembly"

    @staticmethod
    def extract_routines_from_code(code_text: str, source_url: str = "") -> list:
        """
        Parses assembly code block to extract labels, descriptions from comments,
        and starting/loading addresses if found.
        """
        routines = []
        lines = code_text.splitlines()

        current_address = None
        # Try to find load address, e.g., * = $C000 or .pc = $C000
        for line in lines:
            m = re.search(r'(?:\*|\.pc)\s*=\s*\$?([0-9a-fA-F]+)', line)
            if m:
                current_address = "$" + m.group(1)
                break

        for i, line in enumerate(lines):
            # standard 6502 labels match label_name:
            match = re.match(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*):', line)
            if not match:
                # check starting in col 1 followed by spaces/instruction
                match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s+[a-zA-Z]{3}\b', line)

            if match:
                label = match.group(1)
                # avoid instruction false positives
                if label.lower() in [
                    "lda", "sta", "ldx", "stx", "ldy", "sty", "jsr", "rts", "jmp", "beq", "bne", "cmp",
                    "cpx", "cpy", "inc", "dec", "adc", "sbc", "pha", "pla", "php", "plp", "asl", "lsr",
                    "rol", "ror", "and", "ora", "eor", "bit", "sec", "clc", "sed", "cld", "sei", "cli",
                    "tax", "txa", "tay", "tya", "tsx", "txs"
                ]:
                    continue

                # Retrieve comments preceding the label
                comments = []
                # Look up to 5 lines backward for comments
                for j in range(max(0, i-5), i):
                    prev_line = lines[j].strip()
                    if prev_line.startswith(";") or prev_line.startswith("//") or prev_line.startswith("*"):
                        comments.append(prev_line.lstrip(";/* \t"))

                description = " ".join(comments).strip() or "No description available"

                routines.append({
                    "name": label,
                    "address": current_address or "unknown",
                    "description": description,
                    "source_url": source_url
                })
        return routines
