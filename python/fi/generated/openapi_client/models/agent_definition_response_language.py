from enum import Enum


class AgentDefinitionResponseLanguage(str, Enum):
    AR = "ar"
    BG = "bg"
    CS = "cs"
    DA = "da"
    DE = "de"
    EL = "el"
    EN = "en"
    ES = "es"
    FI = "fi"
    FR = "fr"
    HI = "hi"
    HU = "hu"
    ID = "id"
    IT = "it"
    JA = "ja"
    KO = "ko"
    MS = "ms"
    NL = "nl"
    NO = "no"
    PL = "pl"
    PT = "pt"
    RO = "ro"
    RU = "ru"
    SK = "sk"
    SV = "sv"
    TR = "tr"
    UK = "uk"
    VI = "vi"
    ZH = "zh"

    def __str__(self) -> str:
        return str(self.value)
