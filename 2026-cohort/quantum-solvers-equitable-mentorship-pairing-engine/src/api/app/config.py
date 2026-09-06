from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Everything the service needs from its environment.

    Deliberately no defaults for `database_url`: a service that silently falls
    back to a local database is a service that looks healthy in production while
    writing nowhere useful.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    # Where the frontend is served from. CORS must name it exactly, because the
    # frontend sends credentials and a wildcard origin is rejected by browsers
    # when it does.
    web_origin: str = "http://localhost:3000"

    environment: str = "development"

    # The contract fixes this name: openapi.yaml declares the security scheme as
    # an apiKey in a cookie called braid_session.
    session_cookie_name: str = "braid_session"
    session_ttl_days: int = 30

    # Locally the frontend and the API differ only by port, which is the same
    # site, so Lax works. Deployed on separate hosts they are cross-site, and a
    # Lax cookie is silently dropped on every API call — an auth bug that
    # appears only in production. Set to "none" there; browsers then require
    # Secure, which `cookie_secure` provides.
    session_cookie_samesite: str = "lax"

    # Short by design. A sign-in link that lives for hours is a credential
    # sitting in an inbox.
    magic_link_ttl_minutes: int = 15

    # Opens POST /auth/demo, which signs in as a seeded account so a reviewer
    # can get inside a deployed copy. Off unless set: the seeded people have
    # addresses nobody can receive mail at, which is the only reason this
    # exists, and it must never be a way into a real cohort's data.
    demo_mode: bool = False

    # Absent by default, and that absence is a working mode rather than a
    # misconfiguration: with no key `mail.send` logs the message, so a local
    # sign-in works with no provider account anywhere. Set it wherever somebody
    # other than you needs to receive a link.
    resend_api_key: str | None = None

    # Must be an address at a domain verified with the provider. Resend's shared
    # sandbox sender only delivers to the address that owns the account, which
    # looks like working email right up to the moment somebody else signs up.
    mail_from: str = "Braid <onboarding@resend.dev>"

    @property
    def mail_configured(self) -> bool:
        return bool(self.resend_api_key)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cookie_secure(self) -> bool:
        """Off locally, because http://localhost cannot set a Secure cookie.
        Forced on whenever SameSite=None, which browsers reject without it."""
        return self.is_production or self.session_cookie_samesite == "none"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
