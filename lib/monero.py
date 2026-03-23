import re

# Monero base58 uses the same alphabet as Bitcoin base58
# Standard mainnet addresses start with '4' (95 chars)
# Subaddresses start with '8' (95 chars)
# Integrated addresses start with '4' (106 chars)
_XMR_CHARS = r"[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]"

REGEX = re.compile(r"\b[48]" + _XMR_CHARS + r"{93}\b", re.MULTILINE)
REGEX_ALL = re.compile(r"^[48]" + _XMR_CHARS + r"{93}$", re.MULTILINE)


def is_valid(addr):
    """Basic length and character set validation for Monero addresses."""
    addr = addr.strip()
    if not re.match(REGEX_ALL, addr):
        return False
    if len(addr) != 95:
        return False
    return True
