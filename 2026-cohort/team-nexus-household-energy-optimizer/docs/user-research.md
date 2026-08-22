# User Research

Lightweight research to sanity-check the app's input flow, score design, and messaging before launch. Not formal, just enough signal from real people to back up the UX decisions in the demo narrative.

---

## Methodology

- **Who**: People who currently rent and pay their own utility bills
- **How**: 15-minute informal interviews (in person, call, or async over text)
- **When**: July 25 - July 28, 2026
- **Conducted by**: Sehr Abrar

### Interview Questions

1. Do you know roughly how much energy your appliances use, or what's driving your bill?
2. Have you ever tried to reduce your energy usage? What stopped you, or what worked?
3. If an app gave you a "score" for your energy habits, what would make you trust it vs. ignore it?
4. Walk me through how you'd want to input your usage, do you know your appliance hours, or would you rather answer simpler lifestyle questions?

---

## Key Findings

- **Nobody tracks appliance hours.** Across every persona, no one could estimate how many hours a day they run their AC, laundry, or entertainment devices. Manual kWh/hour entry is a non-starter; lifestyle-style questions ("how often do you use your AC?", "do you work from home?") are answerable.
- **Score trust depends on explanation, not just a number.** Budget- and eco-conscious users both said they'd distrust a score unless it's clear how it's calculated and what it's driving toward (savings for one, environmental impact for the other).
- **Motivation splits into two currencies: money and impact.** Some users only care about the bill going down; others want to see the environmental payoff of the same behavior. The score/tips need to speak to both without requiring the user to pick a "mode."
- **Effort tolerance is low.** Busy professionals and students in particular will abandon anything that feels like data entry. Convenience beats precision for this audience.
- **Shared/family living complicates attribution.** Students and parents both raised the same issue from different angles: usage isn't just "mine," it's split across roommates or driven by household size, so the tool needs to work off personal habits/household context rather than assuming one person controls all usage.

---

## Personas

### Persona 1: Budget-Conscious Renter

- **Goals**: Keep monthly costs predictable; get money-saving advice without major lifestyle changes
- **Frustrations**: Knows the bill went up but not which appliance is responsible; unsure if habits like turning off lights actually move the needle
- **Preferred input**: Lifestyle questions ("how often do you use your AC?") over estimating appliance hours
- **Trusts the score if**: it explains how it's calculated and ties directly to potential $ savings

### Persona 2: Eco-Conscious Renter

- **Goals**: Reduce carbon footprint, not just cost; wants to know habits are making a real impact
- **Frustrations**: Already does the "right" things (unplugging devices, efficient lighting) but gets no feedback on whether it matters
- **Preferred input**: Willing to give more detail, but still wants it quick and non-technical
- **Trusts the score if**: it explains the environmental benefit of improving it and shows trends over time

### Persona 3: Busy Professional

- **Goals**: Manage energy with minimal time/effort; convenience over control
- **Frustrations**: Rarely thinks about where energy goes; won't do manual data entry
- **Preferred input**: Quick lifestyle questions ("do you work from home?", "how often is the AC on?")
- **Trusts the score if**: it's presented clearly, updates automatically, and pairs with low-effort recommendations

### Persona 4: Student in Shared Accommodation

- **Goals**: Understand their own footprint despite not controlling the whole household's usage
- **Frustrations**: Bill is split among roommates; knows big drivers exist (AC, gaming PCs, showers) but can't isolate their own share
- **Preferred input**: Simplified questionnaire over detailed appliance tracking, since they don't know who uses what
- **Trusts the score if**: it reflects personal habits rather than trying to estimate the whole household

### Persona 5: Family-Oriented User

- **Goals**: Balance comfort, convenience, and cost across the whole household
- **Frustrations**: Knows heating/cooling, laundry, and kitchen use drives the bill, but family needs make routines hard to change
- **Preferred input**: Household-level questions (household size, laundry frequency, AC usage, cooking habits) over manual appliance hours
- **Trusts the score if**: it gives actionable recommendations that fit into daily family life and tracks progress over time

---

## How Findings Shaped the App

| Finding | Design Decision |
|---------|------------------|
| Nobody tracks appliance hours; lifestyle questions are answerable, manual hours aren't | Usage Simulator uses sliders (HVAC, fridge, laundry, entertainment) instead of manual kWh/hour entry |
| Score trust depends on explanation, not just a number | Score breakdown shown alongside the Personalized Energy Score, not just the number alone |
| Motivation splits between cost-savers and impact-driven users | Tips reference both cost and environmental framing rather than picking one |
| Effort tolerance is low, especially for busy/student personas | Top 3 "energy hog" detection surfaces the highest-impact fixes instead of requiring users to review every category |
| Shared/family living complicates attribution | Baseline profiles and regional comparison are framed around personal habits, not assumed full-household control |
