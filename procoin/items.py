from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

# TODO: Move this to a different file.
def format_currency(amount: int) -> str:
    return f'{amount:,} 💰'

prefixes: Tuple[Tuple[int, str], ...] = (
    (2 ** 32 - 1, '💎'),
    (1_000_000_000, '$$'),
    (1_000_000, '$'),
)
class Item:
    __slots__ = ('id', 'name', 'cost', 'boost', 'default_qty')
    def __init__(self, id: str, name: str, cost: int, boost: int,
            default_qty: int) -> None:
        self.id = id
        self.name = name
        self.cost = cost
        self.boost = boost
        self.default_qty = default_qty

    def __repr__(self) -> str:
        cls = type(self)
        return f'<{cls.__module__}.{cls.__name__} {self.item_string}>'

    @property
    def item_string(self) -> str:
        res = ''
        if self.default_qty:
            # Get a prefix for expensive items.
            for min_cost, prefix in prefixes:
                if self.cost >= min_cost:
                    res = f'**{prefix}** '
                    break
        else:
            # Items no longer sold get their own prefix.
            res = '**V** '

        res += f'{self.name} ({format_currency(self.cost)}'
        if self.boost:
            res += f', provides a boost of {format_currency(self.boost)}'
        return res + ')'

    def to_dict(self) -> Dict[str, Union[str, int]]:
        return {'id': self.id, 'name': self.name, 'cost': self.cost,
                'boost': self.boost, 'default_qty': self.default_qty}

    # Creates an Item from a dict (similar to Item.to_dict()).
    # This treats "default quantity" as an alias for "default_qty" for
    # compatibility with CoinGames.
    @classmethod
    def from_dict(cls, id: str, data: Dict[Any, Any]):
        name = data['name']
        cost = data['cost']
        boost = data['boost']
        default_qty = data.get('default_qty', data.get('default quantity', 0))
        assert isinstance(id, str)
        assert isinstance(name, str)
        assert isinstance(cost, int)
        assert isinstance(boost, int)
        assert isinstance(default_qty, int)
        return cls(id, name, cost, boost, default_qty)


# An ItemInterface will allow the program to work with all
# the items that exist.
class ItemInterface:
    # Items: {"item_id": <Item object at ...>}
    def __init__(self, items: Dict[str, Item]) -> None:
        self.items = items

    # Items: {"item_id": {"name": "<name>", ...}}
    @classmethod
    def from_dict(cls, items: Dict[str, Dict[Any, Any]]):
        return cls({k: Item.from_dict(k, v) for k, v in items.items()})

    def get_item(self, item_id: str) -> Item:
        return self.items[item_id]

    @staticmethod
    def _item(item: str) -> str:
        return item.casefold().strip().replace("'", '').replace('’', '')

    # Get an itemString, which may not be an exact match,
    # an return the Item object if it exists.
    def lookup(self, item_string: str) -> Optional[Item]:
        # For testing, item strings starting with hashes are interpreted as IDs
        if item_string.startswith('#'):
            return self.items.get(item_string[1:])

        item_string = self._item(item_string)
        for item in self.items.values():
            if item_string == self._item(item.name):
                return item
        return None

    # Get an item's name from its ID.
    def get_name(self, item_id: str) -> str:
        try:
            return self.get_item(item_id).name
        except KeyError:
            return 'Unknown Item'

    # Get an item's cost from its ID.
    def get_cost(self, item_id: str) -> int:
        return self.get_item(item_id).cost

    # Get an item's boost from its ID.
    def get_boost(self, item_id: str) -> int:
        try:
            return self.get_item(item_id).boost
        except KeyError:
            return 0

    # Get the default quantity of an item from its ID.
    def get_default_qty(self, item_id: str) -> int:
        return self.get_item(item_id).default_qty

    # Key should be a function that accepts an Item and returns
    # True or False. filterBy will return a list of all items for
    # which key returns True.
    def filter_by(self, key: Callable[[Item], bool]) -> Iterable[Item]:
        return filter(key, self.items.values())

    # Return a human readable string. This should similar to
    # the string format already used by coingames.
    def get_item_string(self, item_id: str) -> str:
        return self.get_item(item_id).item_string
