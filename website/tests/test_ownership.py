import base64
import json

import pytest

from divination.core import DivinationError
from divination.ownership import OwnershipTokens
from divination.publishing import DeckPublisher
from divination.persona_publishing import PersonaPublisher


PNG_1PX = base64.b64encode(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nWQAAAAASUVORK5CYII=')).decode()


def test_owner_tokens_store_only_hash_and_rotate(tmp_path):
    own = OwnershipTokens()
    token = own.issue(tmp_path)
    raw = (tmp_path / '.owner.json').read_text(encoding='utf-8')
    assert token not in raw
    assert own.verify(tmp_path, token)
    token2 = own.rotate(tmp_path, token)
    assert token2 != token
    assert not own.verify(tmp_path, token)
    assert own.verify(tmp_path, token2)


def test_new_deck_can_be_managed_updated_rotated_and_deleted(tmp_path):
    pub = DeckPublisher(tmp_path)
    out = pub.publish({
        'name':'管理測試牌組', 'persona':'master',
        'cards':[{'title':'一','upright':'主要牌義','image':f'data:image/png;base64,{PNG_1PX}'}]
    })
    token = out['management_token']
    deck_id = out['deck_id']
    assert token and token not in (tmp_path / deck_id / '.owner.json').read_text(encoding='utf-8')
    info = pub.management_info(deck_id, token)
    assert info['name'] == '管理測試牌組'
    pub.update_metadata(deck_id, token, {'name':'新版名稱','description':'新版說明'})
    assert pub.management_info(deck_id, token)['name'] == '新版名稱'
    new_token = pub.rotate_management_token(deck_id, token)
    with pytest.raises(DivinationError):
        pub.management_info(deck_id, token)
    assert pub.management_info(deck_id, new_token)['description'] == '新版說明'
    pub.delete(deck_id, new_token)
    assert not (tmp_path / deck_id).exists()


def test_custom_persona_management_keeps_structured_fields(tmp_path):
    pub = PersonaPublisher(tmp_path)
    out = pub.publish({'name':'月光園丁','role':'夜間引路人','voice':'溫柔','principles':'忠實解讀'})
    token = out['management_token']
    pid = out['persona_id']
    info = pub.management_info(pid, token)
    assert info['name'] == '月光園丁'
    assert 'system_prompt' not in info and 'prompt' not in info
    updated = pub.update(pid, token, {'voice':'簡潔\n溫柔','closing':'留一句提醒'})
    assert updated['voice'] == ['簡潔','溫柔']
    assert updated['closing'] == '留一句提醒'
