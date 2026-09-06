import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import install_error_handlers
from app.routers import (
    account,
    applications,
    auth,
    insight,
    invites,
    matching,
    monitoring,
    participant,
    public,
    roster,
    setup,
    strands,
    unmatched,
)

settings = get_settings()

# Uvicorn configures its own loggers and leaves the root without a handler, so
# anything the application logs is dropped by default. That is not cosmetic
# here: with no mail provider configured, the sign-in link is written to the log
# and nothing else, so losing INFO means nobody can sign in at all.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(name)s  %(message)s",
)
logging.getLogger("braid").setLevel(logging.INFO)

app = FastAPI(
    title="Braid API",
    version="0.1.0",
    description=(
        "Implements ../openapi.yaml. That contract is the specification: the "
        "frontend already consumes every operation in it through generated "
        "types, so this service implements something that exists rather than "
        "something negotiated afterwards."
    ),
)

# The frontend sends credentials, so the origin must be named exactly —
# browsers reject a wildcard origin on credentialed requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Everything lives under /v1. The contract declares that base
# (servers: http://localhost:8000/v1) and the frontend's client is built from
# it, so the prefix is part of the interface rather than a preference.
V1 = "/v1"

# Errors leave in the contract's Problem shape, not FastAPI's {"detail": ...}.
# The frontend reads error.message to decide what to show a person, so without
# this every failure in the interface renders as undefined.
install_error_handlers(app)

for router in (
    auth,
    public,
    roster,
    strands,
    participant,
    matching,
    unmatched,
    applications,
    setup,
    monitoring,
    insight,
    account,
    invites,
):
    app.include_router(router.router, prefix=V1)

# Broadcast lives in the monitoring module but is its own contract tag.
app.include_router(monitoring.comms, prefix=V1)


@app.get("/health", tags=["Meta"])
def health() -> dict[str, str]:
    """Liveness for the platform's health check. Outside /v1 deliberately: it is
    infrastructure, not part of the product's API."""
    return {"status": "ok"}


@app.get(f"{V1}/health", tags=["Meta"])
def health_v1() -> dict[str, str]:
    """The same check inside the versioned base, for anything that only knows
    the API root."""
    return {"status": "ok"}
