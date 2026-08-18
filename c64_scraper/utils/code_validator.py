import re
from typing import Dict, Any, List, Tuple

class CodeSyntaxValidator:
    """
    Validates formal correctness of Commodore 64 Assembly (6502/6510)
    and C64 BASIC code blocks.
    """

    STD_6502_OPCODES = {
        "lda", "sta", "ldx", "stx", "ldy", "sty", "jsr", "rts", "jmp",
        "beq", "bne", "cmp", "cpx", "cpy", "inc", "dec", "adc", "sbc",
        "pha", "pla", "php", "plp", "asl", "lsr", "rol", "ror", "and",
        "ora", "eor", "bit", "sec", "clc", "sed", "cld", "sei", "cli",
        "tax", "txa", "tay", "tya", "tsx", "txs", "nop", "brk", "rti"
    }

    ILLEGAL_6510_OPCODES = {
        "anc", "rla", "sre", "rra", "sax", "lax", "dcp", "isc", "slo",
        "ahx", "alr", "arr", "tas", "las", "shx", "shy", "xaa", "axs", "kil"
    }

    ASM_DIRECTIVES = {
        ".org", "*=", "* =", ".pc", ".byte", ".word", ".text", ".db", ".dw",
        ".equ", ".var", ".label", ".const", ".import", ".segment", ".struct",
        ".macro", ".pseudopc", "!to", "!zone", "!byte", "!word", "!src", "!fill",
        "!for", "!pseudopc", "!align", "!convtab", "!8", "!16", "!32", "!ct", "!scr",
        "processor", "dc.b", "dc.w", "ds.b", "seg.u", "seg", ".proc", ".endproc"
    }

    BASIC_KEYWORDS = {
        "print", "goto", "if", "then", "poke", "peek", "next", "for", "data", "rem",
        "gosub", "return", "input", "dim", "read", "restore", "sys", "cont", "list",
        "run", "clr", "load", "save", "verify", "new", "on", "get", "usr", "fre",
        "pos", "sqr", "rnd", "log", "exp", "cos", "sin", "tan", "atn", "peek", "len",
        "str$", "val", "asc", "chr$", "left$", "right$", "mid$"
    }

    @classmethod
    def validate_assembly(cls, code_text: str) -> Dict[str, Any]:
        """
        Validates 6502/6510 Assembly code syntax.
        Returns a dict with validation status, ratio, and detected issues.
        """
        if not code_text or not code_text.strip():
            return {"is_valid": False, "valid_ratio": 0.0, "issues": ["Empty code block"], "illegal_opcodes_found": []}

        lines = [line.strip() for line in code_text.splitlines() if line.strip()]
        if not lines:
            return {"is_valid": False, "valid_ratio": 0.0, "issues": ["No non-empty lines"], "illegal_opcodes_found": []}

        valid_count = 0
        issues = []
        illegal_opcodes = []

        for idx, line in enumerate(lines, 1):
            # Strip comments
            clean_line = re.sub(r'(;|//|\*).*$', '', line).strip()
            if not clean_line:
                valid_count += 1
                continue

            # Check label definition (e.g. label:, .label, or label = $C000)
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*:\s*$', clean_line) or re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[\$0-9a-fA-F]+', clean_line):
                valid_count += 1
                continue

            # Check assembler directives
            lower_line = clean_line.lower()
            if any(lower_line.startswith(d) for d in cls.ASM_DIRECTIVES):
                valid_count += 1
                continue

            # Split line into tokens
            tokens = re.split(r'\s+', clean_line)
            # Optional label at start
            first_token = tokens[0].rstrip(':').lower()

            if first_token in cls.STD_6502_OPCODES:
                valid_count += 1
            elif first_token in cls.ILLEGAL_6510_OPCODES:
                valid_count += 1
                illegal_opcodes.append(first_token)
            elif len(tokens) > 1 and tokens[1].lower() in cls.STD_6502_OPCODES:
                valid_count += 1
            elif len(tokens) > 1 and tokens[1].lower() in cls.ILLEGAL_6510_OPCODES:
                valid_count += 1
                illegal_opcodes.append(tokens[1].lower())
            else:
                # Direct assignment, EQU, or macro call
                if "=" in clean_line or "equ" in lower_line or clean_line.startswith(".") or clean_line.startswith("!"):
                    valid_count += 1
                else:
                    issues.append(f"Line {idx}: Unrecognized assembly instruction '{clean_line}'")

        valid_ratio = round(valid_count / len(lines), 2)
        is_valid = valid_ratio >= 0.70

        return {
            "is_valid": is_valid,
            "valid_ratio": valid_ratio,
            "issues": issues,
            "illegal_opcodes_found": sorted(list(set(illegal_opcodes)))
        }

    @classmethod
    def validate_basic(cls, code_text: str) -> Dict[str, Any]:
        """
        Validates C64 BASIC code syntax.
        Checks for line numbers and valid keywords.
        """
        if not code_text or not code_text.strip():
            return {"is_valid": False, "valid_ratio": 0.0, "issues": ["Empty code block"]}

        lines = [line.strip() for line in code_text.splitlines() if line.strip()]
        if not lines:
            return {"is_valid": False, "valid_ratio": 0.0, "issues": ["No non-empty lines"]}

        valid_count = 0
        issues = []

        for idx, line in enumerate(lines, 1):
            line_lower = line.lower()
            # Standard C64 BASIC line format: 10 PRINT "HELLO"
            has_line_number = re.match(r'^\d{1,5}\s+', line)

            has_keyword = any(re.search(rf'\b{kw}\b', line_lower) for kw in cls.BASIC_KEYWORDS)

            if has_line_number or has_keyword:
                valid_count += 1
            else:
                issues.append(f"Line {idx}: Missing line number or valid BASIC keyword: '{line}'")

        valid_ratio = round(valid_count / len(lines), 2)
        is_valid = valid_ratio >= 0.70

        return {
            "is_valid": is_valid,
            "valid_ratio": valid_ratio,
            "issues": issues
        }

    @classmethod
    def validate_code(cls, code_text: str, lang: str = "asm") -> Dict[str, Any]:
        """Generic validator entrypoint delegating by language."""
        if lang in ["asm", "assembly"]:
            return cls.validate_assembly(code_text)
        elif lang in ["basic"]:
            return cls.validate_basic(code_text)
        return {"is_valid": True, "valid_ratio": 1.0, "issues": []}
