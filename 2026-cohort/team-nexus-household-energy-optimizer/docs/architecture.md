# Architecture

How the pieces fit together.

---

## System Overview

```mermaid
flowchart TB
    subgraph Data["data/ (source datasets)"]
        CSV["eia_appliances.csv"]
        Profiles["tenant_profiles.json"]
        Regions["regions.json"]
    end

    subgraph Backend["backend/ (Flask API)"]
        DataPy["data.py<br/>loads + reshapes datasets"]
        CalcPy["calculations.py<br/>kWh / cost / carbon / score math"]
        AppPy["app.py<br/>routes"]
    end

    subgraph Frontend["frontend/ (React + TypeScript)"]
        ApiTs["lib/api.ts<br/>fetch client"]
        Layout["Layout.tsx<br/>shared simulator/session state"]
        CalcTs["lib/calculations.ts<br/>kWh / cost / carbon / score math"]
        Pages["pages/<br/>Home, Simulator, ScoreBreakdown, EnergyHogs"]
        Components["components/<br/>UsageSimulator, SavingsChart, EnergyScoreCard, TopHogsCard, ..."]
    end

    User(("Tenant in browser"))

    CSV --> DataPy
    Profiles --> DataPy
    Regions --> DataPy
    DataPy --> AppPy
    CalcPy -.->|"mirrors CalcTs, backs /api/simulate for parity"| AppPy

    AppPy -->|"/api/simulator/appliances<br/>/api/simulator/baseline-profiles<br/>/api/regions (fetched once, on load)"| ApiTs
    ApiTs --> Layout
    Layout --> CalcTs
    CalcTs --> Layout
    Layout --> Pages
    Pages --> Components
    Components -->|"slider input"| Layout

    User -->|"drags sliders"| Components
    Pages -->|"renders score, breakdown, tips"| User
```

---

## How data actually flows

1. **On page load**, the frontend calls three read-only endpoints once (`/api/simulator/appliances`, `/api/simulator/baseline-profiles`, and `/api/regions`) via `lib/api.ts`. These are backed by `backend/data.py`, which loads and reshapes the three files in `data/`.
2. **Every slider drag after that is computed entirely client-side.** `Layout.tsx` holds the current hours-per-appliance state; `frontend/src/lib/calculations.ts` recomputes kWh, cost, carbon, score, and top energy hogs instantly, with no network round-trip. That's what makes the simulator feel live.
3. **`backend/calculations.py` mirrors `calculations.ts` line-for-line**, backing a standalone `/api/simulate` endpoint. The live UI doesn't call it; it exists so a non-JS caller (or the backend itself) can get identical numbers to what the frontend computes, and so the Python and TypeScript math stay provably in sync.
4. **Pages** (`Home`, `Simulator`, `ScoreBreakdown`, `EnergyHogs`) all read from the same shared context `Layout.tsx` provides, rather than each fetching or computing independently.
