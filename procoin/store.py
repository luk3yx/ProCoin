import random, time
from typing import Dict, List

# Local imports
from .items import Item, ItemInterface

small_items_stock = 6
big_items_stock = 3
big_item_bound = 0x7fffffff

# A base error.
class Error(Exception):
    pass

# Item not found messages are created in two separate files, unify the message
# here.
class ItemNotFoundError(Error):
    def __str__(self):
        item_name = str(self.args[0] if self.args else 'Unknown item')
        return f"Couldn't find any `{item_name}`s in the store!"

class CannotAffordError(Error):
    def __str__(self):
        return "You don't have enough to buy that!"

class Store:
    __slots__ = ('items', 'current_stock', 'small_items', 'big_items',
                 'last_update')

    def __init__(self, items: ItemInterface) -> None:
        self.items = items

        self.big_items: List[Item] = \
            list(self.items.filter_by(self._is_bigitem))

        self.small_items: List[Item] = \
            list(self.items.filter_by(self._not_bigitem))

        self.current_stock: Dict[Item, int] = {}
        # self.regenerate_store()

    def __str__(self) -> str:
        return self.store_string

    @property
    def store_string(self) -> str:
        store_string = ''
        for item in sorted(self.current_stock.keys(), key=self._sort_key):
            # The diamond prefix is handled in items.py, no need to worry about
            # it here.
            in_stock: int = self.current_stock[item]
            store_string += f'`{in_stock}x` {item.item_string}\n'
        return store_string

    # Returns a boolean (booleans are subclasses of ints anyway).
    def buy(self, item: Item, qty: int) -> None:
        # Can't request less than 1 item.
        if qty < 1:
            raise Error('You must buy at least one item!')

        # Make sure the item(s) are in stock.
        in_stock = self.current_stock.get(item, 0)
        if in_stock < qty:
            if in_stock:
                raise Error(f'The store only has {in_stock} `{item}`s '
                            f'available for purchase!')
            else:
                raise ItemNotFoundError(item)

        # Remove the item(s) from the stock.
        self.current_stock[item] -= qty

        # Remove out-of-stock items from the store.
        if self.current_stock[item] == 0:
            del self.current_stock[item]

    def sell(self, item: Item, qty: int) -> None:
        # Can't request less than 1 item.
        if qty < 1:
            raise Error('You must sell at least one item!')

        # Add the item to the store
        if item in self.current_stock:
            self.current_stock[item] += qty
        else:
            self.current_stock[item] = qty

    def _sort_key(self, item: Item) -> int:
        return item.cost

    # If items have a default quantity of 0, they are excluded from the store.
    # This allows items to be removed from the store without being deleted from
    # items.json.
    def _is_bigitem(self, item: Item) -> bool:
        # Item class could add interface for getting cost etc.
        return item.stockable and item.cost >= big_item_bound

    def _not_bigitem(self, item: Item) -> bool:
        return item.stockable and item.cost < big_item_bound

    def regenerate_store(self) -> None:
        self.current_stock.clear()

        # Ensure that random.sample() doesn't error if there are very few
        # items.
        small_items = min(len(self.small_items), small_items_stock)
        big_items = min(len(self.big_items), big_items_stock)

        for item in random.sample(self.small_items, small_items):
            self.current_stock[item] = item.default_qty
        for item in random.sample(self.big_items, big_items):
            self.current_stock[item] = item.default_qty

        self.last_update = time.time()
