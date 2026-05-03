# Skill: refactor-arch — Refatoração Arquitetural Automatizada

Skill para o Claude Code que audita e refatora projetos backend para o padrão MVC de forma automatizada e agnóstica de tecnologia.

---

## Análise Manual

### Projeto 1 — code-smells-project (Python/Flask)

| # | Severidade | Arquivo | Problema |
|---|---|---|---|
| 1 | CRITICAL | `app.py:7` | `SECRET_KEY` hardcoded em código-fonte |
| 2 | CRITICAL | `app.py:47-78` | Endpoints `/admin/reset-db` e `/admin/query` sem nenhuma autenticação — qualquer usuário anônimo pode destruir o banco ou executar SQL arbitrário |
| 3 | CRITICAL | `models.py:28,48,92,109,127,291-297` | SQL Injection — todas as queries construídas via concatenação de strings ou f-strings com variáveis do usuário |
| 4 | HIGH | `app.py:8,88` | `DEBUG=True` hardcoded — expõe o debugger interativo do Werkzeug em produção (permite RCE) |
| 5 | HIGH | `models.py:127-128` | Senhas armazenadas em plaintext no banco de dados |
| 6 | HIGH | `controllers.py:272-282` | Endpoint `/health` retorna `secret_key`, `db_path` e `debug: true` em texto aberto |
| 7 | HIGH | `models.py:187-200` | N+1 queries: 3 níveis de cursores aninhados para buscar pedidos com itens e produtos |
| 8 | MEDIUM | `database.py:4` | `db_connection = None` como global mutável com `check_same_thread=False` |
| 9 | MEDIUM | `models.py:77-87,93-103` | Campo `senha` incluído na resposta dos endpoints de usuários |
| 10 | MEDIUM | `models.py:256-262` | Magic numbers para thresholds de desconto sem constantes nomeadas |
| 11 | LOW | `app.py:88` | Porta `5000` hardcoded |
| 12 | LOW | `controllers.py:42-43` | Lista de categorias válidas definida inline dentro da função |
| 13 | LOW | `controllers.py` (múltiplas linhas) | Logging via `print()` sem módulo de logging estruturado |

**Justificativa dos principais:** Os dois endpoints admin sem auth (item 2) são a falha mais grave — qualquer pessoa com acesso à rede pode chamar `POST /admin/reset-db` e apagar tudo. O SQL Injection (item 3) em combinação com o `/admin/query` transforma qualquer XSS ou SSRF em exfiltração completa de dados.

---

### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

| # | Severidade | Arquivo | Problema |
|---|---|---|---|
| 1 | CRITICAL | `src/AppManager.js:1-141` | God Class: DB init, routing, checkout, relatórios e gestão de usuários todos no mesmo arquivo de 141 linhas |
| 2 | CRITICAL | `src/utils.js:2-6` | Credenciais de produção hardcoded: `dbPass`, `paymentGatewayKey`, `smtpUser` |
| 3 | CRITICAL | `src/utils.js:13-20` | `badCrypto()` — "hash" de senha via Base64 repetida 10.000x, completamente reversível; o próprio nome da função reconhece que é inseguro |
| 4 | HIGH | `src/AppManager.js:28-78` | Callback hell com 5 níveis de aninhamento no checkout; tratamento de erros inconsistente em cada nível |
| 5 | HIGH | `src/AppManager.js:28-78` | Toda lógica de negócio do checkout (validação de cartão, criação de usuário, matrícula, pagamento, audit log) dentro do route handler |
| 6 | HIGH | `src/AppManager.js:131-137` | DELETE de usuário sem cascade — deixa enrollments e payments órfãos no banco |
| 7 | MEDIUM | `src/AppManager.js:33-35` | Validação do checkout só checa presença dos campos; sem validação de formato de email, número de cartão ou tipo de courseId |
| 8 | MEDIUM | `src/utils.js:9-10` | `globalCache = {}` e `totalRevenue = 0` como estado global mutável compartilhado entre requests |
| 9 | MEDIUM | `src/app.js` | Sem middleware de tratamento de erros — erros retornam strings misturadas com JSON |
| 10 | LOW | `src/AppManager.js:1` | `sqlite3.verbose()` é no-op desde sqlite3 v4+ |
| 11 | LOW | `src/AppManager.js:29-34` | Nomes de variáveis criptografados: `u`, `e`, `p`, `cid`, `cc` para campos do body |

**Justificativa dos principais:** A `badCrypto()` (item 3) é o problema mais insidioso — o código parece fazer algo sofisticado (10.000 iterações) mas é completamente reversível. Qualquer breach do banco entrega todas as senhas em texto claro. As credenciais de gateway de pagamento hardcoded (item 2) são um risco financeiro direto.

---

### Projeto 3 — task-manager-api (Python/Flask)

