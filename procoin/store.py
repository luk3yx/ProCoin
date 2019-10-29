import random

# Local imports
from items import Item, ItemInterface

class Store:

    __slots__ = ('items', 'current_stock')
    def __init__(self, items: ItemInterface) -> None:
        self.items = items
        self.current_stock = {}
        self._generateStore()

    def __str__(self) -> str:
        return self.store_string()

    @property
    def store_string(self) -> str:
        store_string = ""
        for item: Item, in_stock: int in self.current_stock.items():
            # TODO if the item is a big item it it should get
            # a diamond emoji added in front of it.
            store_string += f"`{in_stock} {item.item_string}\n"

    # Returns a 0 to indicate a success or
    # a 1 to indicate that it failed.
    def buy(item: Item, qty: int) -> int:
        # Can't request less than 1 item.
        if qty < 1:
            return 1
        
        # Make sure the item(s) are in stock.
        in_stock = self.current_stock.get(item, 0)
        if in_stock < qty:
            return 1

        # Remove the item(s) from the stock.
        self.current_stock[item] -= qty
        
        # Remove out-of-stock items from the store.
        if self.current_stock[item] == 0:
            self.current_stock.pop(item)

    def _is_sizeable(item: Item) -> bool:
        # Item class could add interface for getting cost etc.
        return (item.cost > 5)

    def _generateStore() -> None:
        sizeable_items = self.items.filter_by(self._is_sizeable)
        for item: Item in sizeable_items:
            self.current_stock[item] = item.default_qty
