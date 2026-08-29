from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ROOT / 'website/public/locales_v10.json'
MAIN = ROOT / 'website/main.js'
TEST = ROOT / 'website/tests/test_ui_locales.py'


def locale(common, nav, hero, labels, introduction, events, groups, footer):
    return {
        'common': common,
        'nav': nav,
        'hero': hero,
        'labels': labels,
        'introduction': introduction,
        'events': events,
        'groups': groups,
        'footer': footer,
    }


def build_ja():
    return locale(
        {
            'nav_logo':'山霊猫','stat_visitors':'訪問者','stat_divinations':'占い','seeker':'相談者','mana':'霊気',
            'btn_draw':'師にカードを開いてもらう','btn_ask':'質問する','btn_share':'🪄 スピリットメモを作成・共有','btn_mint':'記念NFTをミント','btn_reset':'新しい祈り',
            'placeholder_question':'悩みを書き込むか、静かに心を整えてください…','placeholder_chat':'師にさらに尋ねる…','msg_sensing':'師が感じ取っています…','msg_draw_prefix':'師が引いたカードは',
            'label_tarot_meaning':'タロットの意味','label_eco_connection':'ベンガルヤマネコの生態','err_mana_depleted':'⚡ 霊気を使い切りました。','err_empty_question':'師にあなたの問いを聞かせてください！',
            'dharma_prefixes':['森','霧','古寺','山猫','禅','月影','渓谷','そよ風','星','静寂'],
            'dharma_suffixes':['求道者','弟子','隠者','旅人','守り手','友','魂','使者'],
            'share_memo_title':'山霊猫・LeopardCat Tarot','share_seeker_label':'相談者','share_site_tag':'山の精霊とつながり・山猫を守る','share_copy_template':'山霊から啓示を受けました：【{card}】。あなたも山猫とつながってみませんか？'
        },
        {'home':'ホーム','fortune':'占い','gallery':'ギャラリー','intro':'エコ・スピリット'},
        {'title':'山霊猫','subtitle':'ベンガルヤマネコ保護区：生態と心をめぐる旅','cta_fortune':'師に尋ねる','cta_intro':'森へ入る'},
        {'wishing_well':'願いの泉','fortune_title':'山霊猫の師：タロット占い','intro_label':'はじめに','intro_title':'森と魂の守り手','history_label':'記録','history_title':'生態のクロニクル','gallery_label':'ギャラリー','gallery_title':'大アルカナ：山猫の生命の旅'},
        {'description':'ベンガルヤマネコは台湾に現存する唯一の在来ネコ科動物です。アジアに広く分布しますが、台湾では1,000頭未満と推定され、深刻な生存課題に直面しています。各タロットカードは、その生存の物語を映します。','stats':[{'label':'推定個体数','value':'1,000頭未満'},{'label':'保全区分','value':'絶滅危惧野生動物 I 類'},{'label':'主な生息地','value':'苗栗・台中・南投'}]},
        [
            {'date':'2019 - 苗栗','title':'初のロードキル防止フェンス','description':'台13甲線に防護ネットと生態回廊を設置し、継続的な利用が確認されています。','tag':'保全'},
            {'date':'2024 - 台中','title':'高標高での確認記録','description':'標高1,050mで痕跡が確認され、環境配慮型農業による生息域拡大の可能性が示されました。','tag':'発見'},
            {'date':'2025 - 彰化','title':'繁殖個体群を初確認','description':'溪州で幼獣を含む家族が撮影され、新しい生息地への定着が確認されました。','tag':'生態'},
            {'date':'2024 - プロジェクト','title':'AI Leopard Cat Tarot 始動','description':'生成AIアートと神秘学を組み合わせ、台湾の生態保全を伝えるデジタル企画が始まりました。','tag':'デジタルアート'}
        ],
        [
            {'id':'material','title':'第一段階：物質と生存 (0-7)','description':'現実世界での最初の挑戦と社会的つながりを探ります。'},
            {'id':'inner','title':'第二段階：内面と試練 (8-14)','description':'深い谷で孤独と生命の循環に向き合います。'},
            {'id':'cosmic','title':'第三段階：覚醒と調和 (15-21)','description':'災難と夢を越え、人間社会との調和を目指します。'},
            {'id':'wands','title':'ワンド：行動と縄張り','description':'新たな生息地を求める拡張と行動を象徴します。'},
            {'id':'cups','title':'カップ：水と直感','description':'水辺の生息環境、感情、癒し、直感との結びつきを象徴します。'},
            {'id':'swords','title':'ソード：葛藤と判断','description':'人為的な景観の中で必要な洞察と決断を象徴します。'},
            {'id':'pentacles','title':'ペンタクル：資源と安定','description':'食料と安定した生息地という生存基盤を象徴します。'}
        ],
        {'copyright':'© 2026 LeopardCat Tarot Project. All rights reserved.'}
    )


