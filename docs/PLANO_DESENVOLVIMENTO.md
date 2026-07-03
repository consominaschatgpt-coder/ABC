# Plano de Desenvolvimento — Sistema de RDA de Campo

Baseado em `Especificacao_Tecnica_RDA_Campo.docx` (Grupo Consominas Engenharia).

## Stack

- **Backend**: Python (FastAPI) + PostgreSQL + SQLAlchemy + Alembic
- **Painel web**: React
- **App mobile**: Flutter (offline-first, SQLite local)
- **Hospedagem**: a definir pela Consominas (requisito: código e hospedagem sob controle da Consominas, sem lock-in)

## Fases

### Fase 0 — Fundação do repositório
- Estrutura de monorepo: `backend/`, `web/`, `mobile/`, `docs/`
- docker-compose com PostgreSQL para desenvolvimento local

### Fase 1 — Backend: fundação (dados + auth)
- Hierarquia: Organização → Contrato → Equipe/Frente → Usuário (papéis: Admin, Gestor, Coordenador, Coletor, Convidado)
- Autenticação JWT, hashing de senha
- Migrations (Alembic)
- CRUD básico de organizações, contratos, equipes, usuários
- Regra: coordenador só acessa RDAs do(s) contrato(s)/equipe(s) sob sua responsabilidade

### Fase 2 — Construtor de formulários (backend)
- `FormTemplate` por contrato: campos dinâmicos (texto, número, data/hora, seleção única/múltipla, foto, assinatura, GPS)
- Lógica condicional entre campos
- Versionamento de template (editar não pode quebrar RDAs antigos)

### Fase 3 — RDA: submissão, aprovação e auditoria
- Modelo de RDA: respostas + fotos + metadata, vinculado a contrato/equipe/template/versão
- Estados: Rascunho → Enviado → Em revisão → Aprovado / Reprovado (com motivo)
- Edição pelo coordenador antes de aprovar, com trilha de auditoria (dado original preservado, diff, quem, quando)
- Níveis de aprovação configuráveis (mínimo 1, idealmente 2: coordenador → gestor)
- Notificações (novo RDA para aprovar, RDA reprovado devolvido)

### Fase 4 — Painel web
- Login e navegação por papel
- CRUD de contratos, equipes, usuários e permissões
- Construtor de formulários (UI)
- Listagem de RDAs com filtros (contrato, equipe, data, status, coletor) + mapa
- Tela de revisão/aprovação com histórico de edição

### Fase 5 — App mobile (Flutter, offline-first)
- Armazenamento local (SQLite/drift), funcionamento 100% offline
- Renderização dinâmica do formulário a partir do template + lógica condicional
- Foto (câmera e galeria), assinatura, GPS opcional
- Fila de sincronização visível + motor de sync com resolução de conflitos
- Login por usuário ou por equipe/viatura

### Fase 6 — Motor de relatórios
- Templates configuráveis (leiaute, cabeçalho/identidade Consominas, tabelas, fotos posicionadas, campos calculados)
- Geração automática a partir de RDAs aprovados
- Consolidação diária, por período e por contrato
- Exportação PDF, Excel/CSV, GeoJSON/KMZ (quando houver GPS)

### Fase 7 — Integrações
- API REST documentada (OpenAPI via FastAPI)
- Webhooks (ex.: ao aprovar um RDA)
- Exportação/envio automático (planilha, Google Drive, e-mail)
- Preferência por formatos abertos

### Fase 8 — Não-funcionais e homologação
- Segurança: criptografia em trânsito/repouso, perfis/permissões
- Conformidade LGPD
- Trilha de auditoria em toda edição/aprovação
- Escala: 44–60 usuários de campo, 20+ simultâneos sem degradação
- Critérios de aceite (seção 11 da especificação):
  - RDA em modo avião com foto, sync sem perda de dados
  - Edição pelo coordenador auditada
  - Relatório final equivalente/superior ao Excel atual
  - Exportação via API e planilha
  - 20+ usuários simultâneos sem degradação
- Deploy conforme hospedagem definida

## Status atual

- [x] Fase 0 — estrutura do monorepo criada
- [x] Fase 1 — backend: hierarquia de dados, autenticação JWT, CRUD, testes
- [x] Fase 2 — construtor de formulários (FormTemplate versionado, lógica condicional)
- [ ] Fase 3 — em andamento
