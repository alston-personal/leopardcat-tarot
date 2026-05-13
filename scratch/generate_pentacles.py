import json
import os

template_path = "/home/ubuntu/leopardcat-tarot/generator/cards/card-sw-04-four-of-swords.json"
with open(template_path, 'r') as f:
    template = json.load(f)

pentacles_data = {
    "01": {
        "title_zh": "錢幣一",
        "title_en": "ACE OF PENTACLES",
        "subtitle": "Material Gift / Abundance",
        "image_prompt": "A plump Taiwan leopard cat standing upright in a lush, grassy field. It holds a large, golden-brown vole (prey) in its paws with care. The background shows a healthy secondary forest. Sunlight filters through the leaves. Grounded and prosperous atmosphere.",
        "narrative": "The Ace of Pentacles is 'The Gift of the Land'—the discovery of a prey-rich habitat that provides the material basis for survival.",
        "mapping_note": "Ace of Pentacles represents 'Resource Availability'—the fundamental ecological requirement of a healthy prey base for leopard cat persistence.",
        "zh_meaning": "新的財務機會、繁榮、健康、以及大地帶來的生存資源。",
        "en_meaning": "A new material opportunity, prosperity, health, and the abundance of survival resources."
    },
    "02": {
        "title_zh": "錢幣二",
        "title_en": "TWO OF PENTACLES",
        "subtitle": "Balance & Resource Management",
        "image_prompt": "A Taiwan leopard cat standing upright and skillfully juggling two golden circular emblems (pentacles). Background shows a landscape transitioning between a farm and a forest. The cat looks agile and focused, managing its time between two habitat types.",
        "narrative": "The Two of Pentacles is 'The Habitat Balance'—the ability of an individual to manage its time and energy between different hunting and resting patches.",
        "mapping_note": "Two of Pentacles represents 'Temporal Activity Mapping'—how leopard cats adjust their behavior to exploit different resources throughout the day.",
        "zh_meaning": "平衡、多任務處理、適應變化，以及在不同棲地間分配生存能量。",
        "en_meaning": "Balance, multitasking, adaptability, and managing energy across different habitat patches."
    },
    "03": {
        "title_zh": "錢幣三",
        "title_en": "THREE OF PENTACLES",
        "subtitle": "Collaboration / Teamwork",
        "image_prompt": "Three Taiwan leopard cats standing upright and looking at a large ecological map or blueprint on a wooden table. They are in a forest workshop. One holds a compass, another a drafting tool. Symbolizes the collaboration between different conservation stakeholders.",
        "narrative": "The Three of Pentacles is 'The Collaborative Effort'—the successful synergy between local communities, researchers, and government agencies to restore habitat.",
        "mapping_note": "Three of Pentacles represents 'Stakeholder Integration'—the multi-disciplinary cooperation required for large-scale conservation success.",
        "zh_meaning": "團隊合作、專業技能、認可，以及跨領域合作帶來的生態復育成果。",
        "en_meaning": "Teamwork, collaboration, mastery, and the results of multi-disciplinary conservation efforts."
    },
    "04": {
        "title_zh": "錢幣四",
        "title_en": "FOUR OF PENTACLES",
        "subtitle": "Security & Conservation",
        "image_prompt": "A Taiwan leopard cat standing upright and holding one large golden pentacle tightly against its chest, with two others under its feet and one on its head. It stands on the boundary of a protected core forest. Protective and possessive posture.",
        "narrative": "The Four of Pentacles is 'The Territory Guard'—the impulse to fiercely protect and hold onto a secure core habitat, preventing any encroachment.",
        "mapping_note": "Four of Pentacles represents 'Territorial Fidelity'—the strong attachment to high-quality core areas that provide safety and food.",
        "zh_meaning": "控制、穩定、安全感、以及對核心資源與領地的堅定守護。",
        "en_meaning": "Control, stability, security, and the steadfast protection of core resources and territory."
    },
    "05": {
        "title_zh": "錢幣五",
        "title_en": "FIVE OF PENTACLES",
        "subtitle": "Scarcity & Hardship",
        "image_prompt": "Two Taiwan leopard cats standing upright and walking through a cold, barren landscape with dry, cracked earth and leafless trees. They look weary and hungry. In the background, a warm, brightly lit building (human dwelling) is visible but unreachable. Somber and cold atmosphere.",
        "narrative": "The Five of Pentacles is 'The Lean Season'—the struggle for survival during drought or winter when prey is scarce and habitat quality is poor.",
        "mapping_note": "Five of Pentacles represents 'Environmental Stress'—the impact of climate change and habitat degradation on resource availability.",
        "zh_meaning": "貧困、疾病、疏離、以及在極端環境下對生存資源的艱難尋求。",
        "en_meaning": "Poverty, illness, isolation, and the difficult search for resources in extreme environments."
    },
    "06": {
        "title_zh": "錢幣六",
        "title_en": "SIX OF PENTACLES",
        "subtitle": "Generosity & Balance",
        "image_prompt": "A Taiwan leopard cat standing upright and distributing small pieces of prey (or golden coins) to two younger leopard cats. It holds a pair of scales in the other hand. Setting is a peaceful, sun-dappled forest floor. Balanced and benevolent energy.",
        "narrative": "The Six of Pentacles is 'The Shared Bounty'—the equitable distribution of resources within a population, or the maternal care of sharing food with offspring.",
        "mapping_note": "Six of Pentacles represents 'Altruistic Provisioning'—maternal investment and the sharing of resources to ensure the survival of the next generation.",
        "zh_meaning": "慷慨、分享、慈善、以及族群內部與世代間的資源互助。",
        "en_meaning": "Generosity, sharing, charity, and the mutual aid of resources within a population."
    },
    "07": {
        "title_zh": "錢幣七",
        "title_en": "SEVEN OF PENTACLES",
        "subtitle": "Patience & Evaluation",
        "image_prompt": "A Taiwan leopard cat standing upright and leaning on a wooden staff, looking thoughtfully at a vine growing on a wall with seven golden pentacles ripening like fruit. It looks patient and evaluative. Background shows a newly restored habitat.",
        "narrative": "The Seven of Pentacles is 'The Long Game'—the patience required after habitat restoration, waiting for the ecosystem to mature and the population to grow.",
        "mapping_note": "Seven of Pentacles represents 'Ecological Succession'—the time-lag between restoration actions and the measurable recovery of biodiversity.",
        "zh_meaning": "耐心、評估、長遠的回報，以及對復育成果的細心觀察與等待。",
        "en_meaning": "Patience, evaluation, long-term reward, and waiting for the fruits of restoration efforts."
    },
    "08": {
        "title_zh": "錢幣八",
        "title_en": "錢幣八",
        "subtitle": "Diligence & Skill",
        "image_prompt": "A young Taiwan leopard cat standing upright and carefully carving a wooden pentacle at a workbench in the forest. Seven other finished pentacles are lined up on the wall. It looks focused and dedicated to its craft. Mastery of skill.",
        "narrative": "The Eight of Pentacles is 'The Skilled Hunter'—the dedication of a young cat practicing its hunting techniques until they become second nature.",
        "mapping_note": "Eight of Pentacles represents 'Ontogenetic Development'—the learning process by which juveniles acquire the skills needed for independent survival.",
        "zh_meaning": "勤奮、學徒期、技能提升、以及對生存技術的不斷磨練。",
        "en_meaning": "Diligence, apprenticeship, skill development, and the constant refinement of survival techniques."
    },
    "09": {
        "title_zh": "錢幣九",
        "title_en": "NINE OF PENTACLES",
        "subtitle": "Luxury & Self-Sufficiency",
        "image_prompt": "A beautiful female Taiwan leopard cat standing upright in a magnificent, predator-free garden forest filled with ripe fruit and butterflies. She wears a rich silk robe and has a bird (prey) perched calmly on her gloved hand. Sense of peace, independence, and abundance.",
        "narrative": "The Nine of Pentacles is 'The Protected Sanctuary'—a high-quality, secure habitat where an individual can thrive in peace and self-sufficiency.",
        "mapping_note": "Nine of Pentacles represents 'Optimal Habitat Choice'—the ecological success of an individual occupying a top-tier, low-risk territory.",
        "zh_meaning": "自給自足、獨立、優雅、以及在高品質棲地中享受的安全與豐饒。",
        "en_meaning": "Self-sufficiency, independence, luxury, and the security and abundance found in optimal habitats."
    },
    "10": {
        "title_zh": "錢幣十",
        "title_en": "TEN OF PENTACLES",
        "subtitle": "Legacy & Wealth",
        "image_prompt": "A multi-generational scene with several Taiwan leopard cats (old and young) gathered in a large, ancient forest courtyard decorated with ten golden pentacles. They look healthy and secure. Sense of family, heritage, and long-term stability.",
        "narrative": "The Ten of Pentacles is 'The Lasting Legacy'—the vision of a stable, thriving multi-generational population in a large, interconnected landscape.",
        "mapping_note": "Ten of Pentacles represents 'Metapopulation Persistence'—the ultimate conservation goal of a self-sustaining population across generations.",
        "zh_meaning": "財富、傳統、家庭、長久的成功，以及族群代代相傳的繁榮。",
        "en_meaning": "Wealth, tradition, family, long-term success, and the prosperity of a population across generations."
    },
    "11": {
        "title_zh": "錢幣侍者",
        "title_en": "PAGE OF PENTACLES",
        "subtitle": "Exploration / Discovery",
        "image_prompt": "A young Taiwan leopard cat standing upright in a sunlit forest clearing, holding a single golden pentacle and examining a small frog or beetle with great focus. It looks like a young scholar of nature. Fresh and studious energy.",
        "narrative": "The Page of Pentacles is 'The Young Naturalist'—the beginning of learning about the environment and identifying the resources needed for life.",
        "mapping_note": "Page of Pentacles represents 'Environmental Learning'—the early stages of a leopard cat's development where it learns to identify prey and safe areas.",
        "zh_meaning": "學習、新機會、踏實、以及對自然界生存法則的初步探索。",
        "en_meaning": "Learning, new opportunity, groundedness, and the initial exploration of survival laws."
    },
    "12": {
        "title_zh": "錢幣騎士",
        "title_en": "KNIGHT OF PENTACLES",
        "subtitle": "Responsibility / Routine",
        "image_prompt": "A Taiwan leopard cat knight standing upright and riding a slow, powerful feline-proportioned horse through a fertile field. He holds a single golden pentacle. The background shows a well-managed farm-forest mosaic. Methodical and reliable energy.",
        "narrative": "The Knight of Pentacles is 'The Steady Patrol'—the patient and methodical monitoring of a territory to ensure its resources remain secure.",
        "mapping_note": "Knight of Pentacles represents 'Resource Monitoring'—the routine patrolling behavior used by resident cats to manage their home ranges.",
        "zh_meaning": "勤奮、可靠、保守、循序漸進，以及對生存領域的穩定巡護。",
        "en_meaning": "Diligence, reliability, routine, and the steady patrolling of a survival territory."
    },
    "13": {
        "title_zh": "錢幣皇后",
        "title_en": "QUEEN OF PENTACLES",
        "subtitle": "Nurturing / Practicality",
        "image_prompt": "A regal female Taiwan leopard cat seated upright on a throne decorated with carvings of various forest animals and fruits. She holds a golden pentacle and looks down with nurturing care. Around her is a lush, vibrant forest full of life.",
        "narrative": "The Queen of Pentacles is 'The Nurturer of the Land'—the female whose presence and health are the ultimate indicators of a thriving ecosystem.",
        "mapping_note": "Queen of Pentacles represents 'Habitat Suitability'—the ideal conditions that allow for high reproductive success and population health.",
        "zh_meaning": "養育、務實、慷慨、穩定，以及守護大地的母性力量與繁榮。",
        "en_meaning": "Nurturing, practicality, generosity, stability, and the maternal power that guards the land's prosperity."
    },
    "14": {
        "title_zh": "錢幣國王",
        "title_en": "KING OF PENTACLES",
        "subtitle": "Mastery / Success",
        "image_prompt": "A powerful male Taiwan leopard cat seated upright on a throne decorated with bulls. He holds a large golden pentacle and a scepter. He looks out over a vast, rich valley filled with wildlife and healthy forests. Authoritative and prosperous posture.",
        "narrative": "The King of Pentacles is 'The Master of the Forest'—the ultimate alpha who has secured a prey-rich, stable territory and rules it with wisdom.",
        "mapping_note": "King of Pentacles represents 'Carrying Capacity'—the state of an ecosystem that has reached its peak potential to support a healthy apex population.",
        "zh_meaning": "成功、安全、商業頭腦、紀律，以及對土地資源的最終掌握與富足。",
        "en_meaning": "Success, security, mastery, discipline, and the ultimate abundance of land resources."
    }
}

for num, data in pentacles_data.items():
    card = template.copy()
    card["id"] = f"card-pe-{num}-{'of-'.join(data['title_en'].lower().split())}"
    card["number"] = 400 + int(num)
    card["suit"] = "pentacles"
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
    card["main_image"] = f"art/generated/card-pe-{num}-{card['slug']}.png"
    
    file_name = f"card-pe-{num}-{card['slug']}.json"
    file_path = os.path.join("/home/ubuntu/leopardcat-tarot/generator/cards/", file_name)
    
    with open(file_path, 'w') as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
    print(f"Created {file_name}")
