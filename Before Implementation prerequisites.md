# Before Implementation Prerequisites

Everything you need installed and configured on a fresh machine before starting implementation of the RPG-Gamified Life Tracker.

## 1. System Requirements

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| OS | Windows 10+, macOS 12+, or Linux (Ubuntu 20.04+) | GitHub Actions runs on Ubuntu |
| Python | 3.10+ | Required by all tools. Check: `python --version` |
| pip | Latest | Comes with Python. Update: `python -m pip install --upgrade pip` |
| Git | 2.30+ | For version control + GitHub Actions. Check: `git --version` |
| Node.js | Not required | Project is Python-only |

## 2. Python Packages (requirements.txt)

Install all at once: `pip install -r requirements.txt`

| Package | Version | Phase Needed | Purpose |
|---------|---------|-------------|---------|
| `notion-client` | >=2.0.0 | Phase 1 | Notion API SDK — all database operations |
| `python-dotenv` | >=1.0.0 | Phase 1 | Load .env file for API keys and config |
| `pytest` | >=7.0.0 | Phase 1 (tests) | Test runner for all unit tests |
| `Pillow` | >=10.0.0 | Phase 5 | Avatar frame compositing (rank frames + profile picture) |
| `matplotlib` | >=3.7.0 | Phase 5 | Radar chart generation (5-stat spider chart) |
| `numpy` | >=1.24.0 | Phase 5 | Math support for matplotlib radar chart angles |
| `cloudinary` | >=1.36.0 | Phase 5 | Image upload to Cloudinary (avatar + radar chart hosting) |
| `openai` | >=1.0.0 | Phase 6 | OpenAI API for AI coaching briefings + quest generation |

### Optional Development Packages

| Package | Purpose |
|---------|---------|
| `pytest-cov` | Test coverage reports (not required, nice to have) |
| `black` | Code formatting (optional) |
| `flake8` | Linting (optional) |

## 3. External Accounts & API Keys

### Required (Phase 1 — must have before starting)

| Service | What You Need | How to Get It | Cost |
|---------|--------------|---------------|------|
| **Notion** | Integration token + workspace | 1. Go to notion.so/my-integrations 2. Create new integration 3. Copy "Internal Integration Token" 4. Share your workspace pages with the integration | Free (Personal plan) |
| **GitHub** | Repository + Actions enabled | 1. Create repo on github.com 2. Actions is enabled by default on public repos 3. For private repos, check Settings > Actions > General | Free (public repos) or Free tier (private) |

### Required (Phase 5 — needed for avatar/chart image hosting)

| Service | What You Need | How to Get It | Cost |
|---------|--------------|---------------|------|
| **Cloudinary** | Cloud name, API key, API secret | 1. Sign up at cloudinary.com 2. Go to Dashboard 3. Copy Cloud Name, API Key, API Secret | Free tier (25 credits/month — sufficient for single player) |

### Required (Phase 6 — needed for AI coaching)

| Service | What You Need | How to Get It | Cost |
|---------|--------------|---------------|------|
| **OpenAI** | API key | 1. Sign up at platform.openai.com 2. Go to API Keys 3. Create new key | Pay-as-you-go. Budget: ~$1/month with gpt-4o-mini. Capped in config. |

## 4. Environment Variables (.env file)

Create a `.env` file in the project root with these variables. Fill in values as you progress through phases.

```bash
# === Phase 1: Foundation ===
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PARENT_PAGE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Database IDs (populated after running create_databases.py)
CHARACTER_DB_ID=
ACTIVITY_LOG_DB_ID=
GOOD_HABIT_DB_ID=
BAD_HABIT_DB_ID=
SKILL_DB_ID=
STREAK_TRACKER_DB_ID=
GOAL_DB_ID=
BRAIN_DUMP_DB_ID=
DIFFICULTY_DB_ID=
MARKET_DB_ID=
CART_DB_ID=
HOTEL_DB_ID=
BLACK_MARKET_DB_ID=
OVERDRAFT_DB_ID=
LEVEL_SETTING_DB_ID=
SETTINGS_DB_ID=
QUEST_DB_ID=
JOURNAL_DB_ID=
MOOD_DB_ID=
ONBOARDING_IDENTITY_DB_ID=
VISION_BOARD_DB_ID=
BUDGET_CATEGORY_DB_ID=
EXPENSE_LOG_DB_ID=
TREASURY_DB_ID=
EXERCISE_DICT_DB_ID=
WORKOUT_SESSION_DB_ID=
SET_LOG_DB_ID=
MEAL_LOG_DB_ID=
INGREDIENTS_DB_ID=
LOOT_BOX_INVENTORY_DB_ID=
ACHIEVEMENTS_DB_ID=
PLAYER_ACHIEVEMENTS_DB_ID=
DAILY_SNAPSHOTS_DB_ID=

# === Phase 5: Reward Systems ===
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# === Phase 6: AI Coach ===
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# === Phase 8: Dashboard & Onboarding ===
# (These are subset of above — used by onboarding.py and dashboard_setup.py)
# CHARACTER_DB_ID, GOOD_HABIT_DB_ID, BAD_HABIT_DB_ID, VISION_BOARD_DB_ID,
# ONBOARDING_IDENTITY_DB_ID, JOURNAL_DB_ID, BRAIN_DUMP_DB_ID, QUESTS_DB_ID,
# DAILY_SNAPSHOTS_DB_ID — already listed above
```

