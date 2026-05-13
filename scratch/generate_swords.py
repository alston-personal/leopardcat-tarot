import json
import os

template_path = "/home/ubuntu/leopardcat-tarot/generator/cards/card-sw-04-four-of-swords.json"
with open(template_path, 'r') as f:
    template = json.load(f)

swords_data = {
    "05": {
        "title_zh": "寶劍五",
        "title_en": "FIVE OF SWORDS",
        "subtitle": "Conflict & Loss",
        "image_prompt": "Two Taiwan leopard cats standing upright and engaged in a tense territorial dispute at the edge of a forest. One cat stands triumphantly with three swords, while the other walks away defeated with two swords. Cold, gray sky. Tense atmosphere.",
        "narrative": "The Five of Swords is 'The Dispute'—the unfortunate reality of intraspecific competition when habitat fragments become too small to support multiple territories.",
        "mapping_note": "Five of Swords represents 'Territorial Compression'—the friction caused when leopard cats are forced into overlapping ranges due to habitat loss.",
        "zh_meaning": "衝突、背叛、不名譽的勝利，以及在破碎棲地中的資源爭奪。",
        "en_meaning": "Conflict, betrayal, winning at a cost, and the struggle for resources in fragmented habitats."
    },
    "06": {
        "title_zh": "寶劍六",
        "title_en": "SIX OF SWORDS",
        "subtitle": "Transition & Passage",
        "image_prompt": "A Taiwan leopard cat standing upright and steering a small boat across a misty river at dawn. Five swords are planted in the boat, and one is held as a rudder. A younger leopard cat sits in the boat looking toward a lush, safe-looking forest on the far shore.",
        "narrative": "The Six of Swords is 'The Safe Passage'—the journey from a high-risk, fragmented area to a larger, protected core habitat.",
        "mapping_note": "Six of Swords represents 'Corridor Connectivity'—the vital movement of individuals through safe passages to reach sustainable population patches.",
        "zh_meaning": "遠行、渡過難關、療癒，以及透過生態廊道前往安全棲地的旅程。",
        "en_meaning": "Transition, moving on, healing, and the journey to safer habitats via ecological corridors."
    },
    "07": {
        "title_zh": "寶劍七",
        "title_en": "SEVEN OF SWORDS",
        "subtitle": "Strategy & Stealth",
        "image_prompt": "A Taiwan leopard cat standing upright and sneaking away from a farm camp at night, carrying five silver swords in its arms while looking back at two other swords left behind. Moonlit farm setting with a chicken coop in the background.",
        "narrative": "The Seven of Swords is 'The Midnight Raid'—the calculated risk of entering human settlements to find food, a major source of human-animal conflict.",
        "mapping_note": "Seven of Swords represents 'Border Risk'—the opportunistic behavior of raiding domestic livestock when natural prey is scarce.",
        "zh_meaning": "逃避、策略、不誠實，以及在人類聚落邊緣尋找生存機會的冒險。",
        "en_meaning": "Deception, strategy, stealth, and taking risks at the human-animal interface."
    },
    "08": {
        "title_zh": "寶劍八",
        "title_en": "EIGHT OF SWORDS",
        "subtitle": "Interference & Trap",
        "image_prompt": "A Taiwan leopard cat standing upright, blindfolded and loosely bound by vines, surrounded by eight silver swords stuck in the muddy ground like a cage. Background shows a construction site with heavy machinery silhouettes.",
        "narrative": "The Eight of Swords is 'The Invisible Trap'—the feeling of being surrounded by human encroachment and the physical danger of snares.",
        "mapping_note": "Eight of Swords represents 'Anthropogenic Pressure'—the psychological and physical restrictions placed on wildlife by roads and traps.",
        "zh_meaning": "受困、孤立、自我限制，以及被人類設施與獸夾圍困的真實威脅。",
        "en_meaning": "Imprisonment, isolation, restriction, and the physical threat of traps and development."
    },
    "09": {
        "title_zh": "寶劍九",
        "title_en": "NINE OF SWORDS",
        "subtitle": "Anxiety & Nightmares",
        "image_prompt": "A Taiwan leopard cat sitting upright in its den, paws covering its face in deep distress. Nine silver swords hang horizontally on the wall above it. The den is illuminated by the harsh artificial glow of distant streetlights.",
        "narrative": "The Nine of Swords is 'The Urban Stress'—the chronic anxiety caused by light and noise pollution that disrupts the cat's natural nocturnal life.",
        "mapping_note": "Nine of Swords represents 'Sensory Overload'—the impact of light pollution and road noise on the mental well-being of nocturnal predators.",
        "zh_meaning": "憂慮、噩夢、絕望，以及環境噪音與光害造成的長期生存壓力。",
        "en_meaning": "Anxiety, nightmares, despair, and the chronic stress caused by urban light and noise."
    },
    "10": {
        "title_zh": "寶劍十",
        "title_en": "TEN OF SWORDS",
        "subtitle": "The Tragic End",
        "image_prompt": "A symbolic illustration of a fallen Taiwan leopard cat lying at the edge of a dark asphalt road. Ten silver swords are pierced through its back. A cold, dark sky with a waning moon. This is a solemn educational image.",
        "narrative": "The Ten of Swords is 'The Final Toll'—the ultimate tragedy of roadkill, representing the lowest point for a population's survival.",
        "mapping_note": "Ten of Swords represents 'Roadkill Mortality'—the most severe threat to leopard cats, serving as a powerful warning of the cost of fragmentation.",
        "zh_meaning": "慘敗、背叛、痛苦的終結，以及路殺與中毒帶來的族群存續危機。",
        "en_meaning": "Backstabbing, defeat, a painful ending, and the population crisis caused by roadkill."
    },
    "11": {
        "title_zh": "寶劍侍者",
        "title_en": "PAGE OF SWORDS",
        "subtitle": "Vigilance & Curiosity",
        "image_prompt": "A young Taiwan leopard cat standing upright in a grassy field, holding a single silver sword and curiously sniffing a scientific camera trap mounted on a tree. Alert ears and wide eyes.",
        "narrative": "The Page of Swords is 'The Young Watcher'—the curiosity of the next generation as they learn to navigate a landscape monitored by humans.",
        "mapping_note": "Page of Swords represents 'Ecological Monitoring'—the interaction between wildlife and the tools used to study and protect them.",
        "zh_meaning": "警覺、好奇、消息靈通，以及新一代個體對環境監測設施的探索。",
        "en_meaning": "Vigilance, curiosity, mental agility, and the exploration of monitoring tools."
    },
    "12": {
        "title_zh": "寶劍騎士",
        "title_en": "KNIGHT OF SWORDS",
        "subtitle": "Swift Action",
        "image_prompt": "A Taiwan leopard cat knight standing upright and riding a charging feline-proportioned horse through a dark concrete culvert under a road. He holds a silver sword forward like a lance. Intense momentum and speed.",
        "narrative": "The Knight of Swords is 'The Culvert Runner'—the rapid, decisive movement required to cross dangerous human infrastructure safely.",
        "mapping_note": "Knight of Swords represents 'Adaptive Movement'—the swift use of drainage culverts as safe underpasses to navigate roads.",
        "zh_meaning": "急躁、衝動、迅速行動，以及在危險設施中快速穿梭的適應力。",
        "en_meaning": "Haste, impulsiveness, swift action, and adaptive navigation through dangerous infrastructure."
    },
    "13": {
        "title_zh": "寶劍皇后",
        "title_en": "QUEEN OF SWORDS",
        "subtitle": "Independence & Insight",
        "image_prompt": "A regal female Taiwan leopard cat seated upright on a throne made of sharp gray stone. She holds a single silver sword vertically in one hand and gestures with the other. Her gaze is piercing and intelligent. Cold mountain background.",
        "narrative": "The Queen of Swords is 'The Lone Protector'—the fiercely independent female who manages her territory with sharp insight and unwavering boundaries.",
        "mapping_note": "Queen of Swords represents 'Female Philopatry'—the strong territorial bonds and independent survival of female leopard cats.",
        "zh_meaning": "獨立、清晰的思考、判斷力，以及守護領地的堅定意志。",
        "en_meaning": "Independence, clear thinking, judgment, and the fierce protection of territory."
    },
    "14": {
        "title_zh": "寶劍國王",
        "title_en": "KING OF SWORDS",
        "subtitle": "Authority & Strategy",
        "image_prompt": "A powerful male Taiwan leopard cat seated upright on a throne decorated with eagle motifs. He holds a large silver sword. He looks out over a complex map-like landscape of forest and farms. Authoritative and strategic posture.",
        "narrative": "The King of Swords is 'The Landscape Master'—the veteran male who successfully navigates the complex web of human and natural boundaries.",
        "mapping_note": "King of Swords represents 'Territorial Mastery'—the strategic management of large ranges across complex, human-modified landscapes.",
        "zh_meaning": "權威、邏輯、戰略家，以及對複雜地景邊界的精確掌握。",
        "en_meaning": "Authority, logic, strategic thinking, and mastery over complex landscape boundaries."
    }
}

for num, data in swords_data.items():
    card = template.copy()
    card["id"] = f"card-sw-{num}-{'of-'.join(data['title_en'].lower().split())}"
    card["number"] = 200 + int(num)
    card["title"]["zh"] = data["title_zh"]
    card["title"]["en"] = data["title_en"]
    card["subtitle"] = data["subtitle"]
    card["slug"] = '-'.join(data['title_en'].lower().split())
    card["status"] = "prompt_ready"
    card["generation"]["image_prompt"] = data["image_prompt"]
    card["generation"]["narrative"] = data["narrative"]
    card["ecology"]["mapping_note"] = data["mapping_note"]
    card["meaning"]["zh"] = data["zh_meaning"]
    card["meaning"]["en"] = data["en_meaning"]
    card["main_image"] = f"art/generated/card-sw-{num}-{card['slug']}.png"
    
    file_name = f"card-sw-{num}-{card['slug']}.json"
    file_path = os.path.join("/home/ubuntu/leopardcat-tarot/generator/cards/", file_name)
    
    with open(file_path, 'w') as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
    print(f"Created {file_name}")