| # | Severidade | Arquivo | Problema |
|---|---|---|---|
| 1 | CRITICAL | `app.py:13` | `SECRET_KEY = 'super-secret-key-123'` hardcoded |
| 2 | CRITICAL | `services/notification_service.py:9-10` | Credenciais Gmail hardcoded: `email_user` e `email_password = 'senha123'` |
| 3 | HIGH | `models/user.py:29,32` | Senhas hashadas com MD5 — algoritmo quebrado com rainbow tables públicas |
| 4 | HIGH | `models/user.py:17-25` | `to_dict()` inclui `'password': self.password` — hash MD5 exposto em todos os endpoints de usuários |
| 5 | HIGH | `routes/task_routes.py:41-57` | N+1 queries: `User.query.get()` e `Category.query.get()` dentro do loop de tasks |
| 6 | MEDIUM | `routes/task_routes.py:30-39,71-80,171-180,282-287` + `routes/report_routes.py:33-43` | Lógica de `overdue` duplicada em 5 lugares diferentes |
| 7 | MEDIUM | `routes/report_routes.py:53-68` | N+1 query no relatório: `Task.query.filter_by(user_id=u.id)` dentro do loop de usuários |
| 8 | MEDIUM | Todas as rotas | Nenhum endpoint tem autenticação; o token gerado no login (`'fake-jwt-token-' + str(user.id)`) nunca é validado |
| 9 | MEDIUM | `routes/task_routes.py:96,99,100,110,113` | Magic numbers e listas de status/prioridade duplicadas entre create e update |
| 10 | LOW | Múltiplos arquivos | `datetime.utcnow()` deprecated desde Python 3.12 |
| 11 | LOW | Múltiplos arquivos | `except:` sem tipo — silencia todos os erros incluindo `KeyboardInterrupt` |
| 12 | LOW | Múltiplos arquivos | Logging via `print()` |

**Justificativa dos principais:** Apesar de ter mais estrutura que os outros projetos, a falha de MD5 (item 3) combinada com a exposição do hash em todos os responses de usuários (item 4) é grave — qualquer GET /users entrega o material para crackear todas as senhas offline. A ausência total de autenticação (item 8) significa que o token do login é decorativo.

---

## Construção da Skill

### Decisões de design

**Estrutura do SKILL.md:** Organizado em 3 fases explicitamente sequenciais com um CHECKPOINT obrigatório entre a Fase 2 e a Fase 3. Cada fase referencia os arquivos de conhecimento que precisa ler antes de executar, em vez de embutir o conhecimento no próprio SKILL.md — isso mantém o arquivo principal como um orquestrador de fluxo, enquanto os arquivos de referência carregam o conteúdo especializado.

**Arquivos de referência criados:**

| Arquivo | Propósito |
|---|---|
| `stack-detection.md` | Heurísticas de detecção: language → framework → DB → endpoints → domain → architecture |
| `anti-patterns.md` | 12 anti-patterns com sinais de grep exatos, severidade e exemplos de onde foram encontrados |
| `audit-report-template.md` | Template ASCII exato da Fase 2, com regras de preenchimento de cada campo |
| `mvc-architecture.md` | Target MVC, responsabilidades de cada camada, estratégia adaptativa (MONOLITH-REWRITE vs PARTIAL-IMPROVE) |
| `refactor-playbook.md` | 10 transformações T-01 a T-10, cada uma com código Before/After em Python e Node |
| `smoke-test.md` | Procedimento completo de boot, poll, teste de cada endpoint e teardown |

**Anti-patterns escolhidos e por quê:**

Os 12 anti-patterns foram selecionados para cobrir as 4 severidades com distribuição equilibrada e para mapear diretamente os problemas encontrados nos 3 projetos na análise manual:

- **CRITICAL (AP-01, AP-02, AP-03):** SQL Injection, credenciais hardcoded e God Class — as 3 falhas que aparecem em todos os projetos e têm impacto imediato
- **HIGH (AP-04, AP-05, AP-06, AP-07):** Hashing inseguro, Fat Controller, Callback Hell e endpoints sem auth — violações SOLID que tornam manutenção e testes inviáveis
- **MEDIUM (AP-08, AP-09, AP-10):** N+1 queries, validação duplicada e estado global mutável — problemas de performance e qualidade com impacto real em produção
- **LOW (AP-11, AP-12):** APIs deprecated e magic numbers — melhorias de legibilidade e forward-compatibility

**Como a skill é agnóstica de tecnologia:**

1. Cada comando grep nos anti-patterns inclui `--include="*.py" --include="*.js"` — procura nos dois
2. O playbook tem seções Before/After separadas para Python e Node
3. O `stack-detection.md` define o protocolo de decisão: detectar linguagem primeiro, depois bifurcar para Step 2a (Python) ou Step 2b (Node)
4. O `mvc-architecture.md` define estruturas-alvo para Flask e Express separadamente
5. O `smoke-test.md` tem seções de boot separadas para cada runtime