def build_ko():
    return locale(
        {
            'nav_logo':'산령고양이','stat_visitors':'방문자','stat_divinations':'점괘','seeker':'질문자','mana':'영기',
            'btn_draw':'스승에게 카드를 청하기','btn_ask':'질문하기','btn_share':'🪄 영감 메모 만들기·공유','btn_mint':'기념 NFT 민팅','btn_reset':'새 의식',
            'placeholder_question':'고민을 적거나 잠시 마음을 가라앉혀 보세요…','placeholder_chat':'스승에게 더 물어보기…','msg_sensing':'스승이 기운을 읽고 있습니다…','msg_draw_prefix':'스승이 뽑은 카드는',
            'label_tarot_meaning':'타로 의미','label_eco_connection':'삵 생태 연결','err_mana_depleted':'⚡ 영기를 모두 사용했습니다.','err_empty_question':'스승에게 당신의 질문을 들려주세요!',
            'dharma_prefixes':['숲','안개','고찰','삵','선','달빛','계곡','바람','별','고요'],
            'dharma_suffixes':['구도자','제자','은자','나그네','수호자','친구','영혼','전령'],
            'share_memo_title':'산령고양이 · LeopardCat Tarot','share_seeker_label':'질문자','share_site_tag':'산의 영혼과 연결 · 삵 보호','share_copy_template':'산령에게서 계시를 받았습니다: 【{card}】. 당신도 삵과 연결해 보세요!'
        },
        {'home':'홈','fortune':'점괘','gallery':'갤러리','intro':'생태 영혼'},
        {'title':'산령고양이','subtitle':'삵 보호구역: 생태와 마음을 잇는 여정','cta_fortune':'스승에게 묻기','cta_intro':'숲으로 들어가기'},
        {'wishing_well':'소원의 샘','fortune_title':'산령 스승: 타로 리딩','intro_label':'소개','intro_title':'숲과 영혼의 수호자','history_label':'기록','history_title':'생태 연대기','gallery_label':'갤러리','gallery_title':'메이저 아르카나: 삵의 생명 여정'},
        {'description':'삵은 대만에 남아 있는 유일한 토착 야생 고양잇과 동물입니다. 아시아 전역에 분포하지만 대만에는 1,000마리 미만이 남은 것으로 추정되며 심각한 생존 위협에 놓여 있습니다. 각 타로 카드는 그 생존 이야기를 담고 있습니다.','stats':[{'label':'추정 개체수','value':'1,000마리 미만'},{'label':'보전 등급','value':'멸종위기 야생동물 I급'},{'label':'주요 지역','value':'먀오리·타이중·난터우'}]},
        [
            {'date':'2019 - 먀오리','title':'첫 로드킬 방지 울타리','description':'13갑 도로에 보호망과 생태 통로를 설치했고, 모니터링에서 지속적인 이용이 확인되었습니다.','tag':'보전'},
            {'date':'2024 - 타이중','title':'고지대 활동 기록','description':'해발 1,050m에서 흔적이 발견되어 친환경 농업이 서식 범위 확장에 영향을 줄 가능성을 보여 주었습니다.','tag':'발견'},
            {'date':'2025 - 장화','title':'번식 개체군 첫 확인','description':'시저우에서 새끼를 포함한 가족이 촬영되어 새로운 서식지 정착이 확인되었습니다.','tag':'생태'},
            {'date':'2024 - 프로젝트','title':'AI Leopard Cat Tarot 시작','description':'생성형 AI 아트와 신비주의를 결합해 대만 생태 보전을 알리는 디지털 프로젝트가 시작되었습니다.','tag':'디지털 아트'}
        ],
        [
            {'id':'material','title':'1단계: 물질과 생존 (0-7)','description':'현실 세계에서의 첫 도전과 사회적 연결을 탐색합니다.'},
            {'id':'inner','title':'2단계: 내면과 시련 (8-14)','description':'깊은 계곡에서 고독과 삶의 순환을 마주합니다.'},
            {'id':'cosmic','title':'3단계: 각성과 조화 (15-21)','description':'재난과 꿈을 넘어 인간 문명과의 조화를 향합니다.'},
            {'id':'wands','title':'완드: 행동과 영역','description':'새로운 서식지를 찾아 확장하는 행동을 상징합니다.'},
            {'id':'cups','title':'컵: 물과 직관','description':'물가 서식지, 감정, 치유, 직관의 연결을 상징합니다.'},
            {'id':'swords','title':'소드: 갈등과 판단','description':'인간이 바꾼 환경에서 필요한 통찰과 결정을 상징합니다.'},
            {'id':'pentacles','title':'펜타클: 자원과 안정','description':'먹이와 안정적인 서식지라는 생존 기반을 상징합니다.'}
        ],
        {'copyright':'© 2026 LeopardCat Tarot Project. All rights reserved.'}
    )


