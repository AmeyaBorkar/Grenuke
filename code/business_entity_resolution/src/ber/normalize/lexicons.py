"""Hand-written, country-agnostic normalization lexicons for the v0 parser.

These are spelling equivalences, not external business data.  They are applied to
every record regardless of its country; a previously unseen country still works.
"""

LEGAL_FORMS = {
    "llc": "llc", "l l c": "llc", "inc": "inc", "incorporated": "inc",
    "corp": "corp", "corporation": "corp", "ltd": "ltd", "limited": "ltd",
    "pvt ltd": "pvt_ltd", "private limited": "pvt_ltd", "pvt limited": "pvt_ltd",
    "llp": "llp", "lp": "lp", "pllc": "pllc", "pc": "pc",
    "sa": "sa", "sas": "sas", "sasu": "sasu", "sarl": "sarl",
    "eurl": "eurl", "sci": "sci", "snc": "snc", "ei": "ei",
}

HONORIFICS = {"mr", "mrs", "ms", "dr", "shri", "sri", "smt", "prof"}
NAME_JUNK = {"dba", "formerly"}

STREET_TYPES = {
    "street": "st", "str": "st", "st": "st", "saint": "st",
    "avenue": "ave", "av": "ave", "ave": "ave",
    "road": "rd", "rd": "rd", "drive": "dr", "dr": "dr",
    "lane": "ln", "ln": "ln", "boulevard": "blvd", "blvd": "blvd", "bd": "blvd",
    "court": "ct", "ct": "ct", "place": "pl", "pl": "pl",
    "trail": "trl", "trl": "trl", "marg": "marg", "nagar": "nagar",
    "colony": "colony", "sector": "sector", "rue": "rue", "r": "rue",
    "chemin": "ch", "ch": "ch", "impasse": "imp", "imp": "imp",
    "allee": "allee", "quai": "quai", "route": "rte", "rte": "rte",
    "faubourg": "fg", "fg": "fg",
}

US_STATES = {
    "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar",
    "california": "ca", "colorado": "co", "connecticut": "ct", "delaware": "de",
    "florida": "fl", "georgia": "ga", "hawaii": "hi", "idaho": "id",
    "illinois": "il", "indiana": "in", "iowa": "ia", "kansas": "ks",
    "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn",
    "mississippi": "ms", "missouri": "mo", "montana": "mt", "nebraska": "ne",
    "nevada": "nv", "new hampshire": "nh", "new jersey": "nj",
    "new mexico": "nm", "new york": "ny", "north carolina": "nc",
    "north dakota": "nd", "ohio": "oh", "oklahoma": "ok", "oregon": "or",
    "pennsylvania": "pa", "rhode island": "ri", "south carolina": "sc",
    "south dakota": "sd", "tennessee": "tn", "texas": "tx", "utah": "ut",
    "vermont": "vt", "virginia": "va", "washington": "wa",
    "west virginia": "wv", "wisconsin": "wi", "wyoming": "wy",
    "district of columbia": "dc",
}

INDIA_STATES = {
    "andhra pradesh": "ap", "arunachal pradesh": "ar", "assam": "as",
    "bihar": "br", "chhattisgarh": "cg", "goa": "ga", "gujarat": "gj",
    "haryana": "hr", "himachal pradesh": "hp", "jharkhand": "jh",
    "karnataka": "ka", "kerala": "kl", "madhya pradesh": "mp",
    "maharashtra": "mh", "manipur": "mn", "meghalaya": "ml",
    "mizoram": "mz", "nagaland": "nl", "odisha": "od", "orissa": "od",
    "punjab": "pb", "rajasthan": "rj", "sikkim": "sk",
    "tamil nadu": "tn", "telangana": "ts", "tripura": "tr",
    "uttar pradesh": "up", "uttarakhand": "uk", "west bengal": "wb",
    "delhi": "dl", "chandigarh": "ch", "puducherry": "py",
    "jammu and kashmir": "jk", "ladakh": "la",
}

FRANCE_REGIONS = {
    "ile de france": "idf", "hauts de france": "hdf", "normandie": "nor",
    "bretagne": "bre", "pays de la loire": "pdl", "centre val de loire": "cvl",
    "bourgogne franche comte": "bfc", "grand est": "ges",
    "nouvelle aquitaine": "naq", "occitanie": "occ",
    "auvergne rhone alpes": "ara", "provence alpes cote d azur": "paca",
    "corse": "cor",
}

# Abbreviations are ambiguous across countries (CA, IN, GA, etc.).  They are
# retained as-is; no country feature is created from them.
STATE_CODES = ({value for value in US_STATES.values()}
               | {value for value in INDIA_STATES.values()}
               | set(FRANCE_REGIONS.values()))
STATE_NAMES = {**US_STATES, **INDIA_STATES, **FRANCE_REGIONS}
