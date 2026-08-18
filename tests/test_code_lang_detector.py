import pytest
from c64_scraper.utils.code_lang_detector import CodeLanguageDetector

def test_detect_language_basic():
    basic_code = """
    10 PRINT "HELLO COMMODORE 64"
    20 FOR I = 1 TO 10
    30 POKE 53280, I
    40 NEXT I
    50 SYS 49152
    """
    assert CodeLanguageDetector.detect_language(basic_code) == "basic"

def test_detect_language_asm():
    asm_code = """
    * = $c000
    lda #$00
    sta $d020
    sta $d021
    rts
    """
    assert CodeLanguageDetector.detect_language(asm_code) == "asm"

def test_detect_language_hint():
    code = "some ambiguous block"
    assert CodeLanguageDetector.detect_language(code, hint="basic") == "basic"
    assert CodeLanguageDetector.detect_language(code, hint="6502") == "asm"

def test_detect_assembly_dialect():
    acme_code = "!to \"build/main.prg\", cbm\n!byte $00, $01"
    kick_code = ".pc = $0801 \"Basic Upstart\"\n.var x = 10"
    dasm_code = "PROCESSOR 6502\norg $c000\ndc.b 0"

    assert CodeLanguageDetector.detect_assembly_dialect(acme_code) == "ACME"
    assert CodeLanguageDetector.detect_assembly_dialect(kick_code) == "Kick Assembler"
    assert CodeLanguageDetector.detect_assembly_dialect(dasm_code) == "DASM"
