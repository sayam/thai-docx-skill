"""What the checker and the builder both know about WordprocessingML.

Element orders are the schema's sequences (ECMA-376 Part 1, CT_RPr / CT_Settings /
CT_PPr). Word ignores a property that stands in the wrong place without any error,
which is how a file can carry `w:szCs` and still size Thai wrongly — so order is
checked, not assumed.
"""

from __future__ import annotations

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def w(tag: str) -> str:
    return "{%s}%s" % (W, tag)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


# EG_RPrBase, in schema order.
RPR_ORDER = (
    "rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss "
    "imprint noProof snapToGrid vanish webHidden color spacing w kern position sz szCs "
    "highlight u effect bdr shd fitText vertAlign rtl cs em lang eastAsianLayout "
    "specVanish oMath rPrChange"
).split()

# CT_PPrBase, in schema order, then rPr, sectPr, pPrChange.
PPR_ORDER = (
    "pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr "
    "suppressLineNumbers pBdr shd tabs suppressAutoHyphens kinsoku wordWrap "
    "overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd snapToGrid "
    "spacing ind contextualSpacing mirrorIndents suppressOverlap jc textDirection "
    "textAlignment textboxTightWrap outlineLvl divId cnfStyle rPr sectPr pPrChange"
).split()

# CT_Settings, in schema order.
SETTINGS_ORDER = (
    "writeProtection view zoom removePersonalInformation removeDateAndTime "
    "doNotDisplayPageBoundaries displayBackgroundShape printPostScriptOverText "
    "printFractionalCharacterWidth printFormsData embedTrueTypeFonts embedSystemFonts "
    "saveSubsetFonts saveFormsData mirrorMargins alignBordersAndEdges "
    "bordersDoNotSurroundHeader bordersDoNotSurroundFooter gutterAtTop "
    "hideSpellingErrors hideGrammaticalErrors activeWritingStyle proofState formsDesign "
    "attachedTemplate linkStyles stylePaneFormatFilter stylePaneSortMethod documentType "
    "mailMerge revisionView trackRevisions doNotTrackMoves doNotTrackFormatting "
    "documentProtection autoFormatOverride styleLockTheme styleLockQFSet defaultTabStop "
    "autoHyphenation consecutiveHyphenLimit hyphenationZone doNotHyphenateCaps "
    "showEnvelope summaryLength clickAndTypeStyle defaultTableStyle evenAndOddHeaders "
    "bookFoldRevPrinting bookFoldPrinting bookFoldPrintingSheets "
    "drawingGridHorizontalSpacing drawingGridVerticalSpacing "
    "displayHorizontalDrawingGridEvery displayVerticalDrawingGridEvery "
    "doNotUseMarginsForDrawingGridOrigin drawingGridHorizontalOrigin "
    "drawingGridVerticalOrigin doNotShadeFormData noPunctuationKerning "
    "characterSpacingControl printTwoOnOne strictFirstAndLastChars noLineBreaksAfter "
    "noLineBreaksBefore savePreviewPicture doNotValidateAgainstSchema saveInvalidXml "
    "ignoreMixedContent alwaysShowPlaceholderText doNotDemarcateInvalidXml "
    "saveXmlDataOnly useXSLTWhenSaving saveThroughXslt showXMLTags "
    "alwaysMergeEmptyNamespace updateFields hdrShapeDefaults footnotePr endnotePr compat "
    "docVars rsids mathPr attachedSchema themeFontLang clrSchemeMapping "
    "doNotIncludeSubdocsInStats doNotAutoCompressPictures forceUpgrade captions "
    "readModeInkLockDown smartTagType schemaLibrary shapeDefaults doNotEmbedSmartTags "
    "decimalSymbol listSeparator"
).split()

# Invisible characters the builder never adds and the checker always reports.
INVISIBLE = {
    "​": "U+200B ZERO WIDTH SPACE",
    "‌": "U+200C ZERO WIDTH NON-JOINER",
    "‍": "U+200D ZERO WIDTH JOINER",
    "⁠": "U+2060 WORD JOINER",
    "﻿": "U+FEFF ZERO WIDTH NO-BREAK SPACE",
}

# Fonts known to carry Thai glyphs. A font outside this list is a warning, never a
# failure (ADR 0009): the list is what the maintainer knows, not what exists.
THAI_FONTS = frozenset(
    name.casefold()
    for name in (
        "TH Sarabun New", "TH SarabunPSK", "TH Sarabun PSK", "Sarabun",
        "TH Niramit AS", "TH Charm of AU", "TH Krub", "TH Mali Grade6", "TH KoHo",
        "TH Chakra Petch", "TH Baijam", "TH Fah kwang", "TH K2D July8", "TH Kodchasal",
        "TH Charmonman", "TH Srisakdi",
        "Angsana New", "AngsanaUPC", "Browallia New", "BrowalliaUPC", "Cordia New",
        "CordiaUPC", "DilleniaUPC", "EucrosiaUPC", "FreesiaUPC", "IrisUPC", "JasmineUPC",
        "KodchiangUPC", "LilyUPC", "Leelawadee", "Leelawadee UI", "Tahoma",
        "Microsoft Sans Serif", "Segoe UI", "Arial Unicode MS",
        "Noto Sans Thai", "Noto Serif Thai", "Noto Sans Thai Looped", "Noto Sans Thai UI",
        "Kanit", "Prompt", "Pridi", "Mitr", "Bai Jamjuree", "Chakra Petch", "Krub",
        "Niramit", "Athiti", "Taviraj", "Trirong", "Maitree", "Itim", "Pattaya",
        "Sriracha", "Charmonman", "Thasadith", "KoHo", "K2D", "Kodchasan", "Mali",
        "Srisakdi", "Chonburi", "Fahkwang", "Charm", "IBM Plex Sans Thai",
        "IBM Plex Sans Thai Looped", "Anuphan", "Libre Sarabun",
        "Garuda", "Kinnari", "Loma", "Norasi", "Purisa", "Sawasdee", "Tlwg Typist",
        "Tlwg Typo", "TlwgMono", "Umpush", "Waree", "Laksaman",
        "Thonburi", "Ayuthaya", "Krungthep", "Silom", "Sathu",
    )
)


def is_thai(ch: str) -> bool:
    return "฀" <= ch <= "๿"