def build_es():
    return locale(
        {
            'nav_logo':'Espíritu del Monte','stat_visitors':'Visitantes','stat_divinations':'Lecturas','seeker':'Consultante','mana':'Energía',
            'btn_draw':'Pedir al Maestro que revele las cartas','btn_ask':'Preguntar','btn_share':'🪄 Crear y compartir memoria espiritual','btn_mint':'Acuñar NFT conmemorativo','btn_reset':'Nuevo ritual',
            'placeholder_question':'Escribe tu inquietud o toma un momento para centrarte…','placeholder_chat':'Pregunta algo más al Maestro…','msg_sensing':'El Maestro está percibiendo…','msg_draw_prefix':'El Maestro ha sacado',
            'label_tarot_meaning':'Significado del Tarot','label_eco_connection':'Conexión ecológica','err_mana_depleted':'⚡ La energía se ha agotado.','err_empty_question':'¡El Maestro necesita escuchar tu pregunta!',
            'dharma_prefixes':['Bosque','Niebla','Templo','Gato salvaje','Zen','Luna','Valle','Brisa','Estrella','Silencio'],
            'dharma_suffixes':['Buscador','Discípulo','Ermitaño','Viajero','Guardián','Amigo','Alma','Mensajero'],
            'share_memo_title':'Espíritu del Monte · LeopardCat Tarot','share_seeker_label':'Consultante','share_site_tag':'Conecta con el monte · Protege al gato leopardo','share_copy_template':'Recibí una señal del monte: 【{card}】. ¡Ven a conectar con el gato leopardo!'
        },
        {'home':'Inicio','fortune':'Oráculo','gallery':'Galería','intro':'Eco-alma'},
        {'title':'Espíritu del Monte','subtitle':'Santuario del gato leopardo: un viaje ecológico y espiritual','cta_fortune':'Preguntar al Maestro','cta_intro':'Entrar al bosque'},
        {'wishing_well':'Fuente de deseos','fortune_title':'Maestro del Monte: lectura de Tarot','intro_label':'Introducción','intro_title':'Guardián del bosque y del espíritu','history_label':'Historia','history_title':'Crónicas ecológicas','gallery_label':'Galería','gallery_title':'Arcanos Mayores: el viaje de una vida'},
        {'description':'El gato leopardo es el único felino silvestre nativo que aún vive en Taiwán. Aunque se distribuye por Asia, se estima que quedan menos de 1.000 en Taiwán y afrontan graves amenazas. Cada carta del Tarot refleja una parte de esa lucha por sobrevivir.','stats':[{'label':'Población estimada','value':'< 1.000'},{'label':'Estado','value':'Fauna amenazada, Cat. I'},{'label':'Zonas principales','value':'Miaoli, Taichung, Nantou'}]},
        [
            {'date':'2019 - Miaoli','title':'Primer sistema de vallas contra atropellos','description':'Se instalaron redes de protección y corredores ecológicos en la Ruta 13A; el monitoreo muestra un uso frecuente.','tag':'Conservación'},
            {'date':'2024 - Taichung','title':'Nuevo récord de altitud','description':'Se encontraron rastros a 1.050 m, lo que sugiere una expansión del hábitat favorecida por prácticas agrícolas responsables.','tag':'Descubrimiento'},
            {'date':'2025 - Changhua','title':'Primera reproducción confirmada','description':'Imágenes de crías y familias en Xizhou confirmaron el establecimiento en un nuevo hábitat.','tag':'Ecología'},
            {'date':'2024 - Proyecto','title':'Lanzamiento de AI Leopard Cat Tarot','description':'Comenzó un proyecto que combina arte generativo y simbolismo para comunicar la conservación ecológica de Taiwán.','tag':'Arte digital'}
        ],
        [
            {'id':'material','title':'Fase I: Materia y supervivencia (0-7)','description':'Explora los primeros desafíos y vínculos en el mundo físico.'},
            {'id':'inner','title':'Fase II: Pruebas interiores (8-14)','description':'Entra en los valles profundos para afrontar la soledad y los ciclos de la vida.'},
            {'id':'cosmic','title':'Fase III: Despertar y armonía (15-21)','description':'Trasciende desastres y sueños para buscar armonía con la civilización humana.'},
            {'id':'wands','title':'Bastos: acción y territorio','description':'Simbolizan la expansión y la búsqueda de nuevos hábitats.'},
            {'id':'cups','title':'Copas: agua e intuición','description':'Simbolizan el vínculo con el agua, las emociones, la sanación y la intuición.'},
            {'id':'swords','title':'Espadas: conflicto y decisión','description':'Simbolizan la claridad y las decisiones necesarias en paisajes transformados por humanos.'},
            {'id':'pentacles','title':'Oros: recursos y estabilidad','description':'Simbolizan alimento, hábitat estable y bases materiales para sobrevivir.'}
        ],
        {'copyright':'© 2026 LeopardCat Tarot Project. Todos los derechos reservados.'}
    )


