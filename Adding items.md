# Adding items

Items can be added to `items.json` in the following format:

```json
"item_id": {
    "name": "Item name",
    "cost": 1234,
    "boost": 123,
    "default_qty": 10,
    "merges": [
        ["merge_item_1_id", "merge_item_2_id"],
        ["other_merge_item_1_id", "other_merge_item_2_id"]
    ],
    "cursed": false
}
```

## Properties

 - `name` (`str`) The name of the item.
 - `cost` (`int`): The cost of the item.
 - `boost` (`int`): The amount of boost the item gives.
 - `default_qty` (`int`): The amount of items to add when stocking this item
    in the store. If this is 0, the item is not in the store and will get a `V`
    prefix (unless it is cursed).
 - `merges` (`List[List[str]]`, optional): A list of merges (that are
    themselves lists of item IDs).
 - `cursed` (`bool`, optional): Whether the item is cursed. Users cannot give
    away or sell cursed items. *Note that merges will not work with cursed
    items.*

## Sorting the items list

The Python script `sort_items.py` will parse (and validate) `items.json` and
write a formatted representation back to the file.

## Creating new item IDs

To create a new item ID, use `"NEW"`, a string starting with `"NEW:"`,
or an empty string as the item ID, then run `sort_items.py`. This should
generate a new item ID and print a message informing you of the item's new ID.

**WARNING:** Do not give multiple items the same ID (including `"NEW"`)!

**Do not change item IDs**, unless you want to delete all existing items of
that type.
