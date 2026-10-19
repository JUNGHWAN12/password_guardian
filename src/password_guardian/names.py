"""Initials for today's TOP 10: three letters A-Z, checked against the booth's shared banned list.

The list is the same 119 entries as Clean Data Labeler and Data Packet Runner. Change all three games together.
A name is blocked only when it matches an entry exactly; the visitor just sees "use other letters".
"""
NAME_LENGTH = 3

BANNED_NAMES = frozenset({
    # 영어 욕설·비속어
    "FUK", "FUC", "FCK", "FUQ", "FUX", "FKU", "FKN", "FUU", "FFS", "FML", "MFR", "WTF",
    "SHT", "BCH", "CNT", "DCK", "ASS", "AZZ", "SOB", "POS", "PIS", "DMN", "SUX", "SUK", "GTF", "STF",
    # 성적·선정적 표현
    "SEX", "SXY", "SXE", "XXX", "PRN", "CUM", "KUM", "JIZ", "FAP", "DIK", "DIC", "COK", "COC",
    "TIT", "TTS", "ANL", "VAG", "NUD", "PUS", "PNS", "DTF", "POR",
    # 혐오·차별 표현
    "NIG", "NGR", "NGA", "FAG", "FGT", "KKK", "JAP", "NZI", "NAZ", "HTL", "RTD", "HOE", "SLT", "WHR", "GAY",
    "CNK", "GOK", "LES",
    # 폭력·자해
    "KYS", "KMS", "DIE", "KIL",
    # 화장실 말
    "PEE", "POO",
    # 한국어 욕설의 로마자·초성
    "SIB", "SIP", "SSB", "SBL", "SSI", "BSN", "BYS", "GSK", "JOT", "JRL", "MCN", "MCS", "NGM", "NGB",
    "DRI", "EMI", "CBL", "GSE", "JNA", "JOS", "NOM", "YMB", "YMN", "JMT", "ILB",
    # 영문 자판 상태에서 한글 욕을 친 경우 (십·좆·봊·섹·젖·ㅗㅗㅗ·엿·똥, 병신·존나·꺼져·닥쳐·자지 등)
    "TLQ", "WHW", "QHW", "TPR", "WJW", "HHH", "DUT", "EHD",
    "QUD", "WHS", "RJW", "EKR", "WKW", "ROT", "TOR", "ALC", "WLF", "DOA", "WHF", "SUS", "QUS", "QKQ",
})


def is_allowed(name):
    return len(name) == NAME_LENGTH and name.isascii() and name.isalpha() and name.isupper() and name not in BANNED_NAMES