data = json.loads(LOCALES.read_text(encoding='utf-8'))
data['ja'] = build_ja()
data['ko'] = build_ko()
data['es'] = build_es()
LOCALES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

js = MAIN.read_text(encoding='utf-8')
old_meta = """window.localeMeta = {\n    zh: { label: '中', htmlLang: 'zh-TW' },\n    en: { label: 'EN', htmlLang: 'en' }\n};"""
new_meta = """window.localeMeta = {\n    zh: { label: '中', htmlLang: 'zh-TW' },\n    en: { label: 'EN', htmlLang: 'en' },\n    ja: { label: '日本語', htmlLang: 'ja' },\n    ko: { label: '한국어', htmlLang: 'ko' },\n    es: { label: 'ES', htmlLang: 'es' }\n};"""
assert old_meta in js
js = js.replace(old_meta, new_meta, 1)

anchor = """function getLocaleData(lang = window.currentLang) {\n    const resolved = resolveLocale(lang);\n    return (window.siteData && window.siteData[resolved]) || {};\n}\n"""
helper = anchor + """\nfunction getAILanguageTag(lang = window.currentLang) {\n    const resolved = resolveLocale(lang);\n    return ({ zh: 'zh-TW', en: 'en', ja: 'ja', ko: 'ko', es: 'es' })[resolved] || resolved || 'en';\n}\n"""
assert anchor in js
js = js.replace(anchor, helper, 1)
js = js.replace("lang: window.currentLang === 'zh' ? 'zh-TW' : 'en'", "lang: getAILanguageTag()")

# Keep the provider-state message understandable in every newly supported UI locale.
old_err = """function modularErrorMessage(e) {\n    if (e?.code === 'provider_429_billing_or_quota_state' || e?.status === 429) {\n        return window.currentLang === 'zh'\n            ? 'Gemini 目前回報供應商端額度／帳務狀態異常。牌局已保留，稍後可沿用同一副牌重新祈請。'\n            : 'Gemini is currently reporting a provider quota or billing-state issue. Your draw is preserved for retry.';\n    }\n"""
new_err = """function modularErrorMessage(e) {\n    if (e?.code === 'provider_429_billing_or_quota_state' || e?.status === 429) {\n        const messages = {\n            zh: 'Gemini 目前回報供應商端額度／帳務狀態異常。牌局已保留，稍後可沿用同一副牌重新祈請。',\n            en: 'Gemini is currently reporting a provider quota or billing-state issue. Your draw is preserved for retry.',\n            ja: 'Gemini 側で割り当て／請求状態の問題が報告されています。カード結果は保持されているため、後でもう一度試せます。',\n            ko: 'Gemini 공급자 측 할당량/결제 상태 문제가 보고되고 있습니다. 카드 결과는 유지되므로 나중에 다시 시도할 수 있습니다.',\n            es: 'Gemini informa de un problema de cuota o facturación del proveedor. La tirada se conserva para volver a intentarlo más tarde.'\n        };\n        return messages[resolveLocale(window.currentLang)] || messages.en;\n    }\n"""
assert old_err in js
js = js.replace(old_err, new_err, 1)
MAIN.write_text(js, encoding='utf-8')

TEST.write_text("""import json\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\n\n\ndef test_public_ui_has_five_locales_with_matching_shape():\n    data = json.loads((ROOT / 'public' / 'locales_v10.json').read_text(encoding='utf-8'))\n    assert set(['zh','en','ja','ko','es']).issubset(data)\n    reference = data['en']\n    for lang in ('ja','ko','es'):\n        assert set(data[lang]) == set(reference)\n        assert set(data[lang]['common']) == set(reference['common'])\n        assert set(data[lang]['nav']) == set(reference['nav'])\n        assert set(data[lang]['hero']) == set(reference['hero'])\n        assert set(data[lang]['labels']) == set(reference['labels'])\n        assert [g['id'] for g in data[lang]['groups']] == [g['id'] for g in reference['groups']]\n\n\ndef test_runtime_exposes_switcher_and_ai_language_tags():\n    js = (ROOT / 'main.js').read_text(encoding='utf-8')\n    for token in (\"ja: { label: '日本語'\", \"ko: { label: '한국어'\", \"es: { label: 'ES'\"):\n        assert token in js\n    assert 'function getAILanguageTag' in js\n    assert \"ja: 'ja'\" in js and \"ko: 'ko'\" in js and \"es: 'es'\" in js\n    assert \"window.currentLang === 'zh' ? 'zh-TW' : 'en'\" not in js\n""", encoding='utf-8')
