import pytest
from c64_scraper.utils.code_validator import CodeSyntaxValidator

def test_validate_assembly_valid_standard():
    code = """
    * = $C000
    start:
        lda #$00
        sta $D020
        sta $D021
        rts
    """
    res = CodeSyntaxValidator.validate_assembly(code)
    assert res["is_valid"] is True
    assert res["valid_ratio"] >= 0.8
    assert len(res["illegal_opcodes_found"]) == 0

def test_validate_assembly_illegal_opcodes():
    code = """
    * = $C000
    lax $10
    sax $20
    dcp $30
    rts
    """
    res = CodeSyntaxValidator.validate_assembly(code)
    assert res["is_valid"] is True
    assert "lax" in res["illegal_opcodes_found"]
    assert "sax" in res["illegal_opcodes_found"]

def test_validate_assembly_kickasm_directives():
    code = """
    .pc = $0801 "Basic Upstart"
    :BasicUpstart(main)
    .pc = $0810 "Main"
    main:
        lda #0
        sta $d020
        rts
    """
    res = CodeSyntaxValidator.validate_assembly(code)
    assert res["is_valid"] is True

def test_validate_basic_valid():
    code = """
    10 PRINT "HELLO WORLD"
    20 POKE 53280, 0
    30 GOTO 10
    """
    res = CodeSyntaxValidator.validate_basic(code)
    assert res["is_valid"] is True
    assert res["valid_ratio"] == 1.0

def test_validate_generic_entrypoint():
    asm_res = CodeSyntaxValidator.validate_code("lda #$00\nrts", lang="asm")
    basic_res = CodeSyntaxValidator.validate_code("10 PRINT 1", lang="basic")
    assert asm_res["is_valid"] is True
    assert basic_res["is_valid"] is True
