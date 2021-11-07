from __future__ import annotations
from collections.abc import Collection
from typing import Optional
from .items import Item, ItemInterface
from .store import Error
from .users import User, UserInterface

class MergeInterface:
    __slots__ = ('merges', 'items')

    def __init__(self, items: ItemInterface) -> None:
        self.items = items
        self.merges: dict[tuple[Item, ...], Item] = {}
        self.update_merges()

    # Updates the merges
    def update_merges(self) -> None:
        self.merges.clear()
        merge: list[Item]
        for item in self.items.items.values():
            if not item.raw_merges:
                continue
            for merges in item.raw_merges:
                assert merges
                try:
                    merge = sorted((self.items.items[i] for i in merges),
                                   key=lambda n : n.id)
                except KeyError:
                    for i in merges:
                        assert i in self.items.items, f'Error in items.json:' \
                            f'Invalid item ID in merge: {i!r}'

                    # This should never happen
                    raise
                else:
                    self.merges[tuple(merge)] = item

    # Gets a possible merge created from a tuple/list of items
    def get_merge(self, items: Collection[Item]) -> Optional[Item]:
        sorted_items: list[Item] = sorted(items, key=lambda item : item.id)
        return self.merges.get(tuple(sorted_items))

    # Gets a list of merges for the "merges" command.
    def get_merges(self) -> str:
        res: list[str] = []
        for merge, result in self.merges.items():
            items = sorted(item.name for item in merge)
            res.append(f"`{'` + `'.join(items)}` → {result}")
        res.sort()
        return '\n'.join(res)

    # Performs a merge and returns a formatted names list of items and the
    # resulting item.
    def merge_item(self, user: User, items: Collection[Item],
            amount: int) -> tuple[str, Item]:
        items = sorted(items, key=lambda item : item.name)
        if not items or amount < 1:
            raise Error('You... uhh... merge nothing to make '
                '`absolutely nothing`!')

        # Get a nice item list
        names_l = [f'{i.prefixed_name!r}' for i in items]
        if names_l:
            if len(names_l) > 1:
                names_l[-1] = 'and ' + names_l[-1]
        if len(names_l) > 2:
            names = ', '.join(names_l)
        else:
            names = ' '.join(names_l)

        result = self.get_merge(items)
        if not result:
            raise Error(f"You can't merge {names}!")

        # Ensure a user has every item first
        required_items: dict[Item, int] = {}
        for item in items:
            required_items[item] = required_items.get(item, 0) + amount
        for item, qty in required_items.items():
            user.assert_has_item(item, qty)

        idx: int = 0
        try:
            for idx, item in enumerate(items):
                user.take_item(item, amount)
            user.add_item(result, amount)
        except:
            # If this explodes, return all items.
            for item in items[:idx]:
                user.add_item(item, amount)
            raise

        return names, result