**Estratégia adaptativa (MONOLITH-REWRITE vs PARTIAL-IMPROVE):**

Um dos maiores desafios foi garantir que a Fase 3 não destruísse estrutura já existente no projeto 3. A solução foi o algoritmo de decisão baseado em dois indicadores: número de diretórios de camadas conhecidas (`layer_dirs`) e número de arquivos de código no root (`root_files`). Se `layer_dirs >= 2` e `root_files <= 3`, a estratégia é PARTIAL-IMPROVE — preservar o que está correto e só adicionar/corrigir o que está errado.

**Desafios encontrados:**

- **Projeto 2 tinha app.js não atualizado:** Os controllers/models/routes foram criados mas o `src/app.js` continuou usando o `AppManager` legado. Isso foi corrigido atualizando o entry point para usar as novas rotas e o middleware de erro.
- **Dependências faltando no projeto 2:** `sqlite` (wrapper Promise) e `dotenv` foram adicionados ao `package.json` — sem eles o `database/connection.js` e `config/settings.js` falhariam no boot.

---

## Resultados

### Resumo dos relatórios de auditoria

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| code-smells-project (Python/Flask) | 4 | 5 | 3 | 3 | **15** |
| ecommerce-api-legacy (Node.js/Express) | 3 | 4 | 3 | 2 | **12** |
| task-manager-api (Python/Flask) | 2 | 3 | 4 | 3 | **12** |

### Comparação antes/depois da estrutura

#### Projeto 1 — code-smells-project

**Antes:**
```
code-smells-project/
├── app.py          # rotas + config + admin endpoints
├── controllers.py  # validação + lógica de negócio
├── models.py       # 4 domínios + SQL injection + plaintext passwords
└── database.py     # global mutable connection
```

**Depois:**
```
code-smells-project/
├── app.py                          # composition root apenas
└── src/
    ├── config/
    │   ├── settings.py             # env vars, SECRET_KEY, PORT, DEBUG
    │   └── database.py             # get_db() request-scoped
    ├── models/
    │   ├── produto_model.py        # queries parametrizadas
    │   ├── usuario_model.py        # werkzeug password hash
    │   └── pedido_model.py         # JOIN para N+1
    ├── controllers/
    │   ├── produto_controller.py   # validação centralizada
    │   ├── usuario_controller.py
    │   └── pedido_controller.py
    ├── views/
    │   └── routes.py               # apenas HTTP: parse → call → respond
    └── middlewares/
        └── error_handler.py        # tratamento centralizado de erros
```

#### Projeto 2 — ecommerce-api-legacy

**Antes:**
```
src/
├── app.js          # entry point
├── AppManager.js   # God Class: DB + routing + checkout + reports + user delete
└── utils.js        # credenciais hardcoded + badCrypto() + globals mutáveis
```

**Depois:**
```
src/
├── app.js                      # composition root: usa routes + errorHandler
├── config/settings.js          # env vars (PAYMENT_GATEWAY_KEY, DB_PASS, etc.)
├── database/connection.js      # Promise-based sqlite, schema init
├── models/
│   ├── userModel.js
│   ├── courseModel.js
│   └── reportModel.js
├── controllers/
│   ├── checkoutController.js   # async/await, validação, processCard
│   ├── reportController.js
│   └── userController.js
├── routes/index.js             # Router com os 3 endpoints
└── middlewares/errorHandler.js # middleware centralizado de erro
```

#### Projeto 3 — task-manager-api

**Antes:**
```
task-manager-api/
├── app.py              # SECRET_KEY hardcoded, debug=True
├── models/user.py      # MD5 + senha exposta no to_dict()
├── routes/task_routes.py   # N+1 queries, validação duplicada, overdue 3x
├── routes/user_routes.py   # MD5 login, sem auth
├── routes/report_routes.py # N+1 por usuário, overdue 2x
└── services/notification_service.py  # Gmail hardcoded
```

**Pendente (Fase 3 não executada — projeto 3 ainda não refatorado):** ver seção "Como Executar".

### Checklist de validação

#### Projeto 1 — code-smells-project ✅

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (E-commerce API — produtos, pedidos, usuários)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (15 findings)
- [x] Detecção de APIs deprecated incluída (debug=True, porta hardcoded)
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (src/config, models, controllers, views, middlewares)
- [x] Configuração extraída para módulo de config (SECRET_KEY, DEBUG, PORT via os.getenv)
- [x] Models criados para abstrair dados (produto_model, usuario_model, pedido_model)
- [x] Views/Routes separadas para roteamento (src/views/routes.py com Blueprint)
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado (middlewares/error_handler.py)
- [x] Entry point claro (app.py como composition root)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente

