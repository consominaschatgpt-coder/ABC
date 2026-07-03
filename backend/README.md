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
  models/     # SQLAlchemy: Organization, Contract, Team, User, FormTemplate/Version
  schemas/    # Pydantic: request/response
  api/routes/ # endpoints (auth, organizations, contracts, teams, users, form_templates)
alembic/      # migrations
scripts/      # utilitários (seed do admin inicial)
tests/        # pytest
```

## Construtor de formulários (Fase 2)

`FormTemplate` é o modelo de RDA de um contrato; cada edição gera uma nova
`FormTemplateVersion` **imutável** (o conteúdo dos campos não muda depois de
criada). Apenas uma versão pode estar `is_published=True` por vez — é essa a
versão "atual" que a equipe de campo preenche. RDAs (Fase 3) vão referenciar
o `version_id` específico, então editar/publicar uma nova versão nunca
quebra RDAs já preenchidos com a versão anterior.

Tipos de campo suportados: `texto`, `numero`, `data_hora`, `selecao_unica`,
`selecao_multipla`, `foto`, `assinatura`, `localizacao`. Campos de seleção
exigem `options`; qualquer campo pode ter `condition` (`{"field": "...",
"equals": "..."}`) para lógica condicional simples.

Endpoints principais:

- `POST /form-templates` — cria o template + versão 1 (rascunho)
- `GET /form-templates?contract_id=` — lista templates
- `GET /form-templates/{id}` — detalhe + versão publicada atual
- `GET /form-templates/{id}/versions` — histórico de versões (rascunhos e publicadas)
- `POST /form-templates/{id}/versions` — nova versão (rascunho)
- `POST /form-templates/{id}/versions/{version_id}/publish` — publica uma versão (despublica a anterior)

Apenas `admin` cria/edita/publica. Leitura é permitida a `admin`, `gestor`,
`coordenador` e `coletor` (o app de campo precisa buscar a versão atual para
renderizar o formulário).

## Papéis (roles)

`admin`, `gestor`, `coordenador`, `coletor`, `convidado` — ver seção 7 da
especificação técnica. Regras de acesso atuais:

- **Criar** organização/contrato/equipe/usuário: apenas `admin`.
- **Listar/ver** contratos e equipes: `admin`, `gestor`, `coordenador`.
- **Listar/ver** usuários: `admin`, `gestor`.
- Qualquer usuário autenticado pode ver seus próprios dados em `/users/me`.

A restrição fina de "coordenador só vê o(s) contrato(s)/equipe(s) sob sua
responsabilidade" será implementada na Fase 3, junto com o modelo de RDA.
