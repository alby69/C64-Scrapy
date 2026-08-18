import re
from typing import Dict, Any

class CodeLanguageDetector:
    """Detects programming language and assembly dialect for Commodore 64 code snippets."""

    BASIC_KEYWORDS = [
        "print", "goto", "if", "then", "poke", "peek", "next", "for", "data", "rem",
        "gosub", "return", "input", "dim", "read", "restore", "sys", "cont", "list",
        "run", "clr", "load", "save", "verify", "new"
    ]

    ASM_MNEMONICS = [
        "lda", "sta", "ldx", "stx", "ldy", "sty", "jsr", "rts", "jmp",
        "beq", "bne", "cmp", "cpx", "cpy", "inc", "dec", "adc", "sbc",
        "pha", "pla", "php", "plp", "asl", "lsr", "rol", "ror", "and",
        "ora", "eor", "bit", "sec", "clc", "sed", "cld", "sei", "cli",
        "tax", "txa", "tay", "tya", "tsx", "txs", "nop", "brk", "rti"
    ]

    @classmethod
    def detect_language(cls, code_text: str, hint: str = "") -> str:
        """
        Detects if code_text is BASIC, Assembly, or unknown.
        If a hint is provided (e.g. from wiki syntaxhighlight tag), it takes precedence if valid.
        """
        if hint:
            hint_clean = hint.strip().lower()
            if hint_clean in ["basic", "cbmbasic", "cbm-basic"]:
                return "basic"
            if hint_clean in ["asm", "assembly", "6502", "6510", "ca65", "dasm", "acme", "kickassembler"]:
                return "asm"

        if not code_text or not code_text.strip():
            return "unknown"

        code_lower = code_text.lower()

        # Check for line numbers at start of lines (typical for C64 BASIC)
        if re.search(r'^\s*\d{1,5}\s+[a-z]', code_lower, re.MULTILINE):
            return "basic"

        # Count BASIC keyword matches
        basic_score = sum(1 for k in cls.BASIC_KEYWORDS if re.search(rf"\b{k}\b", code_lower))

        # Count Assembly mnemonic matches
        asm_score = sum(1 for m in cls.ASM_MNEMONICS if re.search(rf"\b{m}\b", code_lower))

        # Additional ASM indicators like hex literals ($d020, #$00, %00000000)
        if re.search(r'#?\$[0-9a-f]{2,4}\b', code_lower) or re.search(r'\b(org|\* =|\*=|\!to|\.pc)\b', code_lower):
            asm_score += 2

        if basic_score > asm_score and basic_score > 0:
            return "basic"
        elif asm_score > basic_score and asm_score > 0:
            return "asm"
        elif basic_score > 0:
            return "basic"
        elif asm_score > 0:
            return "asm"

        return "unknown"

    @classmethod
    def detect_assembly_dialect(cls, code_text: str) -> str:
        """Heuristically detects the Assembly dialect/assembler used."""
        if not code_text:
            return "Generic Assembly"

        code_lower = code_text.lower()

        # Kick Assembler
        kick_keywords = [".pc", ".var", ".filenamespace", ".label", ".const", ".import", ".pseudopc", ".segment", ".struct", ".macro"]
        if any(kw in code_lower for kw in kick_keywords):
            return "Kick Assembler"

        # ACME
        acme_keywords = ["!to", "!zone", "!byte", "!src", "!fill", "!for", "!pseudopc", "!align", "!convtab", "!8", "!16", "!32", "!ct", "!scr"]
        if any(kw in code_lower for kw in acme_keywords):
            return "ACME"

        # DASM
        dasm_keywords = ["processor 6502", "dc.b", "dc.w", "ds.b", "seg.u", "seg "]
        if any(kw in code_lower for kw in dasm_keywords):
            return "DASM"

        # Turbo Assembler / Generic directives
        if any(kw in code_lower for kw in ["* =", "*=", ".byte", ".word", ".text", ".db", ".dw", ".equ"]):
            return "Turbo Assembler / Generic"

        return "Generic Assembly"
