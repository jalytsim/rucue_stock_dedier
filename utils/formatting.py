"""
Fonctions de formatage partagées (montants, quantités, dates, nombres en lettres)
"""
from datetime import datetime, timezone

FRENCH_DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
FRENCH_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
                 "août", "septembre", "octobre", "novembre", "décembre"]


def fmt_amount(value):
    """1234567.4 -> '1 234 567' (séparateur de milliers français)"""
    try:
        return f"{float(value):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def fmt_money(value, currency="Ar"):
    """1234567 -> '1 234 567 Ar'"""
    return f"{fmt_amount(value)} {currency}".strip()


def fmt_qty(value):
    """2.0 -> '2', 1.5 -> '1,5'"""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if value == int(value):
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def parse_number(text):
    """
    Convertit une saisie utilisateur en nombre.
    Accepte '5000', '5 000', '5000,50', '5000.50'. Lève ValueError sinon.
    """
    if text is None:
        raise ValueError("vide")
    cleaned = str(text).strip().replace(" ", "").replace(" ", "").replace(" ", "")
    if not cleaned:
        raise ValueError("vide")
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    return float(cleaned)


def fmt_date(date_str):
    """'2025-12-04' -> '04/12/2025'"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return date_str or ""


def parse_created_at(value):
    """
    Les anciens reçus ont created_at en UTC (CURRENT_TIMESTAMP SQLite, 'YYYY-MM-DD HH:MM:SS'),
    les nouveaux en heure locale ISO ('YYYY-MM-DDTHH:MM:SS'). Retourne un datetime local.
    """
    if not value:
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value)
        utc = datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return utc.astimezone().replace(tzinfo=None)
    except ValueError:
        return None


def fmt_datetime(value):
    dt = parse_created_at(value) if isinstance(value, str) else value
    return dt.strftime("%d/%m/%Y %H:%M") if dt else (value or "")


def fmt_long_date(dt):
    """Date en français indépendamment de la locale système"""
    return f"{FRENCH_DAYS[dt.weekday()].capitalize()} {dt.day} {FRENCH_MONTHS[dt.month - 1]} {dt.year}"


# ---------- Nombres en lettres (français) ----------

_UNITS = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
          "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
          "dix-sept", "dix-huit", "dix-neuf"]
_TENS = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def _below_100(n, plural_80=True):
    if n < 20:
        return _UNITS[n]
    tens, unit = divmod(n, 10)
    if tens in (7, 9):
        base = "soixante" if tens == 7 else "quatre-vingt"
        rest = n - (60 if tens == 7 else 80)
        if rest == 11 and tens == 7:
            return "soixante et onze"
        return f"{base}-{_UNITS[rest]}"
    if tens == 8:
        if unit == 0:
            return "quatre-vingts" if plural_80 else "quatre-vingt"
        return f"quatre-vingt-{_UNITS[unit]}"
    if unit == 0:
        return _TENS[tens]
    if unit == 1:
        return f"{_TENS[tens]} et un"
    return f"{_TENS[tens]}-{_UNITS[unit]}"


def _below_1000(n, plural=True):
    hundreds, rest = divmod(n, 100)
    if hundreds == 0:
        return _below_100(rest, plural)
    if hundreds == 1:
        head = "cent"
    else:
        head = f"{_UNITS[hundreds]} cent" + ("s" if rest == 0 and plural else "")
    return head if rest == 0 else f"{head} {_below_100(rest, plural)}"


def number_to_french(n):
    """Convertit un entier positif en toutes lettres (jusqu'aux milliards)."""
    n = int(round(n))
    if n == 0:
        return "zéro"
    if n < 0:
        return "moins " + number_to_french(-n)

    parts = []
    for value, singular, plural in ((10**9, "milliard", "milliards"),
                                    (10**6, "million", "millions")):
        count, n = divmod(n, value)
        if count:
            parts.append(f"{number_to_french(count)} {singular if count == 1 else plural}")
    thousands, n = divmod(n, 1000)
    if thousands:
        # "mille" est invariable et "cent"/"quatre-vingt" ne prennent pas de s devant
        parts.append("mille" if thousands == 1 else f"{_below_1000(thousands, plural=False)} mille")
    if n:
        parts.append(_below_1000(n))
    return " ".join(parts)
