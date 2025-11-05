import argparse
import sys
import json
from j2p._parse_json import combine_nodes, parse_json
from j2p._j2p import generate_pydantic_models

def main():
    parser = argparse.ArgumentParser(
        description="Json 2 Pydantic: Generate Pydantic models from JSON file(s)"
    )

    # Positional argument for JSON files
    parser.add_argument(
        "json_files",
        nargs="+",  # means one or more values
        help="Paths to JSON files to process"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file to write the generated Pydantic models (default: stdout)"
    )

    args = parser.parse_args()

    json_data_list = []

    for file_path in args.json_files:
        try:
            with open(file_path, "r") as f:
                json_data_list.append(json.load(f))
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            sys.exit(1)

    parsed_nodes = [parse_json(data) for data in json_data_list]
    combined_node = combine_nodes(parsed_nodes)
    pydantic_models = generate_pydantic_models(combined_node)

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(pydantic_models)
        except Exception as e:
            print(f"Error writing to {args.output}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(pydantic_models)