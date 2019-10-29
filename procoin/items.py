from typing import Any, Callable, Dict, Iterable, List, Tuple, Union

# TODO: Move this to a different file.
symbol = '💰'

prefixes: Tuple[Tuple[int, str], ...] = (
    (100_000_000, '💎'),
    (10_000_000, '$$'),
    (1_000_000, '$'),
)
class Item:
    __slots__ = ('id', 'name', 'cost', 'boost', 'default_qty')
    def __init__(self, id: int, name: str, cost: int, boost: int,
            default_qty: int) -> None:
        self.id = id
        self.name = name
        self.cost = cost
        self.boost = boost
        self.default_qty = default_qty

    @property
    def item_string(self) -> str:
        res = ''
        # Get a prefix for expensive items.
        for min_cost, prefix in prefixes:
            if self.cost >= min_cost:
                res = f'{prefix} '
                break

        res += f'{self.name} ({self.cost} {symbol}'
        if self.boost:
            res += f', provides a boost of {self.boost} {symbol}'
        return res + ')'

    def to_dict(self) -> Dict[str, Union[str, int]]:
        return {'id': self.id, 'name': self.name, 'cost': self.cost,
                'boost': self.boost, 'default_qty': self.default_qty}

    # Creates an Item from a dict (similar to Item.to_dict()).
    @classmethod
    def from_dict(cls, data: Dict[Any, Any]):
        id = data['id']
        name = data['name']
        cost = data['cost']
        boost = data['boost']
        default_qty = data['default_qty']
        assert isinstance(id, int)
        assert isinstance(name, str)
        assert isinstance(cost, int)
        assert isinstance(boost, int)
        assert isinstance(default_qty, int)
        return cls(id, name, cost, boost, default_qty)


# An ItemInterface will allow the program to work with all
# the items that exist.
class ItemInterface:
    # Items is a list of item dictionaries.
    def __init__(self, items: List[Item]) -> None:
        self.items = items

    # Creates the Item list from a list of dicts.
    @classmethod
    def from_dicts(cls, items: Iterable[Dict[Any, Any]]):
        return cls(list(map(Item.from_dict, items)))

    def get_item(self, item_id: int) -> Item:
        if item_id < 0:
            raise IndexError('Item ID below 0.')
        return self.items[item_id]

    # Get an itemString, which may not be an exact match,
    # an return the item's ID if it exists.
    def lookup_id(self, item_string: str) -> int:
        raise NotImplementedError

    # Get an item's name from its ID.
    def get_name(self, item_id: int) -> str:
        return self.get_item(item_id).name

    # Get an item's cost from its ID.
    def get_cost(self, item_id: int) -> int:
        return self.get_item(item_id).cost

    # Get an item's boost from its ID.
    def get_boost(self, item_id: int) -> int:
        return self.get_item(item_id).boost

    # Get the default quantity of an item from its ID.
    def get_default_qty(self, item_id: int) -> int:
        return self.get_item(item_id).default_qty

    # Key should be a function that accepts an Item and returns
    # True or False. filterBy will return a list of all items for
    # which key returns True.
    def filter_by(self, key: Callable[[Item], bool]) -> Iterable[Item]:
        return filter(key, self.items)

    # Return a human readable string. This should similar to
    # the string format already used by coingames.
    def get_item_string(self, item_id: int) -> str:
        return self.get_item(item_id).item_string
