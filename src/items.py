from typing import Dict, List

# An ItemInterface will allow the program to work with all
# the items that exist. 
class ItemInterface:


    # Items is a list of item dictionaries.
    def __init__(self, items: [ Dict[str, int] ]) -> None:
        self.items = items
        self.item_string = self.getItemString()


    # See getItemString
    def __str__(self) -> str:
        return self.item_string


    # Get an itemString, which may not be an exact match,
    # an return the item's ID if it exists.
    def lookupID(self, item_string: str) -> int:
        pass


    # Get an item's name from its ID.
    def getName(self, item_id: int) -> str:
        pass


    # Get an item's cost from its ID.
    def getCost(self, item_id: int) -> int:
        pass


    # Get an item's boost from its ID.
    def getBoost(self, item_id: int) -> int:
        pass


    # Get the default quantity of an item from its ID.
    def getDefaultQty(self, item_id: int) -> int:
        pass


    # Key should be a function that accepts an Item and returns
    # True or False. filterBy will return a list of all items for
    # which key returns True.
    def filterBy(self, key: function) -> [int]:
        pass


    # Return a human readable string. This should similar to
    # the string format already used by coingames.
    def getItemString(self) -> str:
        pass