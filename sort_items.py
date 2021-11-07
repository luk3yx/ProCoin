#!/usr/bin/env python3
#
# A Python script to sort items.json.
#

from __future__ import annotations
import collections, json, os, random, sys
from procoin.items import Item, ItemInterface
from typing import Any, Union

class ItemsError(Exception):
    pass

_ItemType = Union['dict[str, Union[str, int, bool, list[list[str]]]]']
def _sort_item(item: Item) -> _ItemType:
    """
    Similar to Item.to_dict(), however returns an OrderedDict.
    """
    res: _ItemType = collections.OrderedDict()
    res['name'] = item.name
    res['cost'] = item.cost
    res['boost'] = item.boost
    res['default_qty'] = item.default_qty
    if item.raw_merges:
        res['merges'] = sorted(map(lambda i : sorted(i, key=str.lower),
            item.raw_merges))
    if item.cursed:
        res['cursed'] = item.cursed
    return res

def sort_items(items: ItemInterface) -> dict[str, _ItemType]:
    """
    Sorts a dict of items and returns a collections.OrderedDict. In Python 3.7+
    or CPython 3.6+ an OrderedDict is not necessary.
    """
    res: dict[str, _ItemType] = collections.OrderedDict()
    for item_id in sorted(items.items, key=lambda i : items.get_name(i).lower()):
        res[item_id] = _sort_item(items.get_item(item_id))
    return res

def to_json(items: ItemInterface):
    orig = sort_items(items)
    res = json.dumps(orig, indent=4)

    # A hack
    merges_indent = '\n' + ' ' * 16
    merges_indent2 = '\n' + ' ' * 12
    res = res.replace('[' + merges_indent, '[')
    res = res.replace(merges_indent2 + ']', ']')
    res = res.replace(merges_indent, ' ')

    lines = res.split('\n')
    indent = merges_indent2.lstrip('\n')
    for i, line in enumerate(lines):
        if line.startswith(indent + '[') and len(line) >= 80:
            raw = json.dumps((((json.loads(line),),),), indent=4)
            lines[i] = '\n'.join(raw.strip().split('\n')[3:-3])
            if line.endswith(','):
                lines[i] += ','

    lines.append('')
    res = '\n'.join(lines)

    # Ensure that this is still valid JSON
    assert orig == json.loads(res), 'Error while tweaking formatting!'
    return res

def assign_new_ids(items: dict[str, Any]) -> list[str]:
    """
    Assigns new IDs to any item ID that starts with "NEW:" or is an empty
    string. Will modify the dict in place. Will return a list of new item IDs
    assigned.
    """
    new_items = []
    for item_id in items:
        if item_id in ('', 'NEW') or item_id.startswith('NEW:'):
            new_items.append(item_id)

    for i, item_id in enumerate(new_items):
        item_range = (10 ** (max(len(str(len(items))), 5) + 1)) - 1
        item_range_l = len(str(item_range))
        new_id: str = ''
        while not new_id or new_id in items:
            new_id = str(random.randint(0, item_range)).zfill(item_range_l)
        items[new_id] = items.pop(item_id)
        new_items[i] = new_id

    return new_items

def main(*, dir: str = os.path.dirname(__file__)):
    fn = os.path.join(dir, 'items.json')
    with open(fn, 'r') as f:
        items = json.load(f)

    new_ids = assign_new_ids(items)
    for item_id in new_ids:
        print(f'Assigned item {items[item_id]["name"]!r} an ID of {item_id!r}')

    raw = to_json(ItemInterface.from_dict(items))
    with open(fn, 'w') as f:
        f.write(raw)

if __name__ == '__main__':
    main()
