import re

# Registration/edit-profile inputs (name, contact) are free text, so they're
# the only user input surface reaching the DB. All queries use SQLAlchemy's
# parameterized builder, so SQL injection isn't actually possible here — this
# is a honeypot check to reject obvious injection attempts with a dedicated
# reply, not a real defense mechanism.
_SQL_INJECTION_PATTERN = re.compile(
    r"(--|;|/\*|\*/)"
    r"|\bunion\b\s+\bselect\b"
    r"|\bdrop\b\s+\btable\b"
    r"|\binsert\b\s+\binto\b"
    r"|\bdelete\b\s+\bfrom\b"
    r"|\bxp_cmdshell\b"
    r"|'\s*or\s*'?\d*'?\s*=\s*'?\d*'?",
    re.IGNORECASE,
)

SQL_INJECTION_REPLY = "Я же не дурак, конечно я предусмотрел что будет sql иньекция"


def looks_like_sql_injection(text: str) -> bool:
    return bool(_SQL_INJECTION_PATTERN.search(text))


# Reserved names/usernames that must not be claimable by other users
# (e.g. the bot admin's own handles, to prevent impersonation).
RESERVED_VALUES = {"myxabzbzzzz", "rw8js7", "rw8js8", "муха", "myxa"}

RESERVED_VALUE_REPLY = "Это имя/юзернейм зарезервированы, выбери, пожалуйста, другое."


def is_reserved_value(text: str) -> bool:
    return text.strip().lstrip("@").lower() in RESERVED_VALUES
