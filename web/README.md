# Painel web — Sistema de RDA de Campo

Painel de gestão (React + TypeScript + Vite) para o backend em `../backend`.
Fase 4 do plano em `../docs/PLANO_DESENVOLVIMENTO.md`.

## Rodando localmente

```bash
cp .env.example .env   # aponte VITE_API_BASE_URL para a API (backend rodando)
npm install
npm run dev
```

Abre em `http://localhost:5173`. O backend precisa estar rodando (veja
`../backend/README.md`) e com CORS liberado para essa origem
(`cors_origins` em `app/core/config.py`, já inclui `localhost:5173` por
padrão).

## Estrutura

```
src/
  api/         # client HTTP (fetch + JWT) e tipos compartilhados com o backend
  auth/        # AuthContext (login, usuário atual, logout)
  components/  # Layout (nav por papel) e ProtectedRoute (guarda de rotas)
  pages/       # uma página por rota
```

## Telas

- **Login** — autentica e guarda o JWT em `localStorage`.
- **RDAs** (`/rdas`) — lista com filtro por status; coletor pode criar um
  novo RDA (a equipe é resolvida via `/users/me/teams`); detalhe
  (`/rdas/:id`) mostra respostas, permite editar/enviar (coletor) ou
  revisar/corrigir/aprovar/reprovar (coordenador/admin), com o dado
  original preservado e a trilha de auditoria completa.
- **Formulários** (`/form-templates`) — construtor de campos do RDA por
  contrato: cria novas versões (rascunho) com tipos, opções e lógica
  condicional, e publica a versão ativa.
- **Contratos / Equipes / Usuários** — CRUD básico; a tela de equipe
  (`/teams/:id`) gerencia os membros (vínculo usuário↔equipe usado para o
  escopo de acesso do coordenador).

Navegação e permissões de escrita seguem o papel do usuário logado
(admin/gestor/coordenador/coletor), espelhando as regras já aplicadas no
backend.

## Pendências conhecidas

- Visualização em mapa dos RDAs com GPS (mencionada na especificação) ainda
  não foi implementada — fica para quando o motor de relatórios (Fase 6)
  também precisar de dados georreferenciados.
- Upload real de foto/assinatura: os campos `foto` e `assinatura` hoje
  aceitam texto livre (referência/nome do arquivo); a integração com
  armazenamento de objetos (S3-compatível) é um requisito não-funcional
  ainda não implementado.
