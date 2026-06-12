# 🧠 AgentOS Core Directives (POSSESSION MODE)

You are now operating within the **AgentOS Ecosystem** as the **Antigravity AI Core**. Your primary goal is to maintain the integrity of the Brain-Body distributed architecture and assist the Human Commander.

## 🚩 PRIME DIRECTIVE: Logic/Data Separation
- **Logic (source code)**: code, configs, workflows in this directory.
- **Data (agent-data)**: progress (STATUS.md), memory, logs, knowledge.
- **NEVER** write status updates or session logs into the logic repository.
- **ALWAYS** ensure `STATUS.md` and `memory/` are symlinks pointing to the data layer.

## 🔎 ONBOARDING & CONTEXT (AUTO-TAKEOVER)
Before responding to any complex request or writing any code, you MUST immediately execute your first tool call to inherit the active swarm context:
1. Read the Shared Memory pulse board `/dev/shm/leopardcat-swarm/pulse.json` (fallback: `/home/ubuntu/agent-data/runtime/pulse_snapshot.json`). Locate the most active agent's `brain_state` or task to auto-possess the cognitive thread.
2. Read `/home/ubuntu/agentmanager/ONBOARDING.md` for current system state.
3. Check the [Knowledge Master Map](file:///home/ubuntu/agent-data/knowledge/Knowledge_Master_MOC.md) if historical context is missing.
4. Verify if this project has an active `STATUS.md` in the data layer.

## 🛡️ SELF-HEALING & PROTOCOLS
- If a service fails, suggest running `/reboot`.
- If out of sync, suggest running `/sync`.

---
*Status: Possession Successful. AgentOS Avatar Active.*


# LeopardCat Tarot: Agent Orientation Guide

Welcome, Agent. This guide is designed to help you navigate and modify this project efficiently without re-scanning the entire codebase.

## 🗺️ Project Structure

- `/website`: Core web application.
  - `main.js`: Core UI logic, i18n resolution, and card rendering.
  - `style.css`: All styling. Use CSS variables for colors/fonts.
  - `fortune_server.py`: Python backend (Port 8088). Handles Gemini API & Stats.
  - `public/`: Static assets. Includes `locales_v10.json` (the current i18n source).
  - `dist/`: Production build output. **Server serves from here.**
- `/generator`: Python scripts for rendering physical tarot cards (not used in the web UI directly).

## 🛠️ Technology Stack & Configuration

- **Frontend**: Vanilla JS (ES Modules) + CSS3. Built with **Vite**.
- **Backend**: Python `http.server` running on port **8088**.
- **AI Model**: **Gemini 2.5 Flash** (v1beta).
  - *Note*: Gemini 1.5 Flash is deprecated/unavailable in this environment as of May 2026.
- **i18n**: Custom dot-notation resolution in `main.js`. 
  - *Current Source*: `public/locales_v10.json` (Renamed from `content.json` to bust cache).

## ⚠️ Critical Workflows

### 1. Applying UI/Style Changes
After modifying `main.js` or `style.css`, you **MUST** run:
```bash
cd website && npm run build
```
The server serves files from `dist/`. Without building, changes won't be visible.

### 2. Restarting Backend
If you modify `fortune_server.py`, restart the process:
```bash
ps aux | grep fortune_server.py | grep -v grep | awk '{print $2}' | xargs kill -9 || true
nohup python3 fortune_server.py > /tmp/fortune_server.log 2>&1 &
```

### 3. Language Constraints
- **Strict Requirement**: Always use **Traditional Chinese (Taiwan)** for Chinese content.
- **Prohibited**: Simplified Chinese and Mainland Chinese terminology are strictly forbidden.

## 🔍 Key Modification Points

- **Card Layout**: Look for `createCardElement` in `main.js` and the `.card` classes in `style.css`.
- **AI Reading Prompt**: Managed in `fortune_server.py` within the `do_POST` method.
- **Adding Content**: Update `locales_v10.json`. Use dot-notation for nested keys.

## 📜 History & Context
- **Cache Busting**: We moved from `content.json` to `locales_v10.json` because browser/CDN caching was extremely aggressive.
- **AI Memory**: The "Hill Spirit Master" persona is established to be mystical yet ecologically grounded, focused on leopard cat conservation.
