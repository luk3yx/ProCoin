from . import db, items, store, users
from .store import CannotAffordError, Error, ItemNotFoundError
from typing import Union

class ProCoin:
    items: items.ItemInterface
    store: store.Store
    users: users.UserInterface

    def __init__(self, item_filename: str, user_filename: str) -> None:
        self.item_filename = item_filename
        self.user_filename = user_filename
        self.load_all()

    def load_all(self) -> None:
        self.load_item_file()
        self.store = store.Store(self.items)
        self.load_user_file()

    # Loads the item file from the disk. This should probably modify
    # ProCoin.items directly.
    def load_item_file(self) -> None:
        self.items = items.ItemInterface.from_dict(db.load(self.item_filename))

    # Loads the users file from the disk. This should probably modify
    # ProCoin.users directly.
    def load_user_file(self) -> None:
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

    # Shows the store(?)
    # I think this does what it is meant to.
    def show_store(self) -> str:
        return self.store.store_string
