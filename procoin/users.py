from __future__ import annotations
import math, random, time
from typing import Any, Optional, Union
from . import items
from .items import format_currency
from .store import CannotAffordError, Error, Store as _Store

class User:
    __slots__ = ('store', 'id', 'balance', 'boost', 'inventory', '_next_boost')
    def __init__(self, store: _Store, id: str) -> None:
        self.store = store
        self.id: str = id
        self.balance: int = 1_000_000
        self.boost: int = 1
        self._next_boost: float = 0
        self.inventory: dict[str, int] = {}

    # Convert the User object to a dict.
    def to_dict(self) -> dict[str, Union[int, dict[str, int]]]:
        return {'balance': self.balance, 'inventory': self.inventory}

    # Create a User object from a dict.
    @classmethod
    def from_dict(cls, store: _Store, id: str, data: dict[Any, Any]):
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
        # Convert self.inventory.items() to a tuple so items can be safely
        # deleted from it.
        for item_id, qty in tuple(self.inventory.items()):
            try:
                boost += ii.get_item(item_id).boost * qty
            except KeyError:
                # Delete unknown items
                print(f'WARNING: Deleting unknown item {item_id!r}.')
                del self.inventory[item_id]
        self.boost = boost

    # Adds an item to the user's inventory and adds the boost.
    def add_item(self, item: items.Item, qty: int) -> None:
        assert qty > 0
        if item.id in self.inventory:
            self.inventory[item.id] += qty
        else:
            self.inventory[item.id] = qty
        self.boost += item.boost * qty

    # Buy an item from the store.
    def buy_item(self, item: items.Item, qty: int) -> None:
        total_cost = item.cost * qty
        # Only raise CannotAffordError if the store actually has enough stock,
        # otherwise let Store.buy throw an error.
        sane: bool = True
        if total_cost > self.balance:
            sane = False
            if self.store.current_stock.get(item, 0) >= qty:
                raise CannotAffordError

        self.store.buy(item, qty)
        assert sane # In case Store.buy doesn't throw an error.
        self.balance -= total_cost
        self.add_item(item, qty)

    # Ensures a user has an item.
    def assert_has_item(self, item: items.Item, qty: int) -> None:
        assert qty > 0
        actual_amount = self.inventory.get(item.id, 0)
        if qty > actual_amount:
            raise Error(f'You only have {actual_amount} `{item}`'
                        f'{"" if actual_amount == 1 else "s"}, not {qty}!')
        if item.cursed:
            raise Error('You cannot remove cursed items!')

    # Deletes an item from the user's inventory and subtracts the boost.
    def take_item(self, item: items.Item, qty: int, *,
            ignore_cursed: bool = False) -> None:
        assert qty > 0
        actual_amount = self.inventory.get(item.id, 0)
        if qty > actual_amount:
            raise Error(f'You only have {actual_amount} `{item}`'
                        f'{"" if actual_amount == 1 else "s"}, not {qty}!')
        if item.cursed and not ignore_cursed:
            raise Error('You cannot remove cursed items!')

        actual_amount -= qty
        if actual_amount > 0:
            self.inventory[item.id] = actual_amount
        else:
            del self.inventory[item.id]
        self.boost -= item.boost * qty

    # Sell an item to the store. The actual sale price can be between 0.85 and
    # 1.05 times the actual price.
    def sell_item(self, item: items.Item, qty: int) -> int:
        if qty < 1:
            raise Error('You must sell at least one item!')

        self.take_item(item, qty)
        self.store.sell(item, qty)
        cost: float = item.cost * qty
        cost *= random.uniform(0.85, 1.05)
        cost_int: int = math.floor(cost)
        self.balance += cost_int
        return cost_int

    # Adds the boost if called 20 seconds after the last boost.
    def add_boost(self) -> None:
        t = time.time()
        if t >= self._next_boost + 20:
            self.balance += max(self.boost, 0)
            self._next_boost = t + 20

    # Apparently \r\n is larger than \n but smaller than \n\n.
    def get_inventory(self) -> list[str]:
        items = self.store.items
        inv_string = inv_prefix = \
            f'Balance: {format_currency(self.balance)}\n\n'
        total_items: int = 0
        for item in sorted(self.inventory,
                key=lambda i : items.get_name(i).lower()):
            # The diamond prefix is handled in items.py, no need to worry about
            # it here.
            amount = self.inventory[item]
            inv_string += f'`{amount}x` {items.get_prefixed_name(item)}: ' \
                          f'{format_currency(items.get_boost(item))}\n'
            total_items += amount
        footer = f'\nTotal items: {total_items:,}' \
                 f'\nTotal boost: {format_currency(self.boost)}'

        pages = []
        footer_l = len(footer)
        while len(inv_string) + footer_l > 2048:
            n = inv_string[:2048 - footer_l].rsplit('\n', 1)
            assert n
            pages.append(n[0] + '\n' + footer)
            inv_string = inv_prefix + (n[1] if len(n) > 1 else '') + \
                inv_string[2048 - footer_l:]
        pages.append(inv_string + footer)

        return pages

    @property
    def inv(self) -> str:
        return self.get_inventory()[0]

class UserInterface:
    __slots__ = ('store', 'users')
    def __init__(self, store: _Store, users: dict[str, User]) -> None:
        self.store = store
        self.users = users

    def to_dict(self) -> dict[str, dict[str, Union[int, dict[str, int]]]]:
        return {k: v.to_dict() for k, v in self.users.items()}

    @classmethod
    def from_dict(cls, store: _Store,
            users: dict[str, dict[str, Union[int, dict[str, int]]]]):
        new_users = {k: User.from_dict(store, k, v) for k, v in users.items()}
        return cls(store, new_users)

    def find_by_id(self, user_id: Union[str, int]) -> Optional[User]:
        return self.users.get(str(user_id))

    def get_or_create(self, user_id: Union[str, int]) -> User:
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = User(self.store, user_id)
        return self.users[user_id]
