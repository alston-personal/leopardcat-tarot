import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'website'))

from divination.ai_gateway import ZeroCostGeminiGateway
from divination.themes import ThemePublisher, ThemeRegistry


def test_zero_cost_gateway_has_no_paid_fallback():
    g = ZeroCostGeminiGateway('fake')
    p = g.policy()
    assert p['cost_policy'] == 'zero-cost-required'
    assert p['paid_fallback'] is False
    assert p['billing_state_detectable_by_runtime'] is False


def test_custom_theme_round_trip():
    pixel = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Zl8sAAAAASUVORK5CYII='
    with tempfile.TemporaryDirectory() as td:
        pub = ThemePublisher(td)
        out = pub.publish({'name':'測試主題','colors':{'background':'#112233','accent':'#abcdef'},'background_image':pixel})
        reg = ThemeRegistry(td)
        got = reg.get(out['theme_id'])
        assert got['name'] == '測試主題'
        assert got['colors']['background'] == '#112233'
        assert got['background_image'].startswith('/api/v1/themes/')


def test_builtin_theme_switchable():
    with tempfile.TemporaryDirectory() as td:
        reg = ThemeRegistry(td)
        ids = {x['theme_id'] for x in reg.list_builtin()}
        assert {'leopardcat','midnight','minimal-light'} <= ids
