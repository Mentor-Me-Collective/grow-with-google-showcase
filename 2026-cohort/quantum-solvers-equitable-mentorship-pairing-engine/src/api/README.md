# api

The FastAPI service. Not built yet — this folder exists so the deployment shape
is visible from the start.

## What it has to implement

`../openapi.yaml`, which is not a sketch: the frontend already consumes all 48
endpoints and 144 schemas through generated types, and every screen has been
driven against them. The contract is the specification, so this service
implements something that already exists rather than something negotiated
afterwards.

## Planned shape

```
api/
├── pyproject.toml
├── Dockerfile
├── alembic/                  migrations
└── app/
    ├── main.py               FastAPI app, CORS, session middleware
    ├── db.py                 engine, session
    ├── models/               SQLAlchemy — organisation, program, account,
    │                         participation, strand, application, run
    ├── schemas/              Pydantic, validated against openapi.yaml
    ├── routers/              one per contract tag
    └── matching/
        ├── eligibility.py    stage 1 — hard constraints
        ├── fit.py            stage 2 — weighted score, similar/complementary
        ├── priority.py       stage 3 — equity weighting into bands
        └── assign.py         stage 4 — global assignment
```

## Notes for whoever writes this

**Role lives on `Participation`, never on `Account`.** The same person is a
mentee in one programme and a mentor in another, simultaneously, with different
answers to different forms. Every participant query is scoped by `program_id`.

**The unknown form schema stops at one boundary.** Form definitions are
versioned JSON blobs; answers are keyed by stable field id and never by question
text. A normalisation step projects only the flagged fields (`matching`,
`equity`, `admin`) into fixed typed tables, and everything downstream —
matching, reporting, export — reads that projection rather than the form. That
projection is a job that can be re-run.

**An application keeps its form version permanently.** Reading an old
application through a newer form would put questions in someone's mouth.

**The solver is the small part.** Expand each mentor into `capacity` slots,
build a cost matrix over eligible pairs, and solve with
`scipy.optimize.linear_sum_assignment` or min-cost flow. At cohort scale
(200 mentees × 25 mentors) it runs in milliseconds. The work is in the objective:
a large constant reward per assignment is what stops an optimiser protecting its
average by abandoning the hardest-to-place mentees.

**Two orderings are ethical decisions, not layout.** `POST
/programs/{id}/criteria/test-run` returns a fairness summary and no pairs, and
the run review shows the summary above the names. Both exist to stop a
coordinator tuning pair by pair. Do not add pairs to the test-run response.

**Runs are stored objects with a lifecycle**, not function calls:
`queued → running → drafted → published | discarded`. The frontend polls
`GET /runs/{runId}` and expects `progress` to advance from 0 to 1 with
`fairnessSummary` null until `drafted`.
