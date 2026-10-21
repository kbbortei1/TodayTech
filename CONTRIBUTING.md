# Contributing to TodayTech

Thank you for your interest in contributing to **TodayTech**! TodayTech is an open-source, self-hosted opportunity radar designed to help students and early-career builders discover, rank, and apply for high-impact opportunities globally and locally.

---

## 0. Non-Negotiable Rules

1. **NO PERSONAL DATA ANYWHERE IN THE REPO**
   - Never commit your real name, school, email, student ID, resume contents, specific teammates, or API keys.
   - All personal details must remain strictly in `.env`, `profile.yaml`, or `data/` (all of which are `.gitignore`d).
   - Use mock names (e.g. `Test User`, `Student A`, `University of Example`) in tests and examples.
2. **NO HARDCODED SECRETS**
   - All credentials (Telegram tokens, LLM API keys, Reddit credentials) must be loaded via `todaytech.core.config.Settings` from environment variables.
   - Pre-commit runs `detect-secrets` on every staged commit.
3. **RESPECT SOURCE WEBSITES & ROBOTS.TXT**
   - All web scrapers and feed collectors must respect `robots.txt`, set honest `User-Agent` headers, and adhere to reasonable rate limits.

---

## 🛠️ Development Setup

TodayTech requires **Python 3.12+**.

### 1. Clone the repository
```bash
git clone https://github.com/your-username/TodayTech.git
cd TodayTech
```

### 2. Set up virtual environment
```bash
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
```

### 3. Install in editable mode with development dependencies
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### 4. Install pre-commit hooks
```bash
pre-commit install
```

---

## 🧪 Running Quality Checks & Tests

Before submitting any code changes, verify all linters and tests pass:

```bash
# Format & Lint
ruff check .
ruff format --check .

# Type check
mypy todaytech

# Run unit tests
pytest --cov=todaytech
```

---

## 📦 Adding a New Source Pack

Community-contributed source packs allow users in specific countries, regions, or disciplines to plug in curated opportunity channels.

1. Create a new YAML file under `sources/packs/<name>.yaml` (for example: `sources/packs/nigeria.yaml` or `sources/packs/datascience.yaml`).
2. Follow the standard source pack structure:
```yaml
name: "Nigeria Tech Opportunities 🇳🇬"
description: "Curated tech scholarships, internships, and hackathons in Nigeria"
version: "1.0.0"

sources:
  - name: "Example RSS Feed"
    type: "rss"
    url: "https://example.com/feed"
    refresh_interval_hours: 6
    tags: ["scholarship", "nigeria"]

  - name: "Example Platform"
    type: "platform"
    platform: "devpost"
    tags: ["hackathon"]
```
3. Ensure all URLs resolve, contain real opportunity content, and do not violate the terms of service of the target hosts.

---

## 🔌 Adding a Collector

If you'd like to integrate a new platform or data source:
1. Create a module under `todaytech/collectors/<collector_name>.py`.
2. Implement your collector as an async function or class returning a list of `Opportunity` domain models (`todaytech.core.models.Opportunity`).
3. Ensure every item has a deterministically generated `external_id` via `generate_external_id(item)`.
4. Wrap all external network requests with timeout and error handling.
5. Add unit tests for your collector under `tests/`.

---

## 🤝 Submitting a Pull Request

1. Fork the repository and create a descriptive branch:
   ```bash
   git checkout -b feat/add-kenya-source-pack
   ```
2. Make your changes and commit with concise, conventional commit messages:
   ```bash
   git commit -m "feat(sources): add Kenya community source pack"
   ```
3. Push to your fork and open a Pull Request against the `main` branch.
4. Ensure CI tests and lint checks pass.

Thank you for helping empower students and early-career developers worldwide!
