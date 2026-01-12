# Manual Completo do Plugin ctx-monitor

**Context Oracle - Observabilidade e Auditoria para Claude Code CLI**

---

## Informacoes do Documento

| Campo | Valor |
|-------|-------|
| Versao | 0.3.0 |
| Data | 2026-01-12 |
| Autor | Murillo Dutt |
| Organizacao | Dutt Yeshua Technology Ltd |
| Licenca | MIT |

---

## Sumario

1. [Introducao](#1-introducao)
2. [Conceitos Fundamentais](#2-conceitos-fundamentais)
3. [Arquitetura do Plugin](#3-arquitetura-do-plugin)
4. [Instalacao e Configuracao](#4-instalacao-e-configuracao)
5. [Comandos Disponiveis](#5-comandos-disponiveis)
6. [Dashboard Visual](#6-dashboard-visual)
7. [Sistema de Eventos](#7-sistema-de-eventos)
8. [Analise de Traces](#8-analise-de-traces)
9. [Auditorias Modulares](#9-auditorias-modulares)
10. [Comparacao de Execucoes](#10-comparacao-de-execucoes)
11. [Exportacao de Diagnosticos](#11-exportacao-de-diagnosticos)
12. [Agent trace-analyzer](#12-agent-trace-analyzer)
13. [Skill trace-interpretation](#13-skill-trace-interpretation)
14. [Padroes de Falha Comuns](#14-padroes-de-falha-comuns)
15. [Casos de Uso Praticos](#15-casos-de-uso-praticos)
16. [Resolucao de Problemas](#16-resolucao-de-problemas)
17. [Referencia Tecnica](#17-referencia-tecnica)

---

## 1. Introducao

### 1.1 O que e o ctx-monitor?

O ctx-monitor (Context Oracle) e um plugin de observabilidade e auditoria desenvolvido especificamente para o Claude Code CLI. Seu proposito fundamental e fornecer visibilidade completa sobre o que acontece durante a execucao de sessoes do Claude Code, permitindo que desenvolvedores e equipes de engenharia de contexto compreendam, depurem e otimizem suas implementacoes.

Em um ambiente onde agentes de IA executam multiplas ferramentas, delegam tarefas para subagentes, disparam hooks e aplicam skills, a capacidade de rastrear cada evento torna-se essencial. O ctx-monitor preenche essa lacuna ao capturar, armazenar e analisar cada evento do pipeline de execucao.

### 1.2 Por que utilizar o ctx-monitor?

A complexidade dos sistemas baseados em Claude Code cresce exponencialmente quando combinamos:

- **Multiplos plugins** com comandos, agents e skills proprios
- **Hooks event-driven** que interceptam e modificam comportamentos
- **Subagentes autonomos** que executam tarefas delegadas
- **Configuracoes por projeto** com regras especificas

Sem uma ferramenta de observabilidade adequada, identificar a causa raiz de comportamentos inesperados torna-se uma tarefa frustrante e demorada. O ctx-monitor resolve este problema oferecendo:

1. **Rastreabilidade End-to-End**: Cada ferramenta chamada, cada hook disparado, cada subagente criado e terminado e registrado com timestamp preciso.

2. **Deteccao de Falhas Intermitentes**: Hooks que nao disparam consistentemente, ferramentas que falham esporadicamente, e padroes de erro que surgem apenas sob certas condicoes sao identificados automaticamente.

3. **Comparacao de Regressoes**: Ao capturar traces de sessoes em momentos diferentes, e possivel comparar comportamentos e identificar quando e onde regressoes foram introduzidas.

4. **Auditoria de Compliance**: Verificar se as execucoes seguem padroes esperados, se os formatos de saida estao corretos, e se nao ha conflitos de configuracao.

5. **Bundles de Diagnostico**: Criar pacotes anonimizados contendo traces, configuracoes e metadados para compartilhamento com equipes de suporte ou para documentacao de issues.

### 1.3 Publico-Alvo

Este manual destina-se a:

- **Engenheiros de Contexto**: Profissionais que projetam e otimizam prompts, hooks e configuracoes do Claude Code
- **Desenvolvedores de Plugins**: Criadores de extensoes que precisam depurar comportamentos complexos
- **Equipes de Suporte**: Tecnicos que analisam problemas reportados por usuarios
- **Auditores de Qualidade**: Responsaveis por garantir que sistemas de IA operam conforme especificado

---

## 2. Conceitos Fundamentais

### 2.1 Trace

Um trace e o registro cronologico completo de todos os eventos ocorridos durante uma sessao do Claude Code. Ele e armazenado no formato JSONL (JSON Lines), onde cada linha representa um evento individual.

```
Sessao Claude Code
     |
     v
[SessionStart] -> [UserPromptSubmit] -> [PreToolUse] -> [PostToolUse] -> ... -> [Stop] -> [SessionEnd]
     |                    |                  |                |                    |           |
     v                    v                  v                v                    v           v
  Trace Line 1      Trace Line 2       Trace Line 3     Trace Line 4         Trace Line N   Trace Line N+1
```

Cada trace line contem:
- Identificador unico do evento
- Identificador da sessao
- Timestamp em formato ISO8601
- Tipo do evento
- Status da operacao
- Dados especificos do tipo de evento

### 2.2 Sessao

Uma sessao representa uma instancia completa de interacao com o Claude Code, desde sua inicializacao ate seu encerramento. Cada sessao possui um identificador unico (UUID) que correlaciona todos os eventos pertencentes a ela.

### 2.3 Evento

Um evento e uma unidade atomica de rastreamento. O ctx-monitor captura nove tipos distintos de eventos, cada um representando um momento especifico no ciclo de vida da execucao:

| Evento | Momento de Captura |
|--------|-------------------|
| SessionStart | Inicio da sessao Claude Code |
| SessionEnd | Termino da sessao |
| PreToolUse | Antes de uma ferramenta executar |
| PostToolUse | Apos uma ferramenta completar |
| Stop | Quando o agente principal para |
| SubagentStop | Quando um subagente termina |
| UserPromptSubmit | Quando o usuario envia um prompt |
| PreCompact | Antes da compactacao de contexto |
| Notification | Quando uma notificacao e gerada |

### 2.4 Nivel de Log

O ctx-monitor oferece tres niveis de detalhamento para captura de eventos:

| Nivel | Eventos Capturados | Tamanho do Payload |
|-------|-------------------|-------------------|
| minimal | SessionStart, SessionEnd, Stop | 100 caracteres |
| medium | Todos os eventos | 500 caracteres |
| full | Todos os eventos | Ilimitado |

A escolha do nivel impacta diretamente no volume de dados armazenados e na granularidade da analise possivel.

---

## 3. Arquitetura do Plugin

### 3.1 Estrutura de Diretorios

```
ctx-monitor/
├── .claude-plugin/
│   └── plugin.json              # Manifest do plugin
├── commands/                     # Comandos slash disponiveis
│   ├── start.md                 # /ctx-monitor:start
│   ├── stop.md                  # /ctx-monitor:stop
│   ├── dashboard.md             # /ctx-monitor:dashboard
│   ├── report.md                # /ctx-monitor:report
│   ├── audit.md                 # /ctx-monitor:audit
│   ├── diff.md                  # /ctx-monitor:diff
│   ├── config.md                # /ctx-monitor:config
│   └── export-bundle.md         # /ctx-monitor:export-bundle
├── agents/
│   └── trace-analyzer.md        # Agent especializado em analise
├── skills/
│   └── trace-interpretation/
│       ├── SKILL.md             # Skill de interpretacao de traces
│       └── references/
│           ├── event-types.md   # Documentacao de tipos de evento
│           └── common-failures.md # Catalogo de padroes de falha
├── hooks/
│   ├── hooks.json               # Configuracao dos hooks de captura
│   └── scripts/
│       └── event-logger.sh      # Script de logging de eventos
├── scripts/                      # Scripts Python de analise
│   ├── log-parser.py            # Parser de logs
│   ├── audit-runner.py          # Orquestrador de auditorias
│   ├── audit-intermittency.py   # Auditoria de intermitencia
│   ├── audit-conflicts.py       # Auditoria de conflitos
│   ├── audit-tokens.py          # Auditoria de tokens
│   ├── audit-compliance.py      # Auditoria de compliance
│   ├── diff-engine.py           # Motor de comparacao
│   ├── bundle-creator.py        # Criador de bundles
│   ├── anonymizer.py            # Anonimizador de dados
│   └── config-manager.py        # Gerenciador de configuracao
├── templates/
│   └── ctx-monitor.local.md     # Template de configuracao
└── README.md                     # Documentacao resumida
```

### 3.2 Armazenamento de Dados

Os dados do ctx-monitor sao armazenados em cada projeto, no diretorio:

```
.claude/ctx-monitor/
├── config.json                   # Configuracao ativa
├── traces/
│   ├── sessions.json            # Indice de sessoes
│   ├── session_<uuid>.jsonl     # Trace da sessao
│   └── ...
└── ctx-monitor.local.md         # Configuracao do projeto
```

Esta abordagem garante que cada projeto mantenha seu proprio historico de execucao, permitindo analises contextualizadas e comparacoes dentro do escopo correto.

### 3.3 Fluxo de Dados

```
Evento Claude Code
        |
        v
   Hook Captura
   (event-logger.sh)
        |
        v
   Grava JSONL
   (traces/session_*.jsonl)
        |
        v
   Indexa Sessao
   (traces/sessions.json)
        |
        v
   Disponivel para Analise
   (report, audit, diff)
```

### 3.4 Sistema de Hooks

O ctx-monitor utiliza o sistema de hooks do Claude Code para interceptar eventos. Todos os nove tipos de eventos sao capturados atraves de um hook centralizado:

```json
{
  "description": "Context Oracle event logging hooks",
  "hooks": {
    "SessionStart": [{ "matcher": "*", "hooks": [{"type": "command", "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/event-logger.sh"}] }],
    "SessionEnd": [{ "matcher": "*", "hooks": [...] }],
    "PreToolUse": [{ "matcher": "*", "hooks": [...] }],
    "PostToolUse": [{ "matcher": "*", "hooks": [...] }],
    "SubagentStop": [{ "matcher": "*", "hooks": [...] }],
    "Stop": [{ "matcher": "*", "hooks": [...] }],
    "UserPromptSubmit": [{ "matcher": "*", "hooks": [...] }],
    "PreCompact": [{ "matcher": "*", "hooks": [...] }],
    "Notification": [{ "matcher": "*", "hooks": [...] }]
  }
}
```

O matcher `"*"` garante que todos os eventos de cada tipo sejam capturados, independentemente da ferramenta ou contexto.

---

## 4. Instalacao e Configuracao

### 4.1 Pre-requisitos

Antes de instalar o ctx-monitor, certifique-se de que seu ambiente atende aos seguintes requisitos:

- Claude Code CLI versao 2.1 ou superior
- Python 3.7 ou superior (para scripts de analise)
- Acesso de escrita ao diretorio do projeto

### 4.2 Instalacao via Marketplace

O metodo recomendado de instalacao e atraves do marketplace oficial:

```bash
/plugin install ctx-monitor@dutt-plugins-official
```

Apos a instalacao, reinicie o Claude Code para que os hooks sejam carregados.

### 4.3 Instalacao via curl

Para instalacao rapida em ambiente novo:

```bash
curl -sSL https://raw.githubusercontent.com/murillodutt/ctx-monitor/main/install.sh | bash
```

### 4.4 Configuracao Inicial

Apos a instalacao, inicialize a configuracao para seu projeto:

```bash
/ctx-monitor:config init
```

Este comando cria o arquivo `.claude/ctx-monitor.local.md` com as configuracoes padrao.

### 4.5 Arquivo de Configuracao

A configuracao e armazenada em formato YAML frontmatter:

```yaml
---
enabled: true
log_level: medium
events:
  - SessionStart
  - SessionEnd
  - PreToolUse
  - PostToolUse
  - Stop
  - SubagentStop
  - UserPromptSubmit
  - PreCompact
  - Notification
retention_days: 30
max_sessions: 100
anonymize_on_export: true
---
```

### 4.6 Opcoes de Configuracao

| Opcao | Tipo | Padrao | Descricao |
|-------|------|--------|-----------|
| enabled | boolean | true | Habilita ou desabilita o logging |
| log_level | string | medium | Nivel de detalhamento (minimal, medium, full) |
| events | array | todos | Lista de eventos a capturar |
| retention_days | integer | 30 | Dias para manter traces |
| max_sessions | integer | 100 | Numero maximo de sessoes retidas |
| anonymize_on_export | boolean | true | Anonimizar automaticamente ao exportar |
| tools_filter | array | [] | Filtrar apenas ferramentas especificas |
| exclude_patterns | array | [] | Padroes a ignorar |

### 4.7 Gitignore

Adicione as seguintes entradas ao `.gitignore` do projeto:

```
.claude/ctx-monitor/traces/
.claude/ctx-monitor.local.md
```

Isso evita que traces locais e configuracoes especificas sejam commitados ao repositorio.

---

## 5. Comandos Disponiveis

O ctx-monitor fornece sete comandos slash, todos prefixados com o namespace do plugin.

### 5.1 /ctx-monitor:start

**Proposito**: Inicia o monitoramento de eventos para a sessao atual.

**Sintaxe**:
```bash
/ctx-monitor:start [--level minimal|medium|full]
```

**Parametros**:
- `--level`: Define o nivel de detalhamento da captura

**Comportamento**:
1. Cria o diretorio de traces se nao existir
2. Gera um novo session_id
3. Atualiza o arquivo de configuracao com `enabled: true`
4. Confirma ao usuario que o monitoramento iniciou

**Exemplo**:
```bash
# Iniciar com nivel padrao (medium)
/ctx-monitor:start

# Iniciar com captura completa
/ctx-monitor:start --level full

# Iniciar com captura minima (apenas sessao)
/ctx-monitor:start --level minimal
```

### 5.2 /ctx-monitor:stop

**Proposito**: Encerra o monitoramento e preserva os logs.

**Sintaxe**:
```bash
/ctx-monitor:stop [--keep-logs]
```

**Parametros**:
- `--keep-logs`: Garante preservacao explicita dos logs (padrao: logs sempre preservados)

**Comportamento**:
1. Atualiza configuracao com `enabled: false`
2. Registra timestamp de parada
3. Reporta resumo da sessao ao usuario

**Exemplo**:
```bash
/ctx-monitor:stop
```

### 5.3 /ctx-monitor:report

**Proposito**: Gera relatorio analitico dos eventos capturados.

**Sintaxe**:
```bash
/ctx-monitor:report [--session <id>] [--format text|json|md]
```

**Parametros**:
- `--session`: ID especifico da sessao (padrao: mais recente)
- `--format`: Formato de saida (padrao: text)

**Comportamento**:
1. Localiza arquivos de trace
2. Executa o script log-parser.py
3. Apresenta sumario estruturado contendo:
   - Metricas da sessao
   - Estatisticas por ferramenta
   - Lista de erros
   - Timeline de eventos chave

**Exemplo**:
```bash
# Relatorio da sessao mais recente
/ctx-monitor:report

# Relatorio de sessao especifica em markdown
/ctx-monitor:report --session abc123 --format md
```

### 5.4 /ctx-monitor:audit

**Proposito**: Executa auditorias modulares nos traces.

**Sintaxe**:
```bash
/ctx-monitor:audit [--type all|intermittency|conflicts|tokens|compliance] [--format text|json|md]
```

**Parametros**:
- `--type`: Tipo de auditoria (padrao: all)
- `--format`: Formato de saida (padrao: text)

**Tipos de Auditoria**:

| Tipo | Descricao |
|------|-----------|
| intermittency | Detecta falhas intermitentes e padroes instáveis |
| conflicts | Identifica conflitos de configuracao |
| tokens | Analisa eficiencia de uso de tokens |
| compliance | Verifica conformidade de formatos |
| all | Executa todas as auditorias |

**Exemplo**:
```bash
# Auditoria completa
/ctx-monitor:audit

# Apenas verificar intermitencias
/ctx-monitor:audit --type intermittency

# Auditoria de compliance em JSON
/ctx-monitor:audit --type compliance --format json
```

### 5.5 /ctx-monitor:diff

**Proposito**: Compara traces entre sessoes para identificar regressoes.

**Sintaxe**:
```bash
/ctx-monitor:diff <session1> <session2>
/ctx-monitor:diff --last <n>
```

**Parametros**:
- `<session1> <session2>`: IDs de duas sessoes a comparar
- `--last <n>`: Comparar as ultimas N sessoes

**Comportamento**:
1. Localiza os traces especificados
2. Executa o script diff-engine.py
3. Apresenta diferencas categorizadas:
   - Ferramentas adicionadas/removidas
   - Mudancas em taxas de erro
   - Alteracoes de sequencia

**Exemplo**:
```bash
# Comparar duas sessoes especificas
/ctx-monitor:diff abc123 xyz789

# Comparar as duas ultimas sessoes
/ctx-monitor:diff --last 2
```

### 5.6 /ctx-monitor:config

**Proposito**: Gerencia configuracao do ctx-monitor.

**Sintaxe**:
```bash
/ctx-monitor:config [init|status|enable|disable|set <key> <value>]
```

**Acoes**:
- `status`: Mostra configuracao atual (padrao)
- `init`: Inicializa configuracao para o projeto
- `enable`: Habilita monitoramento
- `disable`: Desabilita monitoramento
- `set <key> <value>`: Define valor de configuracao

**Exemplo**:
```bash
# Verificar status
/ctx-monitor:config status

# Inicializar para projeto novo
/ctx-monitor:config init

# Alterar nivel de log
/ctx-monitor:config set log_level minimal

# Definir retencao
/ctx-monitor:config set retention_days 7
```

### 5.7 /ctx-monitor:export-bundle

**Proposito**: Cria pacote diagnostico para compartilhamento.

**Sintaxe**:
```bash
/ctx-monitor:export-bundle [--anonymize] [--include-config] [--output <path>]
```

**Parametros**:
- `--anonymize`: Anonimizar dados sensiveis (padrao: true)
- `--no-anonymize`: Manter dados sem anonimizacao
- `--include-config`: Incluir arquivos de configuracao (padrao: true)
- `--output`: Caminho customizado para o bundle

**Conteudo do Bundle**:
```
ctx-monitor-bundle.zip
├── traces/              # Arquivos de trace JSONL
│   ├── session_*.jsonl
│   └── sessions.json
├── config.json          # Snapshot de configuracao
├── environment.json     # Versoes de sistema/ferramentas
└── report.md            # Relatorio resumido
```

**Anonimizacao**:
O processo de anonimizacao remove:
- Chaves de API e tokens
- Senhas e segredos
- Caminhos com nomes de usuario
- Enderecos de email
- Enderecos IP internos

**Exemplo**:
```bash
# Bundle padrao (anonimizado, com config)
/ctx-monitor:export-bundle

# Bundle sem anonimizacao
/ctx-monitor:export-bundle --no-anonymize

# Bundle em local customizado
/ctx-monitor:export-bundle --output ./diagnostics/issue-123.zip
```

### 5.8 /ctx-monitor:dashboard

**Proposito**: Exibe dashboard visual com metricas e analise do context engineering stack.

**Sintaxe**:
```bash
/ctx-monitor:dashboard [--page <name>] [--session <id>] [--no-color]
```

**Parametros**:
- `--page`: Pagina a exibir (overview, stack, tools, timeline, alerts)
- `--session`: ID especifico da sessao (padrao: mais recente)
- `--no-color`: Desabilitar cores ANSI

**Paginas Disponiveis**:

| Pagina | Descricao |
|--------|-----------|
| overview | Health score, eventos, token usage, tool activity (default) |
| stack | Context engineering stack (rules, hooks, skills, agents) |
| tools | Performance de ferramentas com graficos e histogramas |
| timeline | Fluxo de eventos e distribuicao temporal |
| alerts | Alertas ativos, severidade, recomendacoes |

**Exemplo**:
```bash
# Ver overview (default)
/ctx-monitor:dashboard

# Ver context engineering stack
/ctx-monitor:dashboard --page stack

# Ver performance de ferramentas
/ctx-monitor:dashboard --page tools

# Ver timeline de eventos
/ctx-monitor:dashboard --page timeline

# Ver alertas e recomendacoes
/ctx-monitor:dashboard --page alerts

# Ver sessao especifica
/ctx-monitor:dashboard --session abc123 --page overview

# Sem cores (para logs)
/ctx-monitor:dashboard --no-color
```

---

## 6. Dashboard Visual

O dashboard do ctx-monitor oferece visualizacao rica em Unicode para analise de sessoes de monitoramento.

### 6.1 Visao Geral

O dashboard e dividido em 5 paginas navegaveis, cada uma focada em um aspecto diferente da sessao:

```
 [1] Overview  [2] Stack  [3] Tools  [4] Timeline  [5] Alerts
```

### 6.2 Elementos Graficos

O dashboard utiliza caracteres Unicode para visualizacoes ricas:

| Elemento | Caracteres | Uso |
|----------|------------|-----|
| Sparklines | `▁▂▃▄▅▆▇█` | Graficos de atividade ao longo do tempo |
| Progress | `○◔◑◕●` | Indicadores de taxa de sucesso (0%, 25%, 50%, 75%, 100%) |
| Bar Charts | `░▒▓█` | Distribuicao de chamadas e uso de recursos |
| Trends | `↑↓↗↘→` | Indicadores de tendencia |
| Box Drawing | `─│┌┐└┘├┤┬┴┼` | Layout de paineis e tabelas |

### 6.3 Pagina Overview

A pagina overview apresenta:

- **Header**: Session ID, projeto, duracao
- **Health Score**: Porcentagem de saude da sessao (baseado em taxa de erro)
- **Events**: Total de eventos com sparkline de atividade
- **Errors**: Contagem e taxa de erros
- **Token Usage**: Barra de uso com breakdown por componente
- **Tool Activity**: Top ferramentas com sparklines e taxa de sucesso
- **Quick Stats**: Metricas resumidas com tendencias

### 6.4 Pagina Stack

A pagina stack mostra o context engineering stack:

- **Stack Composition**: Barra horizontal mostrando proporcao de cada componente
- **Rules**: Arquivos de regras (CLAUDE.md, settings.json, etc.) com tokens e secoes
- **Hooks**: Eventos configurados, disparos, erros e taxa de sucesso
- **Skills & Agents**: Skills e agents disponiveis com uso

### 6.5 Pagina Tools

A pagina tools apresenta performance detalhada:

- **Call Distribution**: Bar chart horizontal de chamadas por ferramenta
- **Detailed Metrics**: Tabela com calls, success, errors, rate, tempo medio e desvio padrao
- **Error Breakdown**: Detalhamento de erros por ferramenta e tipo

### 6.6 Pagina Timeline

A pagina timeline mostra o fluxo temporal:

- **Event Flow**: Lista cronologica dos ultimos eventos
- **Session Events Summary**: Distribuicao de eventos por tipo

### 6.7 Pagina Alerts

A pagina alerts apresenta problemas detectados:

- **Active Alerts**: Lista de alertas com severidade e recomendacao
- **Alert Severity Distribution**: Bar chart de alertas por severidade
- **Recommendations**: Sugestoes baseadas na analise da sessao

### 6.8 Calculo do Health Score

O health score e calculado como:

```
Score = 100 - penalties

Penalties:
- Error rate (40% weight): errors/total_calls * 40
- Unreliable tools (30% weight): tools com >20% erro * 10 (max 30)
- Session completeness (20%): -10 se falta Start, -10 se falta End
- Event pairing (10%): (1 - PostToolUse/PreToolUse) * 10
```

---

## 7. Sistema de Eventos

### 7.1 SessionStart

Capturado quando uma nova sessao do Claude Code inicia.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:00:00.000Z",
  "event_type": "SessionStart",
  "cwd": "/path/to/project",
  "status": "started"
}
```

**Utilidade**: Identificar inicio de sessoes, correlacionar com ambiente de trabalho.

### 7.2 SessionEnd

Capturado quando a sessao termina.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "event_type": "SessionEnd",
  "status": "ended"
}
```

**Utilidade**: Calcular duracao de sessao, identificar terminacoes abruptas.

### 7.3 PreToolUse

Capturado imediatamente antes de uma ferramenta executar.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:05:00.000Z",
  "event_type": "PreToolUse",
  "tool_name": "Write",
  "args_preview": "file_path: /src/main.py, content: ...",
  "status": "pending"
}
```

**Ferramentas Comuns Rastreadas**:
- Read - Leitura de arquivos
- Write - Criacao de arquivos
- Edit - Modificacao de arquivos
- Bash - Comandos shell
- Glob - Pattern matching de arquivos
- Grep - Busca em conteudo
- Task - Delegacao para subagentes
- WebFetch - Busca de URLs
- WebSearch - Pesquisas web

**Utilidade**: Saber quais ferramentas foram invocadas e com quais argumentos.

### 7.4 PostToolUse

Capturado apos uma ferramenta completar.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:05:01.000Z",
  "event_type": "PostToolUse",
  "tool_name": "Write",
  "args_preview": "file_path: /src/main.py",
  "result_preview": "File written successfully",
  "status": "success",
  "duration_ms": 150,
  "error_message": null
}
```

**Status Possiveis**:
- `success`: Ferramenta completou sem erros
- `error`: Ferramenta falhou

**Utilidade**: Identificar falhas, medir performance, calcular taxas de erro.

### 7.5 Stop

Capturado quando o agente principal decide parar.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:25:00.000Z",
  "event_type": "Stop",
  "reason": "completed",
  "status": "completed"
}
```

**Razoes de Parada**:
- `completed`: Tarefa finalizada com sucesso
- `user_interrupt`: Usuario interrompeu
- `error`: Parou devido a erro
- `context_limit`: Janela de contexto esgotada

**Utilidade**: Entender por que o agente encerrou a execucao.

### 7.6 SubagentStop

Capturado quando um subagente (Task tool) termina.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:15:00.000Z",
  "event_type": "SubagentStop",
  "reason": "task_completed",
  "status": "completed"
}
```

**Utilidade**: Rastrear ciclo de vida de subagentes, correlacionar com tarefas delegadas.

### 7.7 UserPromptSubmit

Capturado quando o usuario envia um prompt.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:00:30.000Z",
  "event_type": "UserPromptSubmit",
  "prompt_preview": "Crie um arquivo de configuracao...",
  "prompt_length": 150,
  "status": "submitted"
}
```

**Utilidade**: Analisar padroes de interacao, correlacionar prompts com resultados.

### 7.8 PreCompact

Capturado antes da compactacao de contexto.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:20:00.000Z",
  "event_type": "PreCompact",
  "transcript_path": "/path/to/transcript",
  "status": "compacting"
}
```

**Utilidade**: Monitorar uso de contexto, identificar sessoes com contexto pesado.

### 7.9 Notification

Capturado quando uma notificacao e gerada.

**Schema**:
```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2024-01-15T10:10:00.000Z",
  "event_type": "Notification",
  "notification_type": "warning",
  "notification_message": "Large file detected...",
  "status": "notified"
}
```

**Tipos de Notificacao**:
- `info`: Mensagens informativas
- `warning`: Alertas
- `error`: Notificacoes de erro
- `success`: Confirmacoes de sucesso
- `permission`: Solicitacoes de permissao

**Utilidade**: Rastrear comunicacao com usuario, identificar situacoes de alerta.

### 7.10 Relacionamento entre Eventos

```
SessionStart
    |
    +-- UserPromptSubmit
    |
    +-- PreToolUse (Read)
    |       +-- PostToolUse (Read, success)
    |
    +-- PreToolUse (Task)
    |       +-- PreToolUse (Grep)
    |       |       +-- PostToolUse (Grep, success)
    |       +-- SubagentStop
    |       +-- PostToolUse (Task, success)
    |
    +-- Notification (permission)
    |
    +-- PreToolUse (Write)
    |       +-- PostToolUse (Write, error)
    |
    +-- PreCompact (se contexto esgotado)
    |
    +-- Stop
            +-- SessionEnd
```

---

## 8. Analise de Traces

### 8.1 Localizacao dos Traces

Os arquivos de trace sao armazenados em:

```
.claude/ctx-monitor/traces/
├── sessions.json              # Indice de todas as sessoes
├── session_<uuid>.jsonl       # Trace individual
└── ...
```

### 8.2 Formato JSONL

Cada linha do arquivo de trace e um objeto JSON independente:

```jsonl
{"event_id":"e1","session_id":"s1","timestamp":"...","event_type":"SessionStart","cwd":"/project","status":"started"}
{"event_id":"e2","session_id":"s1","timestamp":"...","event_type":"PreToolUse","tool_name":"Read","status":"pending"}
{"event_id":"e3","session_id":"s1","timestamp":"...","event_type":"PostToolUse","tool_name":"Read","status":"success"}
```

### 8.3 Comandos de Analise Manual

Para analises rapidas via linha de comando:

```bash
# Visualizar todos os eventos
cat session_abc123.jsonl | jq .

# Filtrar por tipo de evento
cat session_abc123.jsonl | jq 'select(.event_type == "PostToolUse")'

# Apenas erros
cat session_abc123.jsonl | jq 'select(.status == "error")'

# Contar eventos por tipo
cat session_abc123.jsonl | jq -s 'group_by(.event_type) | map({type: .[0].event_type, count: length})'

# Calcular taxa de erro por ferramenta
cat session_abc123.jsonl | jq -s '
  [.[] | select(.event_type == "PostToolUse")] |
  group_by(.tool_name) |
  map({
    tool: .[0].tool_name,
    total: length,
    errors: [.[] | select(.status == "error")] | length,
    error_rate: (([.[] | select(.status == "error")] | length) / length * 100)
  }) |
  sort_by(-.error_rate)
'
```

### 8.4 Indice de Sessoes

O arquivo `sessions.json` contem metadados de todas as sessoes:

```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "started_at": "2024-01-15T10:00:00Z",
      "cwd": "/project/path",
      "event_count": 150
    }
  ]
}
```

---

## 9. Auditorias Modulares

O sistema de auditoria do ctx-monitor e composto por quatro modulos independentes, cada um focado em uma categoria especifica de problemas.

### 9.1 Auditoria de Intermitencia

**Objetivo**: Detectar padroes de execucao instáveis.

**O que identifica**:
- Ferramentas que ora funcionam, ora falham
- Hooks que nao disparam consistentemente
- Execucoes parciais
- Padroes de erro oscilantes
- Problemas de estabilidade de sessao

**Script**: `audit-intermittency.py`

**Indicadores de Problema**:
- Taxa de sucesso < 90% para mesma ferramenta
- PreToolUse sem PostToolUse correspondente
- Multiplas sessoes curtas sequenciais

### 9.2 Auditoria de Conflitos

**Objetivo**: Identificar configuracoes contraditorias.

**O que identifica**:
- Instrucoes contraditorias em CLAUDE.md
- Secoes duplicadas
- Matchers de hooks competindo
- Conflitos de permissao em settings
- Comandos/skills duplicados

**Script**: `audit-conflicts.py`

**Arquivos Analisados**:
- `.claude/settings.json`
- `.claude/settings.local.json`
- `CLAUDE.md`
- Arquivos de hooks de todos os plugins

### 9.3 Auditoria de Tokens

**Objetivo**: Analisar eficiencia de uso de tokens.

**O que identifica**:
- Sessoes com uso excessivo de tokens
- Inputs de ferramentas muito grandes (>5000 tokens)
- Padroes redundantes de leitura de arquivos
- Uso ineficiente (alto tokens + alto erro)
- Carregamento pesado de contexto no inicio

**Script**: `audit-tokens.py`

**Metricas**:
- Tokens por ferramenta
- Tokens por sessao
- Densidade de tokens (tokens/evento)

### 9.4 Auditoria de Compliance

**Objetivo**: Verificar conformidade de formatos e padroes.

**O que identifica**:
- Eventos fora do schema esperado
- Timestamps em formato incorreto
- IDs de evento duplicados
- Mensagens de erro de baixa qualidade
- Inconsistencia em nomes de ferramentas
- Validacao do indice de sessoes

**Script**: `audit-compliance.py`

**Padroes Verificados**:
- ISO8601 para timestamps
- UUID para identificadores
- Estrutura JSON valida
- Campos obrigatorios presentes

### 9.5 Niveis de Severidade

Os resultados de auditoria sao classificados em tres niveis:

| Nivel | Significado | Exemplos |
|-------|-------------|----------|
| Critical | Atencao imediata necessaria | Corrupcao de dados, JSON invalido |
| Warning | Deve ser tratado em breve | Falhas intermitentes, conflitos |
| Info | Oportunidade de otimizacao | Melhorias de eficiencia |

---

## 10. Comparacao de Execucoes

### 10.1 Proposito

A comparacao de traces permite identificar diferencas entre execucoes, sendo essencial para:

- Deteccao de regressoes apos mudancas
- Validacao de correcoes
- Analise de impacto de atualizacoes
- Estabelecimento de baselines

### 10.2 Categorias de Diferenca

| Categoria | Descricao |
|-----------|-----------|
| Added Tools | Ferramentas chamadas na sessao2 mas nao na sessao1 |
| Removed Tools | Ferramentas na sessao1 mas nao na sessao2 |
| Changed Tools | Diferencas em contagem ou taxa de erro |
| Error Changes | Novos erros ou erros resolvidos |
| Sequence Changes | Alteracoes na ordem de execucao |

### 10.3 Interpretacao de Resultados

**Ferramentas Adicionadas**:
- Nova funcionalidade foi implementada
- Comportamento mudou para incluir passos adicionais

**Ferramentas Removidas**:
- Funcionalidade foi simplificada
- Possivel regressao se remocao foi inesperada

**Mudancas em Taxa de Erro**:
- Aumento indica possivel regressao
- Reducao indica melhoria

**Mudancas de Sequencia**:
- Pode indicar otimizacao de fluxo
- Pode indicar comportamento inesperado

---

## 11. Exportacao de Diagnosticos

### 11.1 Proposito do Bundle

O bundle de diagnostico e um pacote compactado contendo todas as informacoes necessarias para analisar problemas fora do ambiente original. Ele e util para:

- Compartilhar com equipes de suporte
- Documentar issues em repositorios
- Arquivar sessoes para referencia futura
- Analise em ambiente isolado

### 11.2 Conteudo do Bundle

```
ctx-monitor-bundle.zip
├── traces/
│   ├── session_abc123.jsonl    # Traces JSONL
│   └── sessions.json           # Indice
├── config.json                  # Configuracao snapshot
├── environment.json             # Informacoes de sistema
└── report.md                    # Relatorio resumido
```

### 11.3 Processo de Anonimizacao

A anonimizacao e aplicada automaticamente (padrao) e remove:

| Tipo de Dado | Padrao de Deteccao | Substituicao |
|--------------|-------------------|--------------|
| API Keys | `key`, `token`, `secret` | `[REDACTED_KEY]` |
| Senhas | `password`, `pwd` | `[REDACTED_PASSWORD]` |
| Emails | `*@*.*` | `[REDACTED_EMAIL]` |
| Paths de Usuario | `/Users/nome/`, `/home/nome/` | `/Users/[USER]/` |
| IPs Internos | `10.*`, `192.168.*`, `172.16-31.*` | `[REDACTED_IP]` |

### 11.4 Boas Praticas de Exportacao

1. **Sempre revise o bundle antes de compartilhar**: Mesmo com anonimizacao, verifique se nao ha dados sensiveis.

2. **Use anonimizacao por padrao**: So desative para analise interna.

3. **Inclua configuracao quando relevante**: Ajuda na reproducao do problema.

4. **Nomeie bundles significativamente**: Use convencao como `issue-123-bundle.zip`.

---

## 12. Agent trace-analyzer

### 13.1 Proposito

O trace-analyzer e um agente especializado em analise profunda de traces. Ele e ativado automaticamente quando o usuario solicita analise de execucao ou apos rodar `/ctx-monitor:report`.

### 13.2 Ativacao

O agente e ativado por frases como:
- "analisar traces"
- "encontrar problemas na execucao"
- "por que ha tantos erros nos traces?"
- "debug ctx-monitor logs"

### 12.3 Processo de Analise

1. **Localizacao de Traces**: Busca arquivos em `.claude/ctx-monitor/traces/`

2. **Parse e Extracao**: Le eventos e extrai campos relevantes

3. **Deteccao de Padroes**:
   - Taxas de erro > 10%
   - Falhas intermitentes (consistencia < 90%)
   - Performance (duracao > 5000ms)
   - Sequencias anormais

4. **Coleta de Evidencias**: Para cada problema, registra event_id, timestamp, mensagem de erro

5. **Geracao de Recomendacoes**: Sugere acoes corretivas especificas

### 12.4 Formato de Output

```markdown
## Trace Analysis Report

### Summary
- **Session ID**: [identificador]
- **Time Range**: [inicio] to [fim]
- **Total Events**: [contagem]
- **Error Rate**: [percentual]

### Issues Found

#### [CRITICAL/HIGH/MEDIUM/LOW] Titulo do Problema
**Pattern**: [tipo de padrao]
**Occurrences**: [contagem]
**Affected Components**: [lista]

**Evidence**:
- Event ID: [id] at [timestamp]

**Root Cause Analysis**:
[Explicacao]

**Remediation**:
1. [Acao]
2. [Acao]

---

### Tool Statistics
| Tool | Calls | Errors | Error Rate | Avg Duration |
|------|-------|--------|------------|--------------|

### Recommendations Summary
1. **Immediate**: [urgente]
2. **Short-term**: [melhorias]
3. **Long-term**: [arquiteturais]
```

### 12.5 Classificacao de Severidade

| Nivel | Criterios |
|-------|-----------|
| CRITICAL | Problemas que quebram sistema, perda de dados, seguranca |
| HIGH | Falhas significativas em funcionalidade core |
| MEDIUM | Problemas intermitentes, degradacao de performance |
| LOW | Anomalias menores, oportunidades de otimizacao |

---

## 13. Skill trace-interpretation

### 13.1 Proposito

A skill trace-interpretation fornece conhecimento especializado para interpretar traces do ctx-monitor. Ela e ativada quando o usuario precisa entender o significado dos dados capturados.

### 13.2 Ativacao

Frases que ativam a skill:
- "interpretar traces ctx-monitor"
- "entender logs de execucao"
- "o que significam os eventos ctx-monitor"
- "debugging trace output"

### 13.3 Conteudo da Skill

A skill inclui:
- Documentacao de todos os tipos de evento
- Catalogo de padroes de falha comuns
- Comandos jq para analise manual
- Checklist de troubleshooting

### 13.4 Referencias Bundled

```
skills/trace-interpretation/
├── SKILL.md                    # Documento principal
└── references/
    ├── event-types.md          # Documentacao completa de eventos
    └── common-failures.md      # Catalogo de padroes de falha
```

---

## 14. Padroes de Falha Comuns

### 14.1 Falhas Intermitentes

**Descricao**: A mesma chamada de ferramenta ora funciona, ora falha.

**Indicadores**:
- Ferramenta aparece com status `success` e `error`
- Nenhum padrao claro nos argumentos

**Causas Comuns**:
- Instabilidade de rede
- Condicoes de corrida
- Contencao de recursos
- Dependencias externas instaveis

**Remediacao**:
- Adicionar logica de retry com backoff exponencial
- Implementar tratamento de erro adequado
- Verificar status de servicos externos
- Monitorar uso de recursos

### 14.2 Hook Nao Dispara

**Descricao**: Um hook configurado nao executa quando esperado.

**Indicadores**:
- PreToolUse presente mas sem output de hook
- SessionStart sem contexto esperado de hook
- Nenhum output de debug do hook em `claude --debug`

**Causas Comuns**:
- Matcher nao corresponde ao nome da ferramenta
- Erro de sintaxe em hooks.json
- Plugin nao carregado
- Timeout excedido
- Script do hook falhando silenciosamente

**Remediacao**:
```bash
# Verificar hooks carregados
/hooks

# Validar configuracao
cat hooks/hooks.json | jq .

# Testar script diretamente
echo '{"tool_name": "Write"}' | bash hooks/scripts/event-logger.sh
```

### 14.3 Falhas em Cascata

**Descricao**: Um erro inicial desencadeia multiplos erros subsequentes.

**Indicadores**:
- Primeiro erro seguido de varios erros relacionados
- Mensagens de erro referenciam mesmo recurso

**Causas Comuns**:
- Dependencia faltando (arquivo/recurso nao criado)
- Estado corrompido de operacao anterior
- Tratamento de erro insuficiente
- Corrupcao de recurso compartilhado

**Remediacao**:
- Corrigir causa raiz (primeiro erro da cadeia)
- Adicionar fronteiras de erro entre operacoes
- Implementar mecanismos de rollback
- Adicionar health checks entre passos

### 14.4 Degradacao de Performance

**Descricao**: Tempos de execucao aumentam ao longo da sessao.

**Indicadores**:
- Mesma ferramenta leva mais tempo em eventos posteriores
- Erros relacionados a memoria aparecem

**Causas Comuns**:
- Vazamento de memoria
- Esgotamento de recursos
- Contexto muito grande
- Rate limiting de servico externo

**Remediacao**:
- Executar `/compact` para reduzir contexto
- Limpar arquivos temporarios
- Monitorar uso de memoria
- Verificar limites de API

### 14.5 Eventos Faltando

**Descricao**: Eventos esperados nao aparecem no trace.

**Indicadores**:
- PreToolUse sem PostToolUse correspondente
- SessionStart sem SessionEnd
- Gaps na sequencia de timestamps

**Causas Comuns**:
- Crash nao tratado
- Force quit pelo usuario
- Timeout do hook de logging
- Falha de escrita em disco

**Remediacao**:
- Verificar logs de crash
- Garantir timeouts suficientes para hooks
- Monitorar espaco em disco
- Adicionar flush apos escritas

### 14.6 Taxas de Erro Altas

**Descricao**: Taxa de erro de ferramenta excede 10%.

**Indicadores**:
- Muitos eventos com status `error`
- Mensagens de erro repetitivas

**Causas Comuns**:
- Argumentos invalidos
- Problemas de permissao
- Recurso nao encontrado
- Falhas de validacao

**Remediacao**:
- Revisar mensagens de erro para padroes
- Corrigir geracao de argumentos
- Verificar existencia de arquivos/recursos
- Validar inputs antes de chamar ferramentas

---

## 15. Casos de Uso Praticos

### 15.1 Debugging de Hooks que Nao Disparam

**Cenario**: Voce configurou um hook PreToolUse para validar escritas, mas ele parece nao estar funcionando.

**Procedimento**:

1. Inicie o monitoramento:
```bash
/ctx-monitor:start --level full
```

2. Execute a acao que deveria disparar o hook

3. Pare o monitoramento:
```bash
/ctx-monitor:stop
```

4. Gere o relatorio:
```bash
/ctx-monitor:report
```

5. Verifique se PreToolUse para Write aparece no trace

6. Se aparecer, o problema pode ser no hook em si. Execute auditoria:
```bash
/ctx-monitor:audit --type conflicts
```

### 15.2 Identificacao de Regressoes

**Cenario**: Apos atualizar um plugin, usuarios reportam comportamento diferente.

**Procedimento**:

1. Capture trace com versao antiga (se disponivel no historico)

2. Atualize o plugin

3. Capture novo trace executando mesma tarefa:
```bash
/ctx-monitor:start
# Execute a tarefa
/ctx-monitor:stop
```

4. Compare as sessoes:
```bash
/ctx-monitor:diff --last 2
```

5. Analise diferencas em:
   - Ferramentas adicionadas/removidas
   - Mudancas em taxa de erro
   - Alteracoes de sequencia

### 15.3 Auditoria de Compliance

**Cenario**: Voce precisa garantir que as execucoes seguem padroes estabelecidos.

**Procedimento**:

1. Execute sessao normalmente com monitoramento:
```bash
/ctx-monitor:start
# Trabalhe normalmente
/ctx-monitor:stop
```

2. Execute auditoria completa:
```bash
/ctx-monitor:audit --type all --format md
```

3. Revise cada categoria:
   - Compliance: Formatos e schemas
   - Conflicts: Configuracoes contraditorias
   - Tokens: Eficiencia de uso
   - Intermittency: Estabilidade

4. Exporte bundle para documentacao:
```bash
/ctx-monitor:export-bundle --output ./audit-2024-01.zip
```

### 15.4 Investigacao de Performance

**Cenario**: Sessoes estao demorando mais que o esperado.

**Procedimento**:

1. Inicie monitoramento com nivel full:
```bash
/ctx-monitor:start --level full
```

2. Execute tarefa problematica

3. Pare e analise:
```bash
/ctx-monitor:stop
/ctx-monitor:audit --type tokens
```

4. Identifique:
   - Ferramentas com maior duracao
   - Padroes de leitura redundante
   - Contexto pesado

5. Use o agent para analise profunda:
```
Analisar traces para problemas de performance
```

### 15.5 Compartilhamento com Suporte

**Cenario**: Voce encontrou um bug e precisa reportar para a equipe de suporte.

**Procedimento**:

1. Reproduza o problema com monitoramento ativo:
```bash
/ctx-monitor:start --level full
# Reproduza o bug
/ctx-monitor:stop
```

2. Gere relatorio para sua referencia:
```bash
/ctx-monitor:report --format md
```

3. Exporte bundle anonimizado:
```bash
/ctx-monitor:export-bundle --output ./issue-bug-report.zip
```

4. Revise o conteudo do bundle antes de enviar

5. Anexe o bundle ao ticket de suporte junto com:
   - Descricao do problema
   - Passos para reproducao
   - Comportamento esperado vs observado

---

## 16. Resolucao de Problemas

### 16.1 Monitoramento Nao Inicia

**Sintomas**:
- Comando `/ctx-monitor:start` nao produz efeito
- Nenhum trace e criado

**Verificacoes**:

1. Confirme que o plugin esta instalado:
```bash
/plugins
```

2. Verifique se hooks estao carregados:
```bash
/hooks
```

3. Confira se o diretorio de traces existe:
```bash
ls -la .claude/ctx-monitor/traces/
```

4. Reinicie o Claude Code para recarregar hooks

### 16.2 Traces Vazios ou Incompletos

**Sintomas**:
- Arquivo de trace existe mas esta vazio
- Eventos faltando no trace

**Verificacoes**:

1. Confirme nivel de log:
```bash
/ctx-monitor:config status
```

2. Verifique se eventos estao configurados:
```bash
cat .claude/ctx-monitor.local.md
```

3. Teste hook diretamente:
```bash
echo '{"event_type":"test"}' | bash plugins/ctx-monitor/hooks/scripts/event-logger.sh
```

4. Verifique permissoes de escrita no diretorio

### 16.3 Erros nos Scripts Python

**Sintomas**:
- Comandos report, audit, diff falham
- Erros de import ou sintaxe

**Verificacoes**:

1. Confirme versao do Python:
```bash
python3 --version
```

2. Verifique dependencias instaladas

3. Teste script isoladamente:
```bash
python3 scripts/log-parser.py --help
```

### 16.4 Bundle Nao Exporta

**Sintomas**:
- Comando export-bundle falha
- Bundle gerado esta incompleto

**Verificacoes**:

1. Verifique espaco em disco

2. Confirme permissoes de escrita no destino

3. Verifique se existem traces para exportar:
```bash
ls .claude/ctx-monitor/traces/
```

### 16.5 Auditoria Retorna Falsos Positivos

**Sintomas**:
- Auditoria reporta problemas que nao existem
- Muitos warnings desnecessarios

**Acoes**:

1. Revise configuracao de exclude_patterns

2. Ajuste thresholds se disponivel

3. Filtre resultados por severidade relevante

---

## 17. Referencia Tecnica

### 17.1 Variaveis de Ambiente

| Variavel | Descricao |
|----------|-----------|
| CLAUDE_PLUGIN_ROOT | Caminho absoluto do plugin |
| CLAUDE_PROJECT_DIR | Diretorio raiz do projeto |
| CLAUDE_ENV_FILE | Arquivo para persistir env vars (SessionStart) |

### 17.2 Exit Codes dos Scripts

| Codigo | Significado |
|--------|-------------|
| 0 | Sucesso, nenhum problema critico |
| 1 | Problemas criticos detectados |
| 2 | Erro de execucao do script |

### 17.3 Formatos de Saida

| Formato | Extensao | Uso |
|---------|----------|-----|
| text | .txt | Visualizacao rapida |
| json | .json | Integracao programatica |
| md | .md | Documentacao, sharing |

### 17.4 Limites e Restricoes

| Parametro | Limite | Nota |
|-----------|--------|------|
| Tamanho maximo de evento | 1MB | Eventos maiores sao truncados |
| Timeout de hook | 5s | Configuravel em hooks.json |
| Retencao padrao | 30 dias | Configuravel |
| Sessoes maximas | 100 | Configuravel |

### 17.5 Dependencias

| Dependencia | Versao Minima | Proposito |
|-------------|---------------|-----------|
| Python | 3.7 | Scripts de analise |
| jq | 1.6 | Analise manual de JSON |
| bash | 4.0 | Scripts de hook |

---

## Glossario

| Termo | Definicao |
|-------|-----------|
| Agent | Subprocesso autonomo que executa tarefas complexas |
| Bundle | Pacote compactado de diagnostico |
| Context | Janela de informacao disponivel para o modelo |
| Hook | Script que intercepta eventos do Claude Code |
| JSONL | JSON Lines - formato de uma linha JSON por registro |
| Matcher | Padrao que determina quando um hook dispara |
| Session | Instancia completa de interacao Claude Code |
| Skill | Modulo de conhecimento especializado |
| Subagent | Agente delegado via ferramenta Task |
| Trace | Registro cronologico de eventos de uma sessao |

---

## Suporte e Contribuicao

**Reportar Problemas**:
- GitHub Issues: https://github.com/murillodutt/ctx-monitor/issues

**Contribuir**:
- Pull Requests sao bem-vindos
- Siga as diretrizes de contribuicao no repositorio

**Contato**:
- Autor: Murillo Dutt
- Email: murillo@duttyeshua.com
- Organizacao: Dutt Yeshua Technology Ltd

---

**Fim do Manual**

Versao 0.3.0 - 2026-01-12
