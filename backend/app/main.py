from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, contracts, form_templates, organizations, rdas, teams, users
from app.core.config import settings

app = FastAPI(title="RDA de Campo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(contracts.router)
app.include_router(teams.router)
app.include_router(users.router)
app.include_router(form_templates.router)
app.include_router(form_templates.version_router)
app.include_router(rdas.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
