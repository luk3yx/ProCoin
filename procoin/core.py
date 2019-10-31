from . import db, items, store, users

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

    # Saves the users file to the disk.
    # WARNING: Blocking operations (file writing) on the main thread is
    # probably not a good idea! Calling this in a thread with the result of
    # UserInterface.to_dict() might be a better idea at some later stage.
    def save_user_file(self) -> None:
        db.save(self.user_filename, self.users.to_dict())

    # Buys an item from the store. Returns the total cost.
    def buy(self, user_id: str, item_string: str, qty: int) -> int:
        item = self.items.lookup(item_string)
        if not item:
            raise store.ItemNotFoundError(item_string)

        user = self.users.get_or_create(user_id)
        user.buy_item(item, qty)
        return item.cost * qty

    # Adds money to a user.
    def add_cash(self, user_id: str, amount: int) -> None:
        user = self.users.users[user_id]
        assert amount >= 0
        user.balance += amount

    # Removes money from a user.
    def remove_cash(self, user_id: str, amount: int) -> None:
        user = self.users.users[user_id]
        assert amount >= 0
        user.balance -= amount

    # Shows the store(?)
    # I think this does what it is meant to.
    def show_store(self) -> str:
        return self.store.store_string
