import random
from typing import Dict

# Local imports
from .items import Item, ItemInterface

class Store:
    __slots__ = ('items', 'current_stock')

    def __init__(self, items: ItemInterface) -> None:
        self.items = items
        self.current_stock: Dict[Item, int] = {}
        self._generateStore()

    def __str__(self) -> str:
        return self.store_string

    @property
    def store_string(self) -> str:
        store_string = ""
        for item, in_stock in self.current_stock.items():
            # The diamond prefix is handled in items.py, no need to worry about
            # it here.
            store_string += f"`{in_stock}x` {item.item_string}\n"
        return store_string

    # Returns a boolean (booleans are subclasses of ints anyway).
    def buy(self, item: Item, qty: int) -> bool:
        # Can't request less than 1 item.
        if qty < 1:
            return False

        # Make sure the item(s) are in stock.
        in_stock = self.current_stock.get(item, 0)
        if in_stock < qty:
            return False

        # Remove the item(s) from the stock.
        self.current_stock[item] -= qty

        # Remove out-of-stock items from the store.
        if self.current_stock[item] == 0:
            del self.current_stock[item]

        return True

    def _is_sizeable(self, item: Item) -> bool:
        # Item class could add interface for getting cost etc.
        return (item.cost > 5)

    def _generateStore(self) -> None:
        sizeable_items = self.items.filter_by(self._is_sizeable)
        for item in sorted(sizeable_items, key=lambda i : i.cost):
            self.current_stock[item] = item.default_qty
