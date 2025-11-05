from j2p._j2p import generate_pydantic_models
from j2p._parse_json import parse_json, combine_nodes


def test_j2p():
    dict1 = {"name": "Alice", "age": 30, "active": True, "roles": ["admin", "editor"]}

    dict2 = {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "roles": ["viewer"],
        "preferences": {"theme": "dark", "notifications": True},
    }

    dict3 = {
        "age": 31,
        "address": {"city": "New York", "zip": "10001"},
        "preferences": {"notifications": False, "language": "en"},
    }

    dict4 = {
        "projects": [
            {"id": 1, "title": "Schema Merge"},
            {"id": 2, "title": "API Refactor"},
        ],
        "active": False,
    }

    dict5 = {
        "roles": ["contributor", "admin"],
        "metadata": {
            "created_at": "2024-06-15T10:00:00Z",
            "last_login": "2025-11-01T08:30:00Z",
        },
    }

    obj1 = parse_json(dict1)
    obj2 = parse_json(dict2)
    obj3 = parse_json(dict3)
    obj4 = parse_json(dict4)
    obj5 = parse_json(dict5)

    combined_obj = combine_nodes([obj1, obj2, obj3, obj4, obj5])

    print(combined_obj)

    result = generate_pydantic_models(combined_obj)
    print(result)