## 5. Directory Structure (Create Before Phase 1)

```bash
# These directories should exist in the project root:
mkdir -p tools tests assets/frames assets/icons assets/backgrounds assets/charts \
         workflows .github/workflows checklists .tmp
```

| Directory | Purpose |
|-----------|---------|
| `tools/` | All Python engine scripts |
| `tests/` | All pytest test files |
| `assets/frames/` | Rank frame PNG images (7 files: peasant.png through mythic.png) |
| `assets/icons/` | Achievement badge icons (43 files) |
| `assets/backgrounds/` | Optional Notion page cover images |
| `assets/charts/` | Generated radar chart PNGs (output directory) |
| `workflows/` | SOP markdown files |
| `.github/workflows/` | GitHub Actions YAML files |
| `checklists/` | Manual verification checklists |
| `.tmp/` | Temporary processing files (gitignored) |

## 6. Git Configuration

```bash
# Initialize repo (if not done)
git init

# Create .gitignore with these entries:
.env
.tmp/
credentials.json
token.json
__pycache__/
*.pyc
.pytest_cache/
assets/charts/*.png    # Generated files — regenerated on demand
.claude/
```

## 7. GitHub Actions Secrets (Phase 7)

When you set up CI/CD, add these secrets to your GitHub repo (Settings > Secrets and variables > Actions):

| Secret Name | Value | Used By |
|-------------|-------|---------|
| `NOTION_API_KEY` | Your Notion integration token | daily.yml, weekly.yml, monthly.yml |
| `NOTION_PARENT_PAGE_ID` | Your Notion parent page ID | All workflows |
| `OPENAI_API_KEY` | Your OpenAI API key | weekly.yml (AI coaching) |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | daily.yml (chart upload) |
| `CLOUDINARY_API_KEY` | Cloudinary API key | daily.yml |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | daily.yml |
| All `*_DB_ID` variables | Each database ID | All workflows |

## 8. Notion Workspace Setup

Before running `create_databases.py`:

1. Create a new Notion page that will be the **parent page** for all game databases
2. Share that page with your Notion integration (click Share > Invite > select your integration)
3. Copy the page ID from the URL: `notion.so/<workspace>/<PAGE_ID>?v=...`
4. Set `NOTION_PARENT_PAGE_ID` in `.env`

## 9. Pre-Flight Verification

After setup, verify everything works:

```bash
# 1. Check Python version
python --version  # Should be 3.10+

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify .env loads
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('NOTION_API_KEY set:', bool(os.getenv('NOTION_API_KEY')))"

# 4. Verify Notion connection
python tools/smoke_test.py  # (available after Phase 1, Task 1.3)

# 5. Run tests (available after Phase 9)
python -m pytest tests/ -v
```

## 10. Phase-by-Phase Readiness Checklist

| Phase | Prerequisites to Start |
|-------|----------------------|
| Phase 1: Foundation | Python 3.10+, pip, notion-client, python-dotenv, Notion account + integration token |
| Phase 2: HP/Death/Economy | Phase 1 complete, all DB IDs in .env |
| Phase 3: XP/Streaks/Leveling | Phase 1 complete |
| Phase 4: Domain Modules | Phases 1-3 complete |
| Phase 5: Reward Systems | Phases 1-4 complete, Pillow, matplotlib, numpy, cloudinary, Cloudinary account, rank frame PNGs in assets/frames/ |
| Phase 6: AI Coach & Quests | Phases 1-4 complete, openai package, OpenAI API key |
| Phase 7: Automation | Phases 1-6 complete, GitHub repo with Actions enabled, GitHub Secrets configured |
| Phase 8: Dashboard & Onboarding | Phases 1-7 complete |
| Phase 9: E2E Verification | Phases 1-8 complete, pytest |

## Summary: What to Do First

1. Install Python 3.10+
2. Clone/create the repo
3. `pip install -r requirements.txt`
4. Create Notion integration and get token
5. Create `.env` with `NOTION_API_KEY` and `NOTION_PARENT_PAGE_ID`
6. Create directory structure
7. Place rank frame PNGs in `assets/frames/` (needed by Phase 5)
8. Sign up for Cloudinary (needed by Phase 5)
9. Get OpenAI API key (needed by Phase 6)
10. Start Phase 1
