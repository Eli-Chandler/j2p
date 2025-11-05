from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Iterable

INDENT_AMOUNT = 2


@dataclass(frozen=True)
class Prim:
    name: Literal["int", "float", "str", "bool", "null"]

    def __str__(self, indent=0):
        return self.name

    def to_python_type(self) -> str:
        if self.name == "null":
            return "None"
        return self.name


@dataclass(frozen=True)
class Obj:
    # Needs to be sorted
    props: tuple[tuple[str, Prim | Obj | Arr | J2PUnionType], ...]

    def __str__(self, indent=0):
        next_indent = indent + INDENT_AMOUNT
        indent_str = " " * indent
        props_str = ",\n".join(
            f"{' ' * next_indent}{k}: {v.__str__(next_indent)}" for k, v in self.props
        )
        return f"{{\n{props_str}\n{indent_str}}}"

    def to_python_type(self, name) -> str:
        return f"{name}Model"


@dataclass(frozen=True)
class Arr:
    items: J2PUnionType | None

    def __str__(self, indent=0):
        if self.items is None:
            return "[]"
        return f"[{self.items.__str__(indent + INDENT_AMOUNT)}]"

    def to_python_type(self) -> str:
        if self.items is None:
            return "list[Any]"
        return f"list[{self.items.to_python_type()}]"


@dataclass(frozen=True)
class J2PUnionType:
    types: tuple[Prim | Obj | Arr, ...]

    def __str__(self, indent=0):
        return " | ".join(t.__str__(indent) for t in self.types)

    def to_python_type(self) -> str:
        return " | ".join(
            t.to_python_type() if hasattr(t, "to_python_type") else str(t)
            for t in self.types
        )


JSON = None | str | float | int | bool | list["JSON"] | dict[str, "JSON"]


def _normalize_union(
    types: Iterable[Prim | Obj | Arr | J2PUnionType],
) -> Prim | Obj | Arr | J2PUnionType:
    flat: set[Prim | Obj | Arr] = set()
    for t in types:
        if isinstance(t, J2PUnionType):
            flat.update(t.types)
        else:
            flat.add(t)

    if len(flat) == 1:
        return next(iter(flat))
    return J2PUnionType(
        types=tuple(
            sorted(
                flat,
                key=lambda x: (
                    isinstance(x, Prim),
                    isinstance(x, Obj),
                    isinstance(x, Arr),
                    str(x),
                ),
            )
        )
    )


def _sorted_props(
    d: dict[str, Prim | Obj | Arr | J2PUnionType],
) -> tuple[tuple[str, Prim | Obj | Arr | J2PUnionType], ...]:
    return tuple(sorted(d.items(), key=lambda kv: kv[0]))


def parse_json(j: JSON) -> Prim | Obj | Arr:
    if j is None:
        return Prim(name="null")
    elif isinstance(j, bool):
        return Prim(name="bool")
    elif isinstance(j, int) and not isinstance(j, bool):
        return Prim(name="int")
    elif isinstance(j, float):
        return Prim(name="float")
    elif isinstance(j, str):
        return Prim(name="str")
    elif isinstance(j, list):
        if not j:
            return Arr(items=None)
        item_schemas = [parse_json(item) for item in j]
        items_union = _normalize_union(item_schemas)
        if isinstance(items_union, J2PUnionType):
            return Arr(items=items_union)
        else:
            return Arr(items=J2PUnionType(types=(items_union,)))
    elif isinstance(j, dict):
        props = {key: parse_json(value) for key, value in j.items()}
        return Obj(props=_sorted_props(props))
    else:
        raise ValueError("Unsupported JSON type")


def _combine_nodes(
    a: Prim | Obj | Arr | J2PUnionType, b: Prim | Obj | Arr | J2PUnionType
) -> Prim | Obj | Arr | J2PUnionType:
    if isinstance(a, J2PUnionType) or isinstance(b, J2PUnionType):
        return _normalize_union([a, b])

    if isinstance(a, Prim) and isinstance(b, Prim):
        if a == b:
            return a
        return _normalize_union([a, b])
    if isinstance(a, Prim) or isinstance(b, Prim):
        return _normalize_union([a, b])

    if (isinstance(a, Arr) and isinstance(b, Obj)) or (
        isinstance(a, Obj) and isinstance(b, Arr)
    ):
        return _normalize_union([a, b])

    if isinstance(a, Arr) and isinstance(b, Arr):
        if a.items is None and b.items is None:
            return Arr(items=None)
        if a.items is None:
            return Arr(items=b.items)
        if b.items is None:
            return Arr(items=a.items)
        combined_items = _combine_nodes(a.items, b.items)
        if isinstance(combined_items, J2PUnionType):
            return Arr(items=combined_items)
        else:
            return Arr(items=J2PUnionType(types=(combined_items,)))

    if isinstance(a, Obj) and isinstance(b, Obj):
        merged: dict[str, Prim | Obj | Arr | J2PUnionType] = {}
        a_map = dict(a.props)
        b_map = dict(b.props)
        all_keys = set(a_map) | set(b_map)
        for k in all_keys:
            merged[k] = _combine_nodes(
                a_map.get(k, Prim(name="null")), b_map.get(k, Prim(name="null"))
            )
        return Obj(props=_sorted_props(merged))

    return _normalize_union([a, b])


def combine_nodes(
    nodes: list[Prim | Obj | Arr | J2PUnionType],
) -> Prim | Obj | Arr | J2PUnionType:
    if len(nodes) == 0:
        raise ValueError("No nodes to combine")
    node = nodes[0]
    for other in nodes[1:]:
        node = _combine_nodes(node, other)
    return node
