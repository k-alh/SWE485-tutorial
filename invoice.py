"""Invoice rendering."""

from config.settings import CURRENCY, VAT_RATE


def build_invoice(account: dict, line_items: list[dict]) -> dict:
    """Assemble an invoice document for one billing cycle."""
    subtotal = sum(item["amount_cents"] for item in line_items)
    vat = round(subtotal * VAT_RATE)
    return {
        "account_id": account["id"],
        "cycle": account["cycle"],
        "currency": CURRENCY,
        "line_items": line_items,
        "subtotal_cents": subtotal,
        "vat_cents": vat,
        "total_cents": subtotal + vat,
    }


def format_total(invoice: dict) -> str:
    return f"{invoice['total_cents'] / 100:.2f} {invoice['currency']}"
