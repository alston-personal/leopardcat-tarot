import json

from .forge import forge
from .exporters.divination_os import export_divination_os


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(prog="arcana-forge")
    parser.add_argument("system", choices=["tarot-rws", "iching-zhouyi"])
    parser.add_argument("subject")
    parser.add_argument("style")
    parser.add_argument("--title")
    parser.add_argument("--divination-os-id")
    args = parser.parse_args()
    collection = forge(system=args.system, subject=args.subject, style=args.style, title=args.title)
    payload = (
        export_divination_os(collection, collection_id=args.divination_os_id)
        if args.divination_os_id else collection.to_manifest()
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
