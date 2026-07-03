from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordInfo:
    word: str
    category: str
    meaning: str
    aliases: tuple[str, ...] = ()


# PL/I does not reserve these words globally. They are recognized by context.
KEYWORD_CATALOG: dict[str, KeywordInfo] = {}


def _add(word: str, category: str, meaning: str, *aliases: str) -> None:
    existing = KEYWORD_CATALOG.get(word)
    if existing:
        category = f"{existing.category}; {category}"
        meaning = f"{existing.meaning} Also: {meaning}"
        aliases = existing.aliases + aliases
    info = KeywordInfo(word, category, meaning, aliases)
    KEYWORD_CATALOG[word] = info
    for alias in aliases:
        existing_alias = KEYWORD_CATALOG.get(alias)
        if existing_alias:
            alias_category = f"{existing_alias.category}; {category}"
            alias_meaning = f"{existing_alias.meaning} Also: {meaning}"
            KEYWORD_CATALOG[alias] = KeywordInfo(alias, alias_category, alias_meaning, ())
        else:
            KEYWORD_CATALOG[alias] = KeywordInfo(alias, category, meaning, ())


_add("ALLOCATE", "storage statement", "Allocates controlled or based storage.", "ALLOC")
_add("BEGIN", "structural statement", "Starts a begin block with its own scope.")
_add("CALL", "control statement", "Invokes a procedure and ignores any returned value.")
_add("CLOSE", "I/O statement", "Closes a file.")
_add("DECLARE", "declaration statement", "Declares names and their attributes.", "DCL")
_add("DEFAULT", "declaration statement", "Sets default declaration attributes.", "DFT")
_add("DELETE", "record I/O statement", "Deletes the current keyed record.")
_add("DO", "structural statement", "Starts a group or an iterative loop.")
_add("ELSE", "control keyword", "Introduces the false branch of an IF statement.")
_add("END", "structural statement", "Ends a DO group, block, procedure, package, or select group.")
_add("ENTRY", "structural statement", "Declares an alternate entry point.")
_add("FORMAT", "declaration statement", "Declares a format item for edit-directed I/O.")
_add("FREE", "storage statement", "Releases controlled or based storage.")
_add("GET", "stream I/O statement", "Reads stream input.")
_add("GO", "control statement", "First word of GO TO branch statement.")
_add("GOTO", "control statement", "Branches to a label.", "GO TO")
_add("IF", "control statement", "Conditionally executes a statement or group.")
_add("LOCATE", "record I/O statement", "Positions output for record creation.")
_add("ON", "condition statement", "Establishes a condition handler.")
_add("OPEN", "I/O statement", "Opens a file.")
_add("PROCEDURE", "structural statement", "Starts a procedure.", "PROC")
_add("PUT", "stream I/O statement", "Writes stream output.")
_add("READ", "record I/O statement", "Reads a record.")
_add("RETURN", "control statement", "Returns from a procedure.")
_add("REVERT", "condition statement", "Cancels an ON-unit for a condition.")
_add("REWRITE", "record I/O statement", "Rewrites a record.")
_add("SELECT", "control statement", "Starts a multi-way selection group.")
_add("SIGNAL", "condition statement", "Raises a condition.")
_add("STOP", "control statement", "Terminates program execution.")
_add("THEN", "control keyword", "Introduces the true branch of an IF statement.")
_add("TO", "control keyword", "Used in GO TO and loop ranges.")
_add("WRITE", "record I/O statement", "Writes a record.")

_add("ALIGNED", "data attribute", "Requests aligned storage.")
_add("AREA", "data attribute", "Declares an area for based storage.")
_add("BINARY", "data attribute", "Specifies binary arithmetic representation.", "BIN")
_add("BIT", "data attribute", "Declares a bit string.")
_add("CHARACTER", "data attribute", "Declares a character string.", "CHAR")
_add("COMPLEX", "data attribute", "Specifies a complex arithmetic value.", "CPLX")
_add("DECIMAL", "data attribute", "Specifies decimal arithmetic representation.", "DEC")
_add("FILE", "data attribute", "Declares a file constant or variable.")
_add("FIXED", "data attribute", "Specifies fixed-point arithmetic scale.")
_add("FLOAT", "data attribute", "Specifies floating-point arithmetic scale.")
_add("LABEL", "data attribute", "Declares a label variable.")
_add("MEMBER", "data attribute", "Declares a structure member attribute.")
_add("NONVARYING", "data attribute", "Declares a fixed-length string.", "NONVAR")
_add("OFFSET", "data attribute", "Declares an offset locator.")
_add("PICTURE", "data attribute", "Declares picture-formatted data.", "PIC")
_add("POINTER", "data attribute", "Declares a pointer locator.", "PTR")
_add("STRUCTURE", "data attribute", "Declares a structure.")
_add("UNALIGNED", "data attribute", "Requests unaligned storage.", "UNAL")
_add("VARYING", "data attribute", "Declares a varying-length string.", "VAR")

