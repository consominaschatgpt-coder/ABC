# App mobile — Sistema de RDA de Campo

App Flutter offline-first para o coletor preencher o RDA em campo (sem
sinal) e sincronizar automaticamente ao recuperar conexão. Fase 5 do plano
em `../docs/PLANO_DESENVOLVIMENTO.md`.

## Rodando localmente

Precisa do Flutter SDK (`https://docs.flutter.dev/get-started/install`) e de
um emulador Android/iOS ou aparelho físico — este projeto foi desenvolvido e
testado neste ambiente **sem** emulador disponível (só `flutter analyze` e
`flutter test`); rodar de fato (`flutter run`) exige esse setup à parte.

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000  # emulador Android -> localhost da máquina
```

Em iOS simulator ou dispositivo físico, troque `API_BASE_URL` pelo endereço
acessível do backend (não use `10.0.2.2`, que é específico do emulador
Android).

## Testes e análise estática

```bash
flutter analyze
flutter test
```

## Arquitetura

```
lib/
  core/          # ApiClient (JWT), SessionStore (secure storage), AuthController/Repository
  db/             # AppDatabase (drift/SQLite): cache de formulários + RDAs locais
  models/         # espelham os schemas do backend (FieldDefinition, User, Team)
  repositories/    # RdaRepository (regras de escrita local) e FormTemplateRepository (cache)
  services/       # form_validation.dart — mesma validação do backend, rodando local
  sync/           # SyncEngine — fila de sincronização
  widgets/        # DynamicForm — renderiza os campos a partir do FormTemplateVersion
  screens/        # LoginScreen, RdaListScreen, RdaFormScreen
```

### Por que SQLite local + fila de sincronização

O app precisa funcionar 100% offline (plâtos sem sinal). O fluxo é:

1. **Login**: online na primeira vez; token e usuário ficam em
   `flutter_secure_storage`, então reabrir o app funciona sem rede.
2. Ao logar, o app busca as equipes do coletor (`GET /users/me/teams`) e
   **cacheia localmente** (`CachedFormVersions`) o formulário publicado do
   contrato de cada equipe — isso é o que permite criar um RDA novo
   offline depois.
3. Criar/editar/preencher um RDA grava só no SQLite local
   (`LocalRdas`, status `rascunhoLocal`). Nada disso toca a rede.
4. "Enviar RDA" valida localmente (mesmas regras do
   `app/services/form_validation.py` do backend — tipos, opções, e
   obrigatoriedade respeitando lógica condicional) e, se ok, marca o
   registro como `filaEnvio` — **não** chama a API ainda.
5. O `SyncEngine` observa conectividade (`connectivity_plus`) e, ao
   detectar rede, varre a fila (`filaEnvio` e `erro`, para permitir retry)
   e para cada item chama `POST /rdas` (cria) + `POST /rdas/{id}/submit`
   (envia) — reproduzindo a máquina de estados do backend. Se a criação já
   tinha sido feita numa tentativa anterior (`remoteId` já setado), só
   reenvia o `submit`, sem duplicar o RDA.

Status local (`rascunhoLocal` → `filaEnvio` → `enviando` → `sincronizado` /
`erro`) é **diferente** do status de negócio do RDA no backend
(rascunho/enviado/em_revisao/...) — o primeiro é só "esse registro já saiu
do aparelho ou não".

### Campos de foto, assinatura e GPS

- **Foto**: `image_picker`, câmera ou galeria (permite usar foto já
  carimbada por câmera externa, como pede a especificação).
- **Assinatura**: `signature` (canvas de desenho), salva como PNG
  base64-encoded na resposta.
- **Localização**: `geolocator`, captura `lat,lng` sob demanda.

Nenhum desses três foi coberto por teste automatizado porque dependem de
plugins com canal de plataforma nativo (câmera, GPS) que não existe no
harness de teste headless — precisam ser validados manualmente num
emulador/aparelho real.

## Pendências conhecidas

- Upload real das fotos/assinatura para o backend/storage: hoje ficam como
  caminho de arquivo local (foto) ou base64 (assinatura) no JSON de
  respostas; falta o endpoint de upload e a integração com storage de
  objetos (S3-compatível), que é um requisito não-funcional ainda não
  implementado em nenhuma camada.
- Resolução de conflitos de sincronização mais sofisticada (ex.: RDA
  editado em dois aparelhos) não foi implementada — o cenário atual (um
  RDA pertence a um único coletor, criado uma vez) não produz conflito na
  prática, mas isso deve ser revisitado se o app passar a permitir edição
  colaborativa offline.
- Sem Android/iOS toolchain neste ambiente de desenvolvimento: o app nunca
  rodou de fato numa tela — só `flutter analyze` (sem erros) e
  `flutter test` (21 testes, todos passando). Testar num
  emulador/dispositivo real antes de considerar esta fase pronta para
  produção.
