from decimal import Decimal, ROUND_HALF_UP

from .models import Item, PriceItem


def check_stock(name):
    """Look up how many of an item we have."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    return {"name": item.name, "quantity": item.quantity}


def list_items():
    """Return every item in the inventory."""
    items = Item.objects.all()
    return {"items": [{"name": i.name, "quantity": i.quantity} for i in items]}


def add_item(name, quantity):
    """Create a new item, or add to an existing one's stock."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is not None:
        item.quantity += quantity
        item.save()
        return {"name": item.name, "quantity": item.quantity, "created": False}
    item = Item.objects.create(name=name, quantity=quantity)
    return {"name": item.name, "quantity": item.quantity, "created": True}


def remove_stock(name, quantity):
    """Take a quantity out of stock."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    if quantity > item.quantity:
        return {
            "error": f"Cannot remove {quantity}. Only {item.quantity} in stock.",
            "name": item.name,
            "quantity": item.quantity,
        }
    item.quantity -= quantity
    item.save()
    return {"name": item.name, "quantity": item.quantity}


def delete_item(name):
    """Remove an item from the inventory entirely."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.delete()
    return {"deleted": name}


def _money(value):
    return str(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def set_price(name, unit_price):
    """Create or update the unit price of an item."""
    if unit_price < 0:
        return {"error": "Price cannot be negative."}
    price_item = PriceItem.objects.filter(name__iexact=name).first()
    price = Decimal(str(unit_price))
    if price_item is not None:
        price_item.unit_price = price
        price_item.save()
        return {"name": price_item.name, "unit_price": _money(price_item.unit_price), "created": False}
    price_item = PriceItem.objects.create(name=name, unit_price=price)
    return {"name": price_item.name, "unit_price": _money(price_item.unit_price), "created": True}


def get_price(name):
    """Look up the unit price of an item."""
    price_item = PriceItem.objects.filter(name__iexact=name).first()
    if price_item is None:
        return {"error": f"No price is set for '{name}'."}
    return {"name": price_item.name, "unit_price": _money(price_item.unit_price)}


def list_prices():
    """Return every item that has a price."""
    return {
        "prices": [
            {"name": p.name, "unit_price": _money(p.unit_price)}
            for p in PriceItem.objects.all()
        ]
    }


def calculate_cost(name, quantity, vat_percent=0):
    """Compute the total cost of N units, optionally adding VAT."""
    if quantity <= 0:
        return {"error": "Quantity must be positive."}
    if vat_percent < 0:
        return {"error": "VAT percent cannot be negative."}
    price_item = PriceItem.objects.filter(name__iexact=name).first()
    if price_item is None:
        return {"error": f"No price is set for '{name}'."}
    subtotal = price_item.unit_price * quantity
    vat_amount = subtotal * Decimal(str(vat_percent)) / Decimal("100")
    total = subtotal + vat_amount
    return {
        "name": price_item.name,
        "quantity": quantity,
        "unit_price": _money(price_item.unit_price),
        "subtotal": _money(subtotal),
        "vat_percent": vat_percent,
        "vat_amount": _money(vat_amount),
        "total": _money(total),
    }


TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "check_stock",
        "description": "Look up the current quantity of a single item in the inventory. Use this whenever the user asks whether something is in stock or how many there are.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "list_items",
        "description": "Return every item in the inventory with its quantity. Use this when the user asks what is in stock generally, or asks for a list, rather than about one specific item.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "add_item",
        "description": "Add stock to the inventory. If the item does not exist it is created; if it already exists the quantity is added to the existing total. Use this for restocking and for new deliveries.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to add. Must be positive.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "remove_stock",
        "description": "Reduce the quantity of an existing item. Use this when items are sold, shipped or used. This does NOT delete the item; it only lowers the number.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to remove. Must be positive.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "delete_item",
        "description": "Permanently remove an item and its record from the inventory entirely. This is destructive. Only use it when the user clearly wants the item gone, not when they want to reduce its quantity.",
        "parameters": {
            "type": "object",
            "properties": {

                "name": {
                    "type": "string",
                    "description": "The name of the item to delete.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "set_price",
        "description": "Create or update the unit price of an item. Use this when the user states or changes the price of something.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the item, e.g. 'Chocolate bar'."},
                "unit_price": {"type": "number", "description": "Price of ONE unit. Must not be negative."},
            },
            "required": ["name", "unit_price"],
        },
    },
    {
        "type": "function",
        "name": "get_price",
        "description": "Look up the unit price of a single item. Use this when the user asks how much one item costs.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the item, e.g. 'Chocolate bar'."},
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "list_prices",
        "description": "Return every item that has a price. Use this when the user asks for a price list.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "calculate_cost",
        "description": "Calculate the total cost of a number of units of an item, optionally adding VAT/tax. ALWAYS use this for any cost, total or VAT question instead of doing the arithmetic yourself.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the item, e.g. 'Chocolate bar'."},
                "quantity": {"type": "integer", "description": "How many units. Must be positive."},
                "vat_percent": {"type": "number", "description": "VAT percentage to add, e.g. 10 for 10%. Use 0 if no VAT is mentioned."},
            },
            "required": ["name", "quantity"],
        },
    },
]

TOOL_FUNCTIONS = {
    "check_stock": check_stock,
    "list_items": list_items,
    "add_item": add_item,
    "remove_stock": remove_stock,
    "delete_item": delete_item,
    "set_price": set_price,
    "get_price": get_price,
    "list_prices": list_prices,
    "calculate_cost": calculate_cost,
}