_add("DIRECT", "I/O attribute", "Declares direct file access.")
_add("ENVIRONMENT", "I/O attribute", "Supplies implementation file options.", "ENV")
_add("INPUT", "I/O attribute", "Declares input access.")
_add("KEYED", "I/O attribute", "Declares keyed access.")
_add("OUTPUT", "I/O attribute", "Declares output access.")
_add("PRINT", "I/O attribute", "Declares print-oriented stream output.")
_add("RECORD", "I/O attribute", "Declares record-oriented I/O.")
_add("SEQUENTIAL", "I/O attribute", "Declares sequential access.", "SEQL")
_add("STREAM", "I/O attribute", "Declares stream-oriented I/O.")
_add("UPDATE", "I/O attribute", "Declares update access.")

_add("AUTOMATIC", "storage attribute", "Allocates storage on block entry.", "AUTO")
_add("BASED", "storage attribute", "Declares storage addressed by a locator.")
_add("BUILTIN", "attribute", "Declares a built-in function name.")
_add("CONDITION", "condition attribute", "Declares a condition name.", "COND")
_add("CONSTANT", "attribute", "Declares an immutable value.")
_add("CONTROLLED", "storage attribute", "Declares explicitly allocated stack-like storage.", "CTL")
_add("DEFINED", "storage attribute", "Overlays storage on another variable.", "DEF")
_add("EXTERNAL", "linkage attribute", "Declares external linkage.", "EXT")
_add("GENERIC", "attribute", "Declares a generic procedure name.")
_add("INITIAL", "attribute", "Supplies initial values.", "INIT")
_add("INTERNAL", "linkage attribute", "Declares internal linkage.", "INT")
_add("LIKE", "attribute", "Copies attributes from another declaration.")
_add("LOCAL", "storage attribute", "Declares package-local scope in modern PL/I.")
_add("OPTIONS", "attribute", "Supplies procedure or file options.")
_add("PARAMETER", "attribute", "Declares a procedure parameter.", "PARM")
_add("POSITION", "attribute", "Sets bit or character position.", "POS")
_add("STATIC", "storage attribute", "Allocates persistent storage.")
_add("VARIABLE", "attribute", "Marks an entry or condition as variable.")

_add("BY", "iteration keyword", "Specifies DO-loop step.")
_add("FOREVER", "iteration keyword", "Specifies an unbounded DO loop.")
_add("FROM", "I/O option", "Specifies a source value or buffer.")
_add("KEY", "I/O option", "Specifies a record key.")
_add("LIST", "I/O option", "Selects list-directed GET or PUT.")
_add("REPEAT", "iteration keyword", "Specifies repeated loop evaluation.")
_add("SKIP", "I/O option", "Advances lines in stream I/O.")
_add("UNTIL", "iteration keyword", "Terminates a loop after a condition becomes true.")
_add("WHILE", "iteration keyword", "Continues a loop while a condition is true.")

_add("ANYCONDITION", "condition", "Matches any signaled condition.")
_add("AREA", "condition", "Raised for area storage problems.")
_add("ATTENTION", "condition", "Raised for attention interrupts.")
_add("CONVERSION", "condition", "Raised for conversion errors.", "CONV")
_add("ENDFILE", "condition", "Raised when end of file is reached.")
_add("ENDPAGE", "condition", "Raised when a page boundary is reached.")
_add("ERROR", "condition", "Generic error condition.")
_add("FINISH", "condition", "Raised during program termination.")
_add("FIXEDOVERFLOW", "condition", "Raised for fixed-point overflow.", "FOFL")
_add("KEY", "condition", "Raised for keyed I/O errors.")
_add("NAME", "condition", "Raised for name-related errors.")
_add("OVERFLOW", "condition", "Raised for arithmetic overflow.", "OFL")
_add("RECORD", "condition", "Raised for record I/O errors.")
_add("SIZE", "condition", "Raised when size constraints are violated.")
_add("STRINGRANGE", "condition", "Raised for invalid string bounds.")
_add("STRINGSIZE", "condition", "Raised for string size errors.")
_add("SUBSCRIPTRANGE", "condition", "Raised for invalid array subscripts.")
_add("TRANSMIT", "condition", "Raised for transmission errors.")
_add("UNDEFINEDFILE", "condition", "Raised for undefined file use.", "UNDF")
_add("UNDERFLOW", "condition", "Raised for arithmetic underflow.", "UFL")
_add("ZERODIVIDE", "condition", "Raised for division by zero.", "ZDIV")

_add("ACTIVATE", "preprocessor statement", "Makes a preprocessor name active.")
_add("DEACTIVATE", "preprocessor statement", "Makes a preprocessor name inactive.")
_add("INCLUDE", "preprocessor statement", "Includes source text.")
_add("ITERATE", "preprocessor statement", "Continues a preprocessor or loop iteration.")
_add("LEAVE", "preprocessor statement", "Exits a loop.")
_add("NOTE", "preprocessor statement", "Emits a preprocessor diagnostic.")
_add("PAGE", "listing-control statement", "Starts a new listing page.")
_add("POP", "listing-control statement", "Restores listing-control state.")
_add("PRINT", "listing-control statement", "Enables listing output.")
_add("PUSH", "listing-control statement", "Saves listing-control state.")
_add("REPLACE", "preprocessor statement", "Defines immediate text replacement.")
_add("XINCLUDE", "preprocessor statement", "Includes source text only once.")


def keyword_info(word: str) -> KeywordInfo | None:
    return KEYWORD_CATALOG.get(word.upper())
