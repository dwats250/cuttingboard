"""Moomoo client-statement PDF parser.

Reads a single Moomoo "Client Statement" PDF and returns one
:class:`NormalizedTrade` per Account Activity row across both the CAD
and USD margin sections, plus any "Transactions to settle after current
period" rows (tagged ``next_period=True``). Opening Balance and Closing
Balance rows are skipped.

Read-only. No mutation of pipeline state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pdfplumber


__all__ = [
    "NormalizedTrade",
    "OptionLeg",
    "parse_statement",
    "extract_period_ending",
]


# Side / instrument class literals — closed sets.
SIDE_BUY = "BUY"
SIDE_SELL = "SELL"
SIDE_EXPIRED = "EXPIRED"
SIDE_FX_BUY = "FX_BUY"
SIDE_FX_SELL = "FX_SELL"
SIDE_DEPOSIT = "DEPOSIT"

CLASS_EQUITY = "EQUITY"
CLASS_OPTION = "OPTION"
CLASS_FX = "FX"
CLASS_CASH = "CASH"

ACCOUNT_CAD = "MARGIN_CAD"
ACCOUNT_USD = "MARGIN_USD"

OPTION_CALL = "CALL"
OPTION_PUT = "PUT"


@dataclass(frozen=True)
class OptionLeg:
    strike: float
    expiry: date
    right: str  # "CALL" | "PUT"
    contracts: int


@dataclass(frozen=True)
class NormalizedTrade:
    date: date
    account: str  # "MARGIN_USD" | "MARGIN_CAD"
    side: str
    instrument_class: str
    underlier: Optional[str]
    option: Optional[OptionLeg]
    quantity: float  # signed
    price: Optional[float]
    amount: float  # signed
    raw_description: str
    next_period: bool = False

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "account": self.account,
            "side": self.side,
            "instrument_class": self.instrument_class,
            "underlier": self.underlier,
            "option": (
                {
                    "strike": self.option.strike,
                    "expiry": self.option.expiry.isoformat(),
                    "right": self.option.right,
                    "contracts": self.option.contracts,
                }
                if self.option
                else None
            ),
            "quantity": self.quantity,
            "price": self.price,
            "amount": self.amount,
            "raw_description": self.raw_description,
            "next_period": self.next_period,
        }


# ---------------------------------------------------------------------------
# Internal parsing helpers
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"^([A-Z][a-z]{2} \d{1,2}, \d{4})\s+(.+)$")
_PERIOD_RE = re.compile(r"Period Ending:\s*([A-Z][a-z]{2} \d{1,2}, \d{4})")
_NUM_RE = re.compile(r"^\(?-?\d[\d,]*(?:\.\d+)?\)?$")
_OPTION_RE = re.compile(
    r"^(CALL|PUT)\s+100\s+(\S+)\s+(\d{2}/\d{2}/\d{2})\s+(\d+(?:\.\d+)?)$"
)
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.]{0,5}$")

# Recognised Type-cell prefixes, ordered longest-first so e.g.
# "FX Buy Trade" wins over "Buy". The bare "E-transfer" alias absorbs
# the real-PDF case where the Type cell wraps as "E-transfer\nDeposit"
# and only the first token survives on the trade row; the orphan
# "Deposit" continuation line is filtered upstream.
_TYPE_PREFIXES = [
    ("FX Buy Trade", SIDE_FX_BUY, CLASS_FX),
    ("FX Sell Trade", SIDE_FX_SELL, CLASS_FX),
    ("E-transfer Deposit", SIDE_DEPOSIT, CLASS_CASH),
    ("E-transfer", SIDE_DEPOSIT, CLASS_CASH),
    ("Cash Rebate", SIDE_DEPOSIT, CLASS_CASH),
    ("Expired Option", SIDE_EXPIRED, CLASS_OPTION),
    ("Buy", SIDE_BUY, None),
    ("Sell", SIDE_SELL, None),
]

_SKIP_DESCRIPTIONS = {"Opening Balance", "Closing Balance"}

# Known type-cell continuation tokens that appear as orphan lines in
# the real Moomoo PDFs (e.g. "E-transfer\nDeposit" wraps the Type
# cell). The continuation is redundant with the alias entries in
# ``_TYPE_PREFIXES`` and is dropped during pre-processing.
_TYPE_CONTINUATIONS = {"Deposit"}


def _parse_number(token: str) -> float:
    t = token.strip().replace(",", "")
    if t.startswith("(") and t.endswith(")"):
        return -float(t[1:-1])
    return float(t)


def _parse_date(token: str) -> date:
    return datetime.strptime(token, "%b %d, %Y").date()


def _parse_option_desc(desc: str) -> Optional[tuple[OptionLeg, str]]:
    m = _OPTION_RE.match(desc.strip())
    if not m:
        return None
    right, underlier, exp_raw, strike_raw = m.group(1), m.group(2), m.group(3), m.group(4)
    expiry = datetime.strptime(exp_raw, "%m/%d/%y").date()
    # contracts is set at call site from signed quantity; placeholder=0 here.
    leg = OptionLeg(strike=float(strike_raw), expiry=expiry, right=right, contracts=0)
    return leg, underlier


def _split_type(rest: str) -> Optional[tuple[str, str, Optional[str], str]]:
    """Return (raw_type, side, instrument_hint_or_None, remainder)."""
    for prefix, side, klass in _TYPE_PREFIXES:
        if rest.startswith(prefix + " ") or rest == prefix:
            remainder = rest[len(prefix) :].strip()
            return prefix, side, klass, remainder
    return None


def _split_trailing_numbers(tokens: list[str], count: int) -> tuple[list[str], list[float]]:
    if len(tokens) < count:
        raise ValueError(f"need {count} trailing numbers in {tokens!r}")
    nums = tokens[-count:]
    for n in nums:
        if not _NUM_RE.match(n):
            raise ValueError(f"non-numeric trailing token in {tokens!r}: {n!r}")
    return tokens[:-count], [_parse_number(n) for n in nums]


def _parse_trade_line(
    line: str,
    *,
    account: str,
    next_period: bool,
) -> Optional[NormalizedTrade]:
    m = _DATE_RE.match(line)
    if not m:
        return None
    trade_date = _parse_date(m.group(1))
    rest = m.group(2).strip()

    split = _split_type(rest)
    if split is None:
        return None
    _, side, klass_hint, remainder = split

    tokens = remainder.split()

    if side in (SIDE_DEPOSIT, SIDE_FX_BUY, SIDE_FX_SELL):
        # One trailing amount only.
        desc_tokens, nums = _split_trailing_numbers(tokens, 1)
        amount = nums[0]
        description = " ".join(desc_tokens)
        return NormalizedTrade(
            date=trade_date,
            account=account,
            side=side,
            instrument_class=klass_hint or CLASS_CASH,
            underlier=None,
            option=None,
            quantity=0.0,
            price=None,
            amount=amount,
            raw_description=description,
            next_period=next_period,
        )

    if side == SIDE_EXPIRED:
        # Expired Option rows have no Price column — only quantity + amount.
        desc_tokens, nums = _split_trailing_numbers(tokens, 2)
        quantity, amount = nums
        price = None
    else:
        # Buy / Sell — three trailing numerics: qty, price, amount.
        desc_tokens, nums = _split_trailing_numbers(tokens, 3)
        quantity, price, amount = nums

    description = " ".join(desc_tokens)
    # Real PDFs render a bare "*" between the option strike and the
    # quantity cell (e.g. "CALL 100 GLD 02/25/26 480 *  1 ..."); after
    # stripping trailing numerics the "*" lands at the description tail.
    option_desc = description[:-2].rstrip() if description.endswith(" *") else description

    parsed_opt = _parse_option_desc(option_desc)
    if parsed_opt is not None:
        leg, underlier = parsed_opt
        # Rebuild leg with contracts derived from |quantity|.
        leg = OptionLeg(strike=leg.strike, expiry=leg.expiry, right=leg.right, contracts=int(abs(quantity)))
        return NormalizedTrade(
            date=trade_date,
            account=account,
            side=side,
            instrument_class=CLASS_OPTION,
            underlier=underlier,
            option=leg,
            quantity=quantity,
            price=price,
            amount=amount,
            raw_description=description,
            next_period=next_period,
        )

    # Equity row. A resolvable ticker is a single-token, uppercase
    # description; multi-word company names (e.g. "ETF OPPORTUNITIES TR
    # T REX 2X") yield underlier=None rather than mis-attributing the
    # first description token to a Cuttingboard universe symbol.
    desc_split = description.split() if description else []
    if len(desc_split) == 1 and _TICKER_RE.match(desc_split[0]):
        underlier = desc_split[0]
    else:
        underlier = None
    return NormalizedTrade(
        date=trade_date,
        account=account,
        side=side,
        instrument_class=CLASS_EQUITY,
        underlier=underlier,
        option=None,
        quantity=quantity,
        price=price,
        amount=amount,
        raw_description=description,
        next_period=next_period,
    )


def extract_period_ending(text: str) -> Optional[date]:
    m = _PERIOD_RE.search(text)
    if not m:
        return None
    return _parse_date(m.group(1))


def parse_statement(path: Path) -> list[NormalizedTrade]:
    """Parse a Moomoo client-statement PDF into NormalizedTrade rows."""
    path = Path(path)
    trades: list[NormalizedTrade] = []
    account: Optional[str] = None
    next_period = False

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                if line.startswith("Account Activity - Margin Account (CAD)"):
                    account = ACCOUNT_CAD
                    next_period = False
                    continue
                if line.startswith("Account Activity - Margin Account (USD)"):
                    account = ACCOUNT_USD
                    next_period = False
                    continue
                if line.startswith("Transactions to settle after current period"):
                    next_period = True
                    continue

                if line in _SKIP_DESCRIPTIONS:
                    continue
                # Strip leading "Opening Balance ..." / "Closing Balance ..." rows.
                if line.startswith("Opening Balance") or line.startswith("Closing Balance"):
                    continue
                # Skip Date/Type/Description header row.
                if line.startswith("Date") and "Description" in line:
                    continue
                # Orphan Type-cell continuation (e.g. "Deposit" from a
                # wrapped "E-transfer\nDeposit" Type cell). The trade row
                # itself was parsed via the single-token type alias on the
                # previous line.
                if line in _TYPE_CONTINUATIONS:
                    continue
                if account is None:
                    continue

                trade = _parse_trade_line(line, account=account, next_period=next_period)
                if trade is not None:
                    trades.append(trade)

    return trades


def extract_period_from_pdf(path: Path) -> Optional[date]:
    path = Path(path)
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            d = extract_period_ending(text)
            if d is not None:
                return d
    return None
