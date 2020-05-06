from . import db, items, merges, store, users
from .items import Item as _Item
from .store import CannotAffordError, Error, ItemNotFoundError
from typing import List, Optional, Tuple, Union
import random

class ProCoin:
    items: items.ItemInterface
    store: store.Store
    users: users.UserInterface
    merges: merges.MergeInterface

    def __init__(self, item_filename: str, user_filename: str) -> None:
        self.item_filename = item_filename
        self.user_filename = user_filename
        self.load_all()

    def load_all(self) -> None:
        self._load_item_file()
        self.store = store.Store(self.items)
        self.merges = merges.MergeInterface(self.items)
        self._load_user_file()

    # Loads the item file from the disk. This should probably modify
    # ProCoin.items directly.
    def _load_item_file(self) -> None:
        self.items = items.ItemInterface.from_dict(db.load(self.item_filename))

    # Loads the users file from the disk. This should probably modify
    # ProCoin.users directly.
    def _load_user_file(self) -> None:
        data = db.load(self.user_filename)
        self.users = users.UserInterface.from_dict(self.store, data)

    # Saves the users file to the disk. The actual save operation is now done
    # in another thread.
    def save_user_file(self) -> None:
        db.save(self.user_filename, self.users.to_dict())

    # Saves the users file in the current thread.
    def save_user_file_blocking(self) -> None:
        db.save_blocking(self.user_filename, self.users.to_dict())

    # Buys an item from the store. Returns the total cost.
    def buy(self, user_id: Union[str, int], item_string: str, qty: int) -> int:
        item = self.items.lookup(item_string)
        if not item:
            raise ItemNotFoundError(item_string)

        user = self.users.get_or_create(user_id)
        user.buy_item(item, qty)
        return item.cost * qty

    # Sells an item to the store. Returns the total cost.
    def sell(self, user_id: Union[str, int], item_string: str, qty: int) \
            -> int:
        item = self.items.lookup(item_string)
        if not item:
            raise ItemNotFoundError(item_string)

        user = self.users.get_or_create(user_id)
        sale_price: int = user.sell_item(item, qty)
        return sale_price

    def give_item(self, user_id: Union[str, int], target_uid: Union[str, int],
            item_string: str, qty: int) -> None:
        user = self.users.get_or_create(user_id)
        target_user = self.users.find_by_id(target_uid)
        if not target_user:
            raise Error('Unknown user!')

        item = self.items.lookup(item_string)
        if not item:
            raise ItemNotFoundError(item_string)

        if qty < 0:
            raise Error('You cannot steal from someone!')
        elif qty == 0:
            raise Error('You cannot give someone nothing!')

        # User.take_item() will raise an error if the user doesn't have enough
        # items.
        user.take_item(item, qty)
        target_user.add_item(item, qty)

    # Adds money to a user.
    def add_cash(self, user_id: Union[str, int], amount: int) -> None:
        assert amount >= 0
        user = self.users.users[str(user_id)]
        user.balance += amount

    # Removes money from a user.
    def remove_cash(self, user_id: Union[str, int], amount: int) -> None:
        assert amount >= 0
        user = self.users.users[str(user_id)]
        if amount > user.balance:
            raise CannotAffordError
        user.balance -= amount

    # Pays a user
    def pay(self, source_uid: Union[str, int], target_uid: Union[str, int],
            amount: int) -> None:
        if amount < 0:
            raise Error('You cannot steal from someone!')
        elif amount == 0:
            raise Error('You cannot pay someone nothing!')

        source_uid = str(source_uid)
        target_uid = str(target_uid)
        if source_uid == target_uid:
            raise Error("I mean, you could pay yourself, but it'd do "
                        "absolutely nothing.")

        try:
            self.remove_cash(source_uid, amount)
            self.add_cash(target_uid, amount)
        except KeyError as exc:
            raise Error('Unknown user!') from exc

    # Merges items and returns the item names and resulting item.
    def merge(self, user_id: Union[str, int], item_strings: List[str],
            amount: int) -> Tuple[str, _Item]:
        item_list: List[_Item] = []
        for item_string in item_strings:
            item = self.items.lookup(item_string)
            if not item:
                raise ItemNotFoundError(item_string)
            item_list.append(item)

        user = self.users.get_or_create(user_id)
        return self.merges.merge_item(user, item_list, amount)

    # Uses a scroll of remove curse a user has to remove a cursed item. Will
    # return the item removed and (optionally) the random removed item.
    def remove_curse(self, user_id: Union[str, int]) \
            -> Tuple[_Item, Optional[_Item]]:
        user = self.users.get_or_create(user_id)
        scroll = self.items.get_item('remove_curse')
        user.assert_has_item(scroll, 1)

        cursed_items = []
        not_cursed = []
        for item_id in user.inventory:
            item: _Item = self.items.get_item(item_id)
            if item.cursed:
                cursed_items.append(item)
            else:
                not_cursed.append(item)

        if not cursed_items:
            raise Error('You cannot use a scroll of remove curse when you '
                'do not have a cursed item!')
        cursed_item = random.choice(cursed_items)

        # Take a random item sometimes
        removed_item: Optional[_Item] = None
        if (user.balance > 1_500_000_000 or random.randrange(3) == 0) and \
                not_cursed:
            removed_item = random.choice(not_cursed)
            user.take_item(removed_item, 1)

        # Actually remove the curse
        user.take_item(scroll, 1)
        try:
            user.take_item(cursed_item, 1, ignore_cursed=True)
        except:
            user.add_item(scroll, 1)
            raise

        return cursed_item, removed_item

    # Shows the store(?)
    # I think this does what it is meant to.
    def show_store(self) -> str:
        return self.store.store_string
