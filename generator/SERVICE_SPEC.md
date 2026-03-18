# 🤖 Antigravity Image Generation Service (LeopardCat Tarot Hook)

## 🎯 目的
解決本地開發環境 Gemini API 額度限制問題。透過 Antigravity Agent 的內建生圖能力，為石虎塔羅牌專案提供高品質、符合塔羅美學的原始圖檔。

---

## 🛠️ 運作流程 (方案 A)

### 1. 發送請求 (Request)
將請求 JSON 放入資料層路徑：
`/home/ubuntu/agent-data/projects/leopardcat-tarot/requests/[card_id].json`

**格式規範：**
```json
{
  "card_id": "card-00-the-fool",
  "base_prompt": "一隻幼年石虎在路邊...",
  "status": "pending",
  "timestamp": "2026-03-17T08:00:00Z"
}
```

### 2. 執行生圖 (Processing)
當負責人對 Antigravity 說：「處理塔羅生圖請求」時，我會執行：
1.  讀取請求 JSON。
2.  **優化 Prompt**：加入「塔羅美學過濾器」（見下文）並確保避開版權。
3.  執行 `generate_image`。
4.  將圖檔儲存至 `/home/ubuntu/leopardcat-tarot/art/generated/[card_id].png`。

### 3. 回饋與同步 (Feedback loop)
我會產出回應 JSON 到：
`/home/ubuntu/agent-data/projects/leopardcat-tarot/responses/[card_id].json`

**重要：** 回應中會包含 **`optimized_prompt`**。石虎塔羅專案的腳本應讀取此欄位，並**自動更新**該張牌的原始定義檔 (`generator/cards/*.json`)，以確保源頭資料與產出一致。

---

## 🎨 雙層提示詞架構 (Dual-Layer Prompt Architecture)

為了實現「一次定義，多點替換」，本服務採用以下拼接邏輯產生最終 Prompt：

### 1. 樣式層 (Style Layer - FIXED)
`[STYLE_BASELINE]`: "Vertical 2:3, single unified scene, 1900s mystical tarot lithography, bold ink outlines. Anthropomorphic Taiwan leopard cat with white ear-spots and forehead stripes."

### 2. 敘事層 (Narrative Layer - VARIABLE)
從各牌 JSON 的 `generation.narrative` 欄位讀取。

### 3. 組署公式 (Assembler Formula)
`MATCHING_PROMPT = STYLE_BASELINE + NARRATIVE_CONTENT + TECHNICAL_CONSTRAINTS`

---

## 🔒 版權守則
- 禁令：嚴禁直接提及 "Rider-Waite", "Thoth", "Wild Unknown" 等商標。
- 替代方案：使用 "1900s mystical print style", "Art Nouveau nature illustration", "Classical esoteric woodcut" 等中性描述。
