from __future__ import annotations

import argparse

from .migration import import_legacy_leopardcat_cards
from .packs import save_subject_pack


def main() -> None:
    parser = argparse.ArgumentParser(prog="arcana-forge-migrate-leopardcat")
    parser.add_argument("cards_dir", help="legacy leopardcat-tarot generator/cards directory")
    parser.add_argument("output", help="output ArcanaForge subject-pack JSON")
    args = parser.parse_args()
    pack = import_legacy_leopardcat_cards(args.cards_dir)
    target = save_subject_pack(pack, args.output)
    print(f"migrated_card_count={pack.metadata['migrated_card_count']}")
    print(f"subject_pack={target}")
