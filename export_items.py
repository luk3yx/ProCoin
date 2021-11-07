#!/usr/bin/env python3
#
# A Python script to create items.csv.
#

from __future__ import annotations
import csv, json, os, sys
from procoin.items import Item, ItemInterface

def main(*, dir: str = os.path.dirname(__file__)) -> None:
    fn = os.path.join(dir, 'items.json')
    with open(fn, 'r') as f:
        items = ItemInterface.from_dict(json.load(f))

    writer = csv.writer(sys.stdout)
    writer.writerow(('id', 'name', 'cost', 'boost', 'default_qty', 'cursed'))
    for item in items.items.values():
        writer.writerow((item.id, item.name, item.cost, item.boost,
            item.default_qty, item.cursed))

if __name__ == '__main__':
    main()
