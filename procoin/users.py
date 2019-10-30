from typing import Any, Dict, List, Optional, Union
from . import items
from .store import Store as _Store

class User:
    __slots__ = ('store', 'id', 'balance', 'boost')
    def __init__(self, store: _Store, id: str) -> None:
        self.store = store
        self.id: str = id
        self.boost: int = 0
        self.balance: int = 0
        self.inventory: Dict[str, int] = {}

    # Convert the User object to a dict.
    def to_dict(self) -> Dict[str, Union[int, Dict[str, int]]]:
        return {'balance': self.balance, 'inventory': self.inventory}

    # Create a User object from a dict.
    @classmethod
    def from_dict(cls, store: _Store, id: str, data: Dict[Any, Any]):
        balance = data['balance']
        inventory = data['inventory']
        assert isinstance(id, str)
        assert isinstance(balance, int)
        assert isinstance(inventory, dict)
        self = cls(store, id)
        self.balance = balance
        self.inventory.update(inventory)
        self.recalc_boost()
        return self

    # Recalculates the user's boost, should be called when the inventory is
    # updated and the delta is not easily obtainable.
    def recalc_boost(self) -> None:
        ii: items.ItemInterface = self.store.items
        boost: int = 0
        for item_id, qty in self.inventory.items():
            boost += ii.get_boost(item_id) * qty
        self.boost = boost

    # Buy an item from the store.
    def buy_item(self, item: items.Item, qty: int) -> bool:
        if qty < 0:
            return False

        success = self.store.buy(item, qty)
        if success:
            if item.id in self.inventory:
                self.inventory[item.id] += 1
            else:
                self.inventory[item.id] = 1
            self.boost += item.boost * qty

        return success


class UserInterface:
    def __init__(self, store: _Store, users: Dict[str, User]) -> None:
        self.store = store
        self.users = users

    def to_dict(self) -> Dict[str, Dict[str, Union[int, Dict[str, int]]]]:
        return {k: v.to_dict() for k, v in self.users.items()}

    @classmethod
    def from_dict(cls, store: _Store,
            users: Dict[str, Dict[str, Union[int, Dict[str, int]]]]):
        new_users = {k: User.from_dict(store, k, v) for k, v in users.items()}
        return cls(store, new_users)

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
