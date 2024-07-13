from settings import WHITELIST_CHARS


from typing import Sequence


def lower_underscore(seq: Sequence):
    col_names = []
    for col in seq:
        col = col.lower()
        name = []
        for c in col:
            l = WHITELIST_CHARS.get(c, " ")
            name.append(l)
        new = "".join(name).strip()
        while "  " in new:
            new = new.replace("  ", " ")
        new = new.replace(" ", "_")
        col_names.append(new)

    return col_names