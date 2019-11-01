from typing import Any, Dict, List, Optional, Union
from . import items
from .store import Error, Store as _Store

class User:
    __slots__ = ('store', 'id', 'balance', 'boost', 'inventory')
    def __init__(self, store: _Store, id: str) -> None:
        self.store = store
        self.id: str = id
        self.balance: int = 0
        self.boost: int = 1
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
        boost: int = 1
        for item_id, qty in self.inventory.items():
            boost += ii.get_boost(item_id) * qty
        self.boost = boost

    # Buy an item from the store.
    def buy_item(self, item: items.Item, qty: int) -> None:
        total_cost = item.cost * qty
        if total_cost > self.balance:
            raise Error("You don't have enough to buy that!")

        self.store.buy(item, qty)
        self.balance -= total_cost
        if item.id in self.inventory:
            self.inventory[item.id] += qty
        else:
            self.inventory[item.id] = qty
        self.boost += item.boost * qty

class UserInterface:
    __slots__ = ('store', 'users')
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

    def find_by_id(self, user_id: Union[str, int]) -> Optional[User]:
        return self.users.get(str(user_id))

    def get_or_create(self, user_id: Union[str, int]) -> User:
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = User(self.store, user_id)
        return self.users[user_id]
