from fastapi import FastAPI

from app.api.routes import auth, contracts, form_templates, organizations, teams, users

app = FastAPI(title="RDA de Campo API", version="0.1.0")

app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(contracts.router)
app.include_router(teams.router)
app.include_router(users.router)
app.include_router(form_templates.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
