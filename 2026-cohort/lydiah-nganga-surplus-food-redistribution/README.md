# Surplus Food Redistribution Network

**Team Catalyst Alliance** — Grow with Google x Mentor Me Collective, BUILD Project, 2026 Cohort

🔗 **[Live Demo](https://baki-app.onrender.com/)** &nbsp;|&nbsp; 🎥 **[Walkthrough Video](#walkthrough-video)** &nbsp;|&nbsp; 📄 **[3-Page Summary & Slides](docs/06-Project%20Summary%20&%20Presentation/)**

> ⚠️ **Note:** the live demo is hosted on Render's free tier. If it's been idle, the first load can take 30–60 seconds to wake up, please wait rather than assuming it's broken.

<img width="1366" height="617" alt="hero" src="https://github.com/user-attachments/assets/a39b5611-8cf0-4e49-b57d-6b8588b766e2" />


## Table of Contents

- [Assigned Problem Statement](#assigned-problem-statement)
- [What This Project Does](#what-this-project-does)
- [Problem Grounding](#problem-grounding)
- [UN SDG Alignment](#un-sdg-alignment)
- [Team](#team)
- [How It Works](#how-it-works)
- [Business Model](#business-model)
- [Data & Privacy](#data--privacy)
- [Data Sources](#data-sources)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
- [Walkthrough Video](#walkthrough-video)
- [Roadmap](#roadmap)
- [Future Ideas](#future-ideas)
- [License](#license)

## Assigned Problem Statement

> Local grocery vendors dump surplus perishable items due to a lack of an automated, hyper-local coordination hub for local pantries.

## What This Project Does

Local grocery vendors, along with restaurants and small hotels, generate surplus perishable food nearing expiry that often goes to waste, while nearby local pantries, NGOs, and community organizations could redistribute it to people in need. The gap isn't food scarcity — it's a coordination gap: no fast, low-friction way for a vendor with surplus today to know which pantry or NGO can collect it before it spoils.

This project is a lightweight web platform that lets a vendor log a surplus food listing, automatically matches it to the nearest suitable pantry, NGO, or collection point based on proximity, urgency (expiry window), and capacity, and sends an automated notification to the matched organization — closing the loop between "food about to be wasted" and "organization that can use it," in minutes instead of hours. Vendors can alternatively list surplus for discounted sale to the community, for surplus better suited to a small recovery than a full donation. Community members can also subscribe to get notified automatically when new discounted listings appear near them.

The platform currently operates in Nairobi, Lagos, and Johannesburg.

<img width="1366" height="613" alt="listing" src="https://github.com/user-attachments/assets/16bd8225-82fd-4639-844c-dde6d047f5b1" />


## Problem Grounding

Food waste is a documented, substantial problem across all three countries represented on our team. According to the UNEP Food Waste Index Report 2024, Kenya has seven household food waste datapoints ranging from 40 to 100 kg per capita per year, with a 2010 JICA study specifically measuring Nairobi at 100 kg per capita per year — the high end of the national range (UNEP, 2024). Nigeria shows the highest household food waste in Sub-Saharan Africa, estimated at 113 kg per capita per year and roughly 24.79 million tonnes nationally, with some methodologies putting the figure as high as 189 kg per capita per year (UNEP, 2024; Pulse Nigeria, 2024). South Africa's national estimate sits at 27 kg per capita per year, though the report notes this masks wide variation, with city-level studies ranging from 8 to 134 kg per capita per year (UNEP, 2024).

Globally, the same report found that of all food wasted in 2022, 60% occurred at the household level, 28% at food service (restaurants, hotels, catering), and 12% at retail (UNEP, 2024). This is directly relevant to our project's focus: while household waste is comparatively well-measured across Kenya, Nigeria, and South Africa, **food service and retail waste — the exact vendor categories our platform targets — remain largely unmeasured at the national level in all three countries.** The report itself identifies this as a global data gap, particularly acute in low- and middle-income countries (UNEP, 2024).

This isn't an assumption, UNEP's own data confirms it directly. In the report's G20 country table, South Africa's entry lists food service and retail as **"No identified data."** Regionally, of the 14 Sub-Saharan African countries with any household food waste data, only 1 has any food-service datapoint, and only 2 have any retail datapoint, covering just 5% and 6% of the region's population respectively, compared to 66% for household data. The report itself concludes there is **"a notable absence of usable estimates for the retail and food service sectors, particularly in middle- and low-income countries."**

This gap is part of our project's rationale, not just a limitation of the data we could find: if restaurants, small hotels, and groceries in our countries are wasting food at anywhere close to the rate suggested by the food-service/retail share of global waste, there is currently no visibility into it, let alone a system for redirecting it to people who need it. Our MVP targets that specific, under-addressed slice of the problem.

**Sources:**
- United Nations Environment Programme (2024). *Food Waste Index Report 2024: Think Eat Save — Tracking Progress to Halve Global Food Waste.* Nairobi. https://www.unep.org/resources/publication/food-waste-index-report-2024
- "10 African countries that waste the most food in 2024," Pulse Nigeria, 2024. https://www.pulse.ng/story/10-african-countries-that-waste-the-most-food-in-2024-2024072702140403976
- "New report shows mounting food waste as many go to bed hungry," The Star (Kenya), 2024. https://www.the-star.co.ke/counties/nairobi/2024-03-29-new-report-shows-mounting-food-waste-as-many-go-to-bed-hungry/

## UN SDG Alignment

**SDG 2: Zero Hunger** — reducing food waste and improving food access through automated redistribution coordination.

## Team

| Name | Role | Grow with Google Resource |
|---|---|---|
| Oke Oluwatoyin | Project Management | Project Management, Grow with Google Track |
| Zoliswa Mokopu | Cybersecurity | Cybersecurity, Grow with Google Track |
| Omoruyi Igbinovia | Data Analytics | Data Analytics, Grow with Google Track |
| Lydiah Nganga | IT Automation with Python | IT Automation with Python, Grow with Google Track |
| Esther Vincent | Digital Marketing | Digital Marketing, Grow with Google Track |

## How It Works

1. A vendor submits a surplus food listing (item, quantity, expiry window, pickup location, country) through a web form, choosing either "Donate to a Pantry or NGO" or "Sell to the community."
2. **Donate path:** the matching engine scores nearby pantries/NGOs in the same country by proximity, urgency, and declared capacity, and selects the best match. The matched organization receives an automated notification with pickup details. The listing also stays visible on the public live board, in case the automated match doesn't get collected in time.
3. **Sell path:** the listing posts directly to the public live board at a vendor-set discounted price, and any community subscriber in that location gets an automated alert.
4. Every listing is logged, powering the live impact numbers on the homepage — kg redistributed, kg sold, and match success rate.

<img width="1366" height="613" alt="ngo match" src="https://github.com/user-attachments/assets/cb56171c-e6ee-4fb8-a53d-95471718817f" />


## Business Model

Donations stay free, permanently, that's core to the mission and non-negotiable. Revenue comes from a small transaction fee (5–10%) on the "sell to community" path, where money is already changing hands between vendor and buyer, so monetization never touches the social-impact side of the platform.

Longer-term, two additional levers: a paid tier for high-volume vendors (bulk listing, recurring automated posts, waste analytics dashboards), and grant/CSR partnerships, given the direct SDG 2 alignment, food redistribution organizations commonly access non-dilutive funding alongside product revenue rather than relying on one or the other.

<img width="1366" height="601" alt="live impact" src="https://github.com/user-attachments/assets/bf30743c-b332-4ed5-95cf-26f89530b2fa" />


## Data & Privacy

Baki collects personal contact information from two groups:

- **Vendors** (name, phone number): shown **publicly** on the live board, since pantries, NGOs, and neighbors need it to arrange pickup. Vendors are told this explicitly at the point of submission.
- **Community subscribers** (name, phone number, location): used only to trigger a pickup-window alert when a matching listing is posted nearby. Never displayed publicly.

Runtime data files (`public_board.json`, `subscribers.json`, `notifications.log`) are excluded from version control via `.gitignore`, since they accumulate real contact details during testing and demos, and should never end up in a public repository.

All three countries we operate in have active, enforced data protection legislation: Kenya's Data Protection Act (2019), enforced by the Office of the Data Protection Commissioner; Nigeria's Data Protection Act (NDPA), enforced by the Nigeria Data Protection Commission; and South Africa's Protection of Personal Information Act (POPIA), enforced by the Information Regulator. A production version of Baki would need a documented lawful basis for processing, a data retention/deletion policy, and likely registration with the relevant regulator in each country before operating at scale.

## Data Sources

**Grounding (problem statement, research log, README):**
- UNEP Food Waste Index Report 2024 — household food waste figures for Kenya, Nigeria, and South Africa, plus global sector-level waste distribution.
- FAO Food Loss and Waste Database — country-level agricultural loss statistics for additional context.

**Prototype logic (commodity urgency weighting in the matching engine):**
- A cleaned operational grocery inventory dataset (see `docs/01-Research`), used to derive a relative risk ranking across food categories (surplus volume x inventory turnover speed).

### Limitations

No publicly available retail or grocery-level food waste dataset currently exists for Kenya, Nigeria, or South Africa — this is a documented gap in the UNEP Food Waste Index Report itself, not a gap in our research. The dataset used to inform the matching engine's commodity weighting is a general operational inventory dataset, not African-specific data, and is used only as a modeling reference for relative category risk (e.g. fruits and vegetables spoil faster than grains), not as evidence about African markets. All claims about food waste in our specific countries are sourced only from the UNEP and FAO reports above.

The pantries and NGOs in `data/ngos.json` are hand-built seed organizations for this prototype, not yet real registered partners — the result page states this explicitly after every donation match.

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Data:** JSON files (`ngos.json`, `locations.json`, `commodity_weights.json` as seed/reference data; `public_board.json`, `subscribers.json` as live runtime data)
- **Notifications:** currently logged to `data/notifications.log` for demo purposes (no external API keys required to run); structured so a real SMS/WhatsApp provider (e.g. Twilio) can be swapped in later with changes confined to `notify.py`
- **Containerization:** Docker, with a working `Dockerfile` and `docker-compose.yml`
- **Deployment:** live on Render at [baki-app.onrender.com](https://baki-app.onrender.com/)

## Project Structure

```
lydiah-nganga-surplus-food-redistribution/
├── README.md
├── LICENSE
├── src/
│   ├── app.py
│   ├── matching_engine.py
│   ├── notify.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .dockerignore
│   ├── .gitignore
│   ├── templates/
│   │   ├── index.html
│   │   ├── browse.html
│   │   └── result.html
│   ├── static/
│   │   ├── style.css
│   │   └── images/
│   │       └── hero-photo.jpg
│   └── data/
│       ├── ngos.json
│       ├── locations.json
│       ├── commodity_weights.json
│       ├── public_board.json       (gitignored, runtime data)
│       └── subscribers.json        (gitignored, runtime data)
└── docs/
    ├── 01-Research/
    │   ├── Data Analysis Report.pdf
    │   └── Research Report.pdf
    ├── 02-Project Management/
    │   ├── Project Charter.pdf
    │   ├── Project Management Plan.pdf
    │   ├── Project Timeline.pdf
    │   ├── RACI Chart.pdf
    │   ├── Risk Register.pdf
    │   └── Project Communication Plan.pdf
    ├── 03-Technical/
    │   ├── Security Testing & Analysis/
    │   ├── THREAT_MODEL.md
    │   ├── RISK_REGISTER.md
    │   └── SECURITY_TEST_PLAN.md
    ├── 04-Meetings/
    │   └── (kickoff + progress review notes)
    ├── 05-Evidence/
    │   └── Data Analysis - Charts.pdf
    └── 06-Project Summary & Presentation/
        ├── 3-page Project Summary.pdf
        ├── Zero Hunger 2026 Presentation Slide.pdf
        └── screenshots/
            ├── hero.png
            ├── live-board.png
            ├── match-result.png
            └── live-impact.png
```

## How to Run

**Option A — plain Python:**
```bash
cd 2026-cohort/lydiah-nganga-surplus-food-redistribution/src
pip install -r requirements.txt
python app.py
```

**Option B — Docker:**
```bash
cd 2026-cohort/lydiah-nganga-surplus-food-redistribution/src
docker compose up --build
```

Either way, open `http://localhost:5000` in your browser.

**Option C — no setup at all:** just use the [live demo](https://baki-app.onrender.com/).

## Walkthrough Video

[Watch the walkthrough video](https://drive.google.com/file/d/1weE2-9P3X4bNK6_-cUKUpD6IATJuH58y/view?usp=sharing)

## Roadmap

This web MVP proves the matching engine and dual-path model work end to end. The next step beyond this submission is a native mobile app (iOS/Android), which would let vendors and pantries/NGOs get push notifications directly, work better on unreliable mobile data, and support offline listing drafts, all things a browser-based form handles poorly for our target users.

## Future Ideas

- Expand matching to individual consumers, not just NGOs (already partially supported: unclaimed donations are visible to anyone on the live board)
- Real-time geolocation instead of dropdown location selection
- SMS-first / WhatsApp bot interface for lower-bandwidth accessibility, for vendors without reliable smartphone/data access
- Natural-language listing intake: a vendor sends a free-text message (e.g. "20kg tomatoes, ready now, Kibera") and it's automatically parsed into a structured listing. [Hashbrown](https://hashbrown.dev) is a strong technical fit for this specifically, since it's built to turn natural language into strongly-typed structured data inside a web frontend. This would require migrating the frontend to React or Angular (Hashbrown's supported frameworks), so it's scoped as a v2 direction, not part of this MVP.
- Partner integrations with real pantries, NGOs, and vendors post-MVP
- A volunteer courier role for pickups: some pantries/NGOs lack their own transport, so a lightweight "volunteer collects surplus and delivers it, keeping a small share as thanks" model (similar in spirit to Olio's volunteer network) could close that logistics gap. Not built in this MVP; would need its own signup flow and a way to notify nearby volunteers alongside pantries/NGOs.
- Vendor accounts, so returning vendors don't have to re-enter their details on every listing.

## License

MIT — see [LICENSE](./LICENSE)
