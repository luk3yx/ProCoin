#!/usr/bin/env python3
#
# Converts the users.json export from CoinGames into ProCoin's users format.
#

from __future__ import annotations
import collections, json, os, random, sys
from procoin.items import Item, ItemInterface
from procoin.store import Store
from procoin.users import User, UserInterface
from collections.abc import Iterator
from typing import Any, Union

try:
    from ruamel.yaml import YAML
except ImportError:
    import yaml
else:
    yaml = YAML(typ='safe') # type: ignore
    del YAML

# Fix weirdness in item names
def fix_item_name(item_name) -> Iterator[str]:
    assert isinstance(item_name, str)
    item_name = item_name.replace("/'", "'")
    yield item_name
    yield item_name.replace("'", ' ')
    yield item_name.replace("'", "'s")

def main(*, dir: str = os.path.dirname(__file__)):
    # Get the ItemInterface
    with open(os.path.join(dir, 'items.json'), 'r') as f:
        items = ItemInterface.from_dict(json.load(f))

    # Get users.json (load it with YAML so it is less strict)
    print('Loading users.json...')
    fn = os.path.join(dir, 'users.json')
    with open(fn, 'r') as f:
        users = yaml.load(f)
    assert isinstance(users, dict)

    # Caches items
    cached_items: dict[str, Item] = {}

    unknown_items: set[str] = set()

    # Iterate over the users
    print('Converting...')
    for data in users.values():
        if 'upgrades' not in data:
            continue

        inventory = data.get('inventory', {})
        for upgrade in data['upgrades'].values():
            # Search for the item (and cache it to prevent many lookups)
            name = upgrade['name']
            item = cached_items.get(name)
            if not item:
                for fixed_name in fix_item_name(name):
                    item = cached_items[name] = items.lookup(fixed_name)
                    if item:
                        break
                else:
                    if name not in unknown_items:
                        unknown_items.add(name)
                        print(f'WARNING: Unknown item {name!r}')
                    continue

            # Ensure the quantity isn't a float
            qty = int(upgrade['quantity'])
            if qty > 0:
                inventory[item.id] = inventory.get(item.id, 0) + qty

        # Write back the inventory
        data['inventory'] = inventory

    # The users file needs a store
    store = Store(items)

    # Convert it to a UserInterface and back to remove all the unrequired data.
    print('Removing unrequired data...')
    users = UserInterface.from_dict(store, users).to_dict()

    # Write back to users.json
    print('Writing back to users.json...')
    raw = json.dumps(users)
    with open(fn, 'w') as f:
        f.write(raw)

if __name__ == '__main__':
    main()
