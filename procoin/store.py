import random
from typing import Dict, List

# Local imports
from .items import Item, ItemInterface

small_items_stock = 6
big_items_stock = 3
big_item_bound = 0x7fffffff

class Store:
    __slots__ = ('items', 'current_stock', 'small_items', 'big_items')

    def __init__(self, items: ItemInterface) -> None:
        self.items = items
        
        self.big_items: List[Item] =\
            list(self.items.filter_by(self._is_bigitem))
            
        self.small_items: List[Item] =\
            list(self.items.filter_by(self._not_bigitem))
           
        self.current_stock: Dict[Item, int] = {}
        self._generateStore()

    def __str__(self) -> str:
        return self.store_string

    @property
    def store_string(self) -> str:
        store_string = ""
        for item in sorted(self.current_stock.keys(), key=self._sort_key):
            # The diamond prefix is handled in items.py, no need to worry about
            # it here.
            in_stock: int = self.current_stock[item]
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

    def _sort_key(self, item: Item) -> int:
        return (item.cost)

    def _is_bigitem(self, item: Item) -> bool:
        # Item class could add interface for getting cost etc.
        return (item.cost >= big_item_bound)

    def _not_bigitem(self, item: Item) -> bool:
        return (item.cost < big_item_bound)

    def _generateStore(self) -> None:
        self.current_stock: Dict[Item, int] = {}
        for item in random.sample(self.small_items, small_items_stock):
            self.current_stock[item] = item.default_qty
        for item in random.sample(self.big_items, big_items_stock):
            self.current_stock[item] = item.default_qty
