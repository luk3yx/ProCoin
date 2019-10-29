from typing import Dict, List, Callable

# An ItemInterface will allow the program to work with all
# the items that exist. 
class ItemInterface:


    # Items is a list of item dictionaries.
    def __init__(self, items: List[ Dict[str, int] ]) -> None:
        self.items = items
        self.item_string = self.get_item_string()


    # See getItemString
    def __str__(self) -> str:
        return self.item_string


    # Get an itemString, which may not be an exact match,
    # an return the item's ID if it exists.
    def lookup_id(self, item_string: str) -> int:
        pass


    # Get an item's name from its ID.
    def get_name(self, item_id: int) -> str:
        pass


    # Get an item's cost from its ID.
    def get_cost(self, item_id: int) -> int:
        pass


    # Get an item's boost from its ID.
    def get_boost(self, item_id: int) -> int:
        pass


    # Get the default quantity of an item from its ID.
    def get_default_qty(self, item_id: int) -> int:
        pass


    # Key should be a function that accepts an Item and returns
    # True or False. filterBy will return a list of all items for
    # which key returns True.
    def filter_by(self, key: Callable) -> List[int]:
        pass


    # Return a human readable string. This should similar to
    # the string format already used by coingames.
    def get_item_string(self) -> str:
        pass