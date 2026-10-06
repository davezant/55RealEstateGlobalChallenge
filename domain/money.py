from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

CURRENCIES = ("BRL", "USD", "AED")

PER_USD = {
    "USD": Decimal("1"),
    "AED": Decimal("3.6725"),
    "BRL": Decimal("5.40"),
}

PREFIX = {"BRL": "R$", "USD": "US$", "AED": "AED"}

CENTS = Decimal("0.01")

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self):
        if self.currency not in CURRENCIES:
            raise ValueError("moeda_invalida")
        if not isinstance(self.amount, Decimal):
            raise TypeError("amount deve ser Decimal")
        object.__setattr__(self, "amount", self.amount.quantize(CENTS, rounding=ROUND_HALF_UP))

    def per_area(self, area: Decimal) -> "Money":
        if area <= 0:
            raise ValueError("area_invalida")
        return Money(self.amount / area, self.currency)

    def to_usd(self) -> Decimal:
        return self.amount / PER_USD[self.currency]

    def to_dict(self) -> dict:
        return {"valor": f"{self.amount:.2f}", "moeda": self.currency}

    def format(self) -> str:
        has_cents = self.amount % 1 != 0
        raw = f"{self.amount:,.2f}" if has_cents else f"{self.amount:,.0f}"
        if self.currency == "BRL":
            raw = raw.replace(",", "#").replace(".", ",").replace("#", ".")
        return f"{PREFIX[self.currency]} {raw}"

def sort_key_usd(money: Money | None) -> tuple:
    if money is None:
        return (1, Decimal("0"))
    return (0, money.to_usd())
