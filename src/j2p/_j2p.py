from collections import defaultdict
from dataclasses import dataclass

from j2p._parse_json import Obj, Prim, J2PUnionType, Arr


@dataclass(frozen=True)
class Schema:
    name: str
    fields: list[tuple[str, str]]


def generate_pydantic_models(schema: Obj, root_name: str = "Root") -> str:
    schemas = flatten_obj(schema, root_name)
    schemas.reverse()
    lines = ["from pydantic import BaseModel", "from typing import Any", ""]

    for schema in reversed(schemas):
        lines.append(f"class {schema.name}(BaseModel):")
        if not schema.fields:
            lines.append("    pass")
        else:
            for field_name, field_type in schema.fields:
                lines.append(f"    {field_name}: {field_type}")
        lines.append("")

    return "\n".join(lines)


def flatten_obj(obj: Obj, parent_name: str = "Root") -> list[Schema]:
    schemas: list[Schema] = []
    usage_counter = defaultdict(int)

    def _flatten(t: Obj | Arr | Prim | J2PUnionType, curr_name: str) -> str:
        if isinstance(t, Obj):
            usage_counter[curr_name] += 1
            name = (
                curr_name
                if usage_counter[curr_name] == 1
                else f"{curr_name}{usage_counter[curr_name]}"
            )
            schema = Schema(name=name, fields=[])
            for prop_name, prop_type in t.props:
                schema.fields.append(
                    (
                        prop_name,
                        _flatten(prop_type, f"{curr_name}{prop_name.capitalize()}"),
                    )
                )
            schemas.append(schema)
            return name
        elif isinstance(t, J2PUnionType):
            types = []
            for subtype in t.types:
                types.append(_flatten(subtype, curr_name))
            return " | ".join(types)
        elif isinstance(t, Arr):
            if t.items is None:
                return "list[Any]"
            else:
                item_type = _flatten(t.items, f"{curr_name}Item")
                return f"list[{item_type}]"
        else:
            return str(t)

    _flatten(obj, parent_name)

    return schemas
