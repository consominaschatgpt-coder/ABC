# Backend — Sistema de RDA de Campo

API (FastAPI + PostgreSQL) para o sistema de Relatório Diário de Atividades.
Fase 1 do plano em `../docs/PLANO_DESENVOLVIMENTO.md`: hierarquia de dados
(Organização → Contrato → Equipe → Usuário), autenticação JWT e CRUD básico.

## Rodando localmente com Docker

```bash
cp .env.example .env   # ajuste SECRET_KEY em produção
docker compose up --build
```

A API sobe em `http://localhost:8000`. Docs interativas (Swagger) em
`http://localhost:8000/docs`.

Aplique as migrations (primeira vez ou após alterar models):

```bash
docker compose exec api alembic upgrade head
```

Crie a organização e o usuário administrador inicial (bootstrap):

```bash
docker compose exec api python scripts/seed_admin.py "Consominas" admin@consominas.com "senha-forte"
```

## Rodando sem Docker (Postgres local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # aponte DATABASE_URL para seu Postgres local
alembic upgrade head
python scripts/seed_admin.py "Consominas" admin@consominas.com "senha-forte"
uvicorn app.main:app --reload
```

## Testes

Os testes usam um banco Postgres separado (`rda_campo_test` por padrão,
configurável via `DATABASE_URL` no ambiente de teste):

```bash
createdb rda_campo_test   # uma vez, se ainda não existir
pytest
```

## Estrutura

```
app/
  core/       # config, segurança (hash, JWT)
  db/         # engine, sessão, base declarativa
  models/     # SQLAlchemy: Organization, Contract, Team, User
  schemas/    # Pydantic: request/response
  api/routes/ # endpoints (auth, organizations, contracts, teams, users)
alembic/      # migrations
scripts/      # utilitários (seed do admin inicial)
tests/        # pytest
```

## Papéis (roles)

`admin`, `gestor`, `coordenador`, `coletor`, `convidado` — ver seção 7 da
especificação técnica. Regras de acesso atuais:

- **Criar** organização/contrato/equipe/usuário: apenas `admin`.
- **Listar/ver** contratos e equipes: `admin`, `gestor`, `coordenador`.
- **Listar/ver** usuários: `admin`, `gestor`.
- Qualquer usuário autenticado pode ver seus próprios dados em `/users/me`.

A restrição fina de "coordenador só vê o(s) contrato(s)/equipe(s) sob sua
responsabilidade" será implementada na Fase 3, junto com o modelo de RDA.