#### Projeto 2 — ecommerce-api-legacy ⚠️

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Node.js)
- [x] Framework detectado corretamente (Express 4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS API — cursos, matrículas, checkout)
- [x] Número de arquivos analisados condiz com a realidade (3 arquivos: AppManager, app, utils)

**Fase 2 — Auditoria**
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (12 findings)
- [x] Detecção de APIs deprecated incluída (sqlite3.verbose())
- [x] Skill pausa e pede confirmação antes da Fase 3

**Fase 3 — Refatoração**
- [x] Estrutura de diretórios segue padrão MVC (config, database, models, controllers, routes, middlewares)
- [x] Configuração extraída para módulo de config (settings.js usa process.env)
- [x] Models criados para abstrair dados (userModel, courseModel, reportModel)
- [x] Views/Routes separadas para roteamento (routes/index.js)
- [x] Controllers concentram o fluxo da aplicação (checkoutController, reportController, userController)
- [x] Error handling centralizado (middlewares/errorHandler.js)
- [x] Entry point atualizado (src/app.js usa novas rotas e middleware)
- [ ] Aplicação inicia sem erros — *requer `npm install` após adição de `sqlite` e `dotenv` ao package.json*
- [ ] Endpoints originais respondem corretamente — *dependente do npm install*

#### Projeto 3 — task-manager-api ❌

**Fase 1 — Análise**
- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask + SQLAlchemy)
- [x] Domínio da aplicação descrito corretamente (Task Manager API)
- [x] Número de arquivos analisados condiz com a realidade (8 arquivos)

**Fase 2 — Auditoria**
- [x] Relatório gerado e salvo em reports/audit-project-3.md
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (12 findings)
- [x] Detecção de APIs deprecated incluída (datetime.utcnow())
- [x] Relatório inclui estratégia de refatoração (Partial-Improve)

**Fase 3 — Refatoração**
- [ ] Não executada ainda — ver "Como Executar"

---

## Como Executar

### Pré-requisitos

- **Claude Code** instalado e configurado (`claude --version`)
- Python 3.10+ com `pip` (projetos 1 e 3)
- Node.js 18+ com `npm` (projeto 2)

### Projeto 1 — code-smells-project

```bash
cd code-smells-project
claude "/refactor-arch"
```

Para validar manualmente após a refatoração:

```bash
cd code-smells-project
cp .env.example .env         # preencha SECRET_KEY
source .venv/bin/activate
pip install -r requirements.txt
python app.py &
curl http://localhost:5000/health
curl http://localhost:5000/produtos
kill %1
```

### Projeto 2 — ecommerce-api-legacy

```bash
cd ecommerce-api-legacy
claude "/refactor-arch"
```

Para validar manualmente após a refatoração:

```bash
cd ecommerce-api-legacy
cp .env.example .env         # preencha PAYMENT_GATEWAY_KEY, etc.
npm install
node src/app.js &
curl http://localhost:3000/health
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Test","eml":"t@t.com","c_id":1,"card":"4111111111111111"}'
kill %1
```

> **Nota:** O `package.json` foi atualizado para incluir `sqlite` e `dotenv`. Execute `npm install` antes de iniciar.

### Projeto 3 — task-manager-api

A Fase 3 ainda precisa ser executada. A skill está copiada e o relatório de auditoria está salvo. Para executar:

```bash
cd task-manager-api
claude "/refactor-arch"
# Quando perguntado sobre o número do projeto, responda: 3
# Ao exibir o relatório da Fase 2, confirme com: y
```

A skill identificará a estratégia como **PARTIAL-IMPROVE** e irá:
1. Criar `config/settings.py` com `SECRET_KEY` e `FLASK_DEBUG` via env vars
2. Criar `controllers/` extraindo lógica de negócio das routes
3. Criar `middlewares/error_handler.py` e `middlewares/auth.py`
4. Corrigir `models/user.py` (MD5 → werkzeug, remover senha do to_dict)
5. Corrigir `services/notification_service.py` (credenciais → env vars)
6. Extrair `is_overdue()` para `utils/helpers.py`
7. Atualizar `app.py` para carregar SECRET_KEY do ambiente

Para validar após a Fase 3:

```bash
cd task-manager-api
pip install -r requirements.txt
python seed.py
python app.py &
curl http://localhost:5000/health
curl http://localhost:5000/tasks
curl http://localhost:5000/users
kill %1
```

### Como validar que a refatoração funcionou

Para qualquer projeto, a validação passa quando:

1. O servidor inicia sem erros de import ou de banco de dados
2. `GET /health` retorna `200` com `{"status": "ok"}`
3. Os endpoints de listagem (GET /produtos, GET /tasks, GET /users) retornam `200`
4. Os endpoints de criação (POST) retornam `400` para payload vazio (validação funcionando)
5. Nenhum endpoint retorna `5xx`
