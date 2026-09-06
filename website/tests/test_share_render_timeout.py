from pathlib import Path


def test_mobile_share_render_has_safari_budget_and_shared_timeout_wrapper():
    src = Path(__file__).parents[1].joinpath('main.js').read_text(encoding='utf-8')
    assert 'function shareRenderBudgetMs()' in src
    assert 'mobileSafari ? 60000 : 35000' in src
    assert "renderShareCanvas(template, {" in src
    assert "}, 'square');" in src
    assert "}, 'og');" in src
    assert "reject(new Error('TIMEOUT')), 20000" not in src
