from pathlib import Path

css_path = Path('website/style.css')
css = css_path.read_text()
marker = '/* === Ritual Reading Setup v2 === */'
if marker not in css:
    css += r'''

/* === Ritual Reading Setup v2 === */
#reading-config-card.reading-config-card {
  position: relative;
  display: flex !important;
  flex-direction: column;
  gap: 0;
  margin: 18px 0 0;
  padding: 22px 20px 20px;
  overflow: visible;
  border: 1px solid rgba(212,175,55,.34);
  border-radius: 24px 24px 10px 10px;
  background:
    radial-gradient(circle at 50% 0%, rgba(212,175,55,.12), transparent 34%),
    linear-gradient(180deg, rgba(12,19,15,.94), rgba(2,7,5,.98));
  box-shadow: inset 0 1px rgba(255,255,255,.035), 0 20px 50px rgba(0,0,0,.28);
}
#reading-config-card.reading-config-card::before {
  content: '占卜設定';
  display: block;
  margin: 0 0 18px;
  color: rgba(226,190,66,.92);
  font-size: .76rem;
  font-weight: 700;
  letter-spacing: .24em;
  text-align: center;
}
#reading-config-card .reading-config-group {
  position: relative;
  padding: 18px 0 20px;
  border: 0;
  border-radius: 0;
  background: transparent;
}
#reading-config-card .reading-config-group + .reading-config-group {
  border-top: 1px solid rgba(212,175,55,.12);
}
#reading-config-card .reading-config-spread::before,
#reading-config-card .reading-config-mode::before {
  position: absolute;
  top: 20px;
  left: 0;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(212,175,55,.34);
  border-radius: 50%;
  color: #e3bf48;
  background: rgba(212,175,55,.06);
  font-size: .58rem;
  font-weight: 800;
  letter-spacing: .04em;
}
#reading-config-card .reading-config-spread::before { content: '01'; }
#reading-config-card .reading-config-mode::before { content: '02'; }
#reading-config-card .legacy-spread-picker {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px !important;
  padding: 0 0 0 42px !important;
}
#reading-config-card .legacy-spread-label {
  grid-column: 1 / -1;
  margin: 0 0 4px;
  color: rgba(244,241,234,.78);
  font-size: .78rem;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: none;
}
#reading-config-card .legacy-spread-btn {
  position: relative;
  min-height: 116px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 56px 12px 14px !important;
  border: 1px solid rgba(212,175,55,.18) !important;
  border-radius: 16px !important;
  background: rgba(255,255,255,.018) !important;
  color: rgba(244,241,234,.76) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.018);
  overflow: hidden;
}
#reading-config-card .legacy-spread-btn::before {
  content: '';
  position: absolute;
  top: 16px;
  left: 50%;
  width: 28px;
  height: 42px;
  transform: translateX(-50%);
  border: 1px solid rgba(230,197,85,.55);
  border-radius: 4px;
  background: linear-gradient(145deg, rgba(230,197,85,.15), rgba(230,197,85,.025));
  box-shadow: 0 5px 14px rgba(0,0,0,.22);
}
#reading-config-card [data-spread-choice="three_card"]::before {
  width: 24px;
  box-shadow:
    -22px 5px 0 -1px rgba(8,13,10,1), -22px 5px 0 0 rgba(230,197,85,.48),
     22px 5px 0 -1px rgba(8,13,10,1),  22px 5px 0 0 rgba(230,197,85,.48),
     0 5px 14px rgba(0,0,0,.22);
}
#reading-config-card .draw-mode-picker .legacy-spread-btn::before {
  width: 42px;
  height: 42px;
  border-radius: 50%;
}
#reading-config-card [data-draw-mode="auto"]::before {
  content: '✦';
  display: grid;
  place-items: center;
  color: rgba(230,197,85,.9);
  font-size: 1.1rem;
  background: radial-gradient(circle, rgba(230,197,85,.16), rgba(230,197,85,.02));
}
#reading-config-card [data-draw-mode="manual"]::before {
  content: '☝';
  display: grid;
  place-items: center;
  color: rgba(230,197,85,.9);
  font-size: 1rem;
  background: radial-gradient(circle, rgba(230,197,85,.16), rgba(230,197,85,.02));
}
#reading-config-card [data-draw-mode="auto"]::after,
#reading-config-card [data-draw-mode="manual"]::after,
#reading-config-card [data-spread-choice="single"]::after,
#reading-config-card [data-spread-choice="three_card"]::after {
  display: block;
  color: rgba(244,241,234,.46);
  font-size: .62rem;
  font-weight: 500;
  line-height: 1.35;
}
#reading-config-card [data-spread-choice="single"]::after { content: '聚焦一個核心訊息'; }
#reading-config-card [data-spread-choice="three_card"]::after { content: '看見脈絡與前後關係'; }
#reading-config-card [data-draw-mode="auto"]::after { content: '由大師替你抽取此刻的牌'; }
#reading-config-card [data-draw-mode="manual"]::after { content: '親手洗牌，憑直覺選牌'; }
#reading-config-card .legacy-spread-btn:hover {
  transform: translateY(-2px);
  border-color: rgba(212,175,55,.46) !important;
}
#reading-config-card .legacy-spread-btn.active {
  color: #f7e9a7 !important;
  background: linear-gradient(180deg, rgba(212,175,55,.12), rgba(212,175,55,.035)) !important;
  border-color: rgba(235,201,82,.66) !important;
  box-shadow: inset 0 0 0 1px rgba(235,201,82,.08), 0 8px 22px rgba(0,0,0,.22);
}
#reading-config-card .legacy-spread-btn.active::before {
  border-color: rgba(255,220,101,.92);
  box-shadow: 0 0 20px rgba(212,175,55,.16);
}
#reading-config-card .manual-draw-stage {
  margin: 2px 0 0;
  padding: 18px 0 4px;
  border-top: 1px solid rgba(212,175,55,.12);
}
#reading-config-card + #btn-primary-draw {
  position: relative;
  z-index: 2;
  width: min(86%, 420px);
  min-height: 58px;
  margin: -1px auto 28px;
  border-radius: 0 0 22px 22px;
  border-top-color: rgba(212,175,55,.18);
  background: linear-gradient(135deg, #f0d471, #c9a23a);
  box-shadow: 0 16px 32px rgba(0,0,0,.22), 0 0 0 1px rgba(212,175,55,.1);
  font-size: .92rem;
  letter-spacing: .13em;
}
@media (max-width: 620px) {
  #reading-config-card.reading-config-card {
    margin-left: 4px;
    margin-right: 4px;
    padding: 18px 14px 16px !important;
    border-radius: 22px 22px 8px 8px !important;
  }
  #reading-config-card.reading-config-card::before { margin-bottom: 10px; }
  #reading-config-card .reading-config-group { padding: 16px 0 18px; }
  #reading-config-card .reading-config-spread::before,
  #reading-config-card .reading-config-mode::before { top: 17px; }
  #reading-config-card .legacy-spread-picker {
    padding-left: 38px !important;
    gap: 9px !important;
  }
  #reading-config-card .legacy-spread-btn {
    min-height: 108px;
    padding: 54px 8px 12px !important;
    font-size: .83rem;
  }
  #reading-config-card [data-draw-mode="auto"]::after,
  #reading-config-card [data-draw-mode="manual"]::after,
  #reading-config-card [data-spread-choice="single"]::after,
  #reading-config-card [data-spread-choice="three_card"]::after {
    font-size: .56rem;
  }
  #reading-config-card + #btn-primary-draw {
    width: calc(100% - 38px);
    margin-top: -1px;
    min-height: 58px;
  }
}
'''
    css_path.write_text(css)

# Focused source-level regression that protects structure/controller IDs and v2 visual contract.
test_path = Path('website/tests/test_reading_setup_v2.py')
test_path.write_text(r'''from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text()
CSS = (ROOT / 'style.css').read_text()


def test_controller_ids_preserved():
    for token in ('id="reading-config-card"', 'id="legacy-spread-picker"', 'id="draw-mode-picker"', 'id="manual-draw-stage"', 'id="btn-primary-draw"'):
        assert token in HTML


def test_ritual_setup_v2_visual_contract():
    assert '/* === Ritual Reading Setup v2 === */' in CSS
    assert '[data-spread-choice="three_card"]::before' in CSS
    assert '[data-draw-mode="auto"]::after' in CSS
    assert '#reading-config-card + #btn-primary-draw' in CSS
    assert '@media (max-width: 620px)' in CSS
''')
