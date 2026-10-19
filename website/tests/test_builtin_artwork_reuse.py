from pathlib import Path

import pytest

from divination.core import DivinationError
from divination.publishing import DeckPublisher


def test_builtin_artwork_reference_does_not_copy_images(tmp_path):
    publisher = DeckPublisher(tmp_path)
    result = publisher.publish({
        "name": "Reuse LeopardCat Artwork",
        "slug": "reuse-leopardcat-test",
        "persona": "master",
        "cards": [{
            "title": "愚者",
            "upright": "新的開始",
            "reversed": "謹慎評估",
            "image_ref": "card-00-the-fool",
        }],
        "reversals": True,
    })
    data = (tmp_path / result["deck_id"] / "deck.json").read_text(encoding="utf-8")
    assert '"/art/renders/card-00-the-fool.png"' in data
    assert not list((tmp_path / result["deck_id"] / "images").iterdir())


@pytest.mark.parametrize("image_ref", ["../../etc/passwd", "no-such-card", "https://example.org/image.png"])
def test_builtin_artwork_rejects_non_manifest_reference(tmp_path, image_ref):
    publisher = DeckPublisher(tmp_path)
    with pytest.raises(DivinationError):
        publisher.publish({
            "name": "Rejected",
            "cards": [{"title": "Card", "upright": "Meaning", "image_ref": image_ref}],
        })
