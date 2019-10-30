from . import items, store, users

class ProCoin:
    items: items.ItemInterface
    users: users.UserInterface

    def __init__(self, item_filename: str, user_filename: str) -> None:
        self.item_filename = item_filename
        self.user_filename = user_filename

    # Loads the item file from the disk. This should probably modify
    # ProCoin.items directly.
    def load_item_file(self) -> None:
        raise NotImplementedError

    # Loads the users file from the disk. This should probably modify
    # ProCoin.users directly.
    def load_user_file(self) -> None:
        raise NotImplementedError

    # Saves the users file to the disk.
    # WARNING: Blocking operations (file writing) on the main thread is
    # probably not a good idea! Calling this in a thread with the result of
    # UserInterface.to_dict() might be a better idea at some later stage.
    def save_user_file(self) -> None:
        raise NotImplementedError

    # Buys an item from the store.
    def buy(self, user_id: str, item_string: str, qty: int) -> bool:
        user = self.users.find_by_id(user_id)
        if not user:
            return False
        item = self.items.lookup(item_string)
        if not item:
            return False

        return user.buy_item(item, qty)

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
    def show_store(self) -> str:
        raise NotImplementedError
