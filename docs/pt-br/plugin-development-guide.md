# Claude Code Plugin Development Guide

Manual completo para desenvolvimento de plugins para Claude Code CLI.

**Baseado em:** claude-plugins-official (Anthropic) + plugin-dev oficial
**Versao:** 0.3.5
**Ultima atualizacao:** 2026-01-12

---

## Sumario

1. [Arquitetura de Diretorios](#1-arquitetura-de-diretorios)
2. [Estrutura do Marketplace (GitHub)](#2-estrutura-do-marketplace-github)
3. [Estrutura de Plugin](#3-estrutura-de-plugin)
4. [Comandos (Slash Commands)](#4-comandos-slash-commands)
5. [Agents](#5-agents)
6. [Skills](#6-skills)
7. [Hooks](#7-hooks)
8. [MCP Servers](#8-mcp-servers)
9. [Arquivos de Configuracao Local](#9-arquivos-de-configuracao-local)
10. [Processo de Instalacao](#10-processo-de-instalacao)
11. [Progressive Disclosure](#11-progressive-disclosure)
12. [Best Practices](#12-best-practices)
13. [Troubleshooting](#13-troubleshooting)
14. [Checklist](#14-checklist)

---

## 1. Arquitetura de Diretorios

O Claude Code usa tres diretorios principais para gerenciar plugins:

```
~/.claude/plugins/
├── known_marketplaces.json    # Registro de marketplaces
├── installed_plugins.json     # Registro de plugins instalados
├── marketplaces/              # Repositorios clonados
│   ├── claude-plugins-official/
│   └── seu-marketplace/
└── cache/                     # Plugins extraidos (usados em runtime)
    ├── claude-plugins-official/
    │   ├── hookify/<commit-sha>/
    │   └── plugin-dev/<commit-sha>/
    └── seu-marketplace/
        └── seu-plugin/<commit-sha>/
```

### Fluxo de Instalacao

1. **Marketplace e registrado** em `known_marketplaces.json`
2. **Repositorio e clonado** para `marketplaces/<nome>/`
3. **Plugin e extraido** para `cache/<marketplace>/<plugin>/<version>/`
4. **Plugin e registrado** em `installed_plugins.json`

---

## 2. Estrutura do Marketplace (GitHub)

Um marketplace e um repositorio GitHub que contem multiplos plugins.

### Estrutura Oficial

```
marketplace-name/
├── .claude-plugin/
│   └── marketplace.json       # APENAS este arquivo aqui!
├── plugins/                   # Plugins internos
│   ├── plugin-a/
│   └── plugin-b/
├── external_plugins/          # Plugins de terceiros (opcional)
├── LICENSE
└── README.md
```

### IMPORTANTE: Raiz do Marketplace

Na pasta `.claude-plugin/` da **raiz do repositorio**:
- marketplace.json - DEVE existir
- plugin.json - NAO deve existir aqui!

### marketplace.json

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "seu-marketplace",
  "description": "Descricao do marketplace",
  "owner": {
    "name": "Seu Nome",
    "email": "email@exemplo.com"
  },
  "plugins": [
    {
      "name": "seu-plugin",
      "description": "Descricao do plugin",
      "version": "1.0.0",
      "author": {
        "name": "Seu Nome",
        "email": "email@exemplo.com"
      },
      "source": "./plugins/seu-plugin",
      "category": "development",
      "homepage": "https://github.com/user/repo",
      "tags": ["community-managed"]
    }
  ]
}
```

### Referencia de Campos do marketplace.json

#### Campos de Nivel Raiz

| Campo | Obrigatorio | Tipo | Descricao |
|-------|-------------|------|-----------|
| `$schema` | Nao | string | URL do schema JSON para validacao |
| `name` | **Sim** | string | Identificador unico do marketplace |
| `description` | **Sim** | string | Descricao breve do marketplace |
| `owner` | **Sim** | object | Informacoes do dono do marketplace |
| `plugins` | **Sim** | array | Lista de definicoes de plugins |

#### Objeto Owner

| Campo | Obrigatorio | Tipo | Descricao |
|-------|-------------|------|-----------|
| `name` | **Sim** | string | Nome do dono/organizacao |
| `email` | **Sim** | string | Email de contato |

#### Campos de Entrada de Plugin

| Campo | Obrigatorio | Tipo | Descricao |
|-------|-------------|------|-----------|
| `name` | **Sim** | string | Identificador do plugin (kebab-case) |
| `description` | **Sim** | string | Visao geral da funcionalidade do plugin |
| `author` | **Sim** | object | Criador do plugin (name, email) |
| `source` | **Sim** | string/object | Localizacao do plugin (caminho ou objeto URL) |
| `category` | **Sim** | string | Categoria de classificacao |
| `version` | Nao | string | Versao semantica (ex: "1.0.0") |
| `homepage` | Nao | string | URL da homepage/repositorio do projeto |
| `tags` | Nao | array | Labels (ex: "community-managed") |
| `strict` | Nao | boolean | Flag de rigidez |
| `lspServers` | Nao | object | Configuracao de Language Server Protocol |

#### Categorias Disponiveis

- `development` - Ferramentas e workflows de desenvolvimento
- `productivity` - Melhorias de produtividade
- `security` - Ferramentas e orientacao de seguranca
- `learning` - Recursos educacionais
- `testing` - Utilitarios de teste
- `database` - Ferramentas de banco de dados
- `design` - Utilitarios de design
- `deployment` - Automacao de deploy
- `monitoring` - Monitoramento e observabilidade

#### Formatos de Source

**Referencia de caminho (recomendado para plugins internos):**
```json
"source": "./plugins/seu-plugin"
```

**Objeto URL (para repositorios externos):**
```json
"source": {
  "source": "url",
  "url": "https://github.com/user/repo.git"
}
```

#### Configuracao de LSP Server (Opcional)

Para plugins que fornecem integracao com Language Server Protocol:

```json
"lspServers": {
  "server-name": {
    "command": "nome-executavel",
    "args": ["--arg1", "--arg2"],
    "extensionToLanguage": {
      ".ext": "language-id"
    },
    "startupTimeout": 5000
  }
}
```

---

## 3. Estrutura de Plugin

Baseado no example-plugin e plugin-dev oficiais da Anthropic.

### Estrutura Completa

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json        # Plugin metadata (REQUIRED)
├── .mcp.json              # MCP server configuration (optional)
├── commands/              # Slash commands (optional)
│   └── command-name.md
├── agents/                # Agent definitions (optional)
│   └── agent-name.md
├── skills/                # Skill definitions (optional)
│   └── skill-name/
│       ├── SKILL.md       # Required for each skill
│       ├── references/    # Detailed documentation
│       ├── examples/      # Working examples
│       └── scripts/       # Utility scripts
├── hooks/                 # Hook definitions (optional)
│   ├── hooks.json
│   └── scripts/
├── scripts/               # Shared utilities
└── README.md              # Documentation (REQUIRED)
```

### Regras Criticas

1. **Localizacao do manifest**: `plugin.json` DEVE estar em `.claude-plugin/`
2. **Localizacao de componentes**: Todos os diretorios (commands, agents, skills, hooks) DEVEM estar na raiz do plugin, NAO dentro de `.claude-plugin/`
3. **Componentes opcionais**: Criar apenas diretorios para componentes que o plugin usa
4. **Convencao de nomes**: Usar kebab-case para todos os diretorios e arquivos

### plugin.json

Localizacao: `.claude-plugin/plugin.json`

#### Exemplo Minimo (Padrao Oficial Anthropic)

```json
{
  "name": "seu-plugin",
  "description": "Descricao do plugin",
  "author": {
    "name": "Seu Nome",
    "email": "email@exemplo.com"
  }
}
```

#### Exemplo Estendido (Com Campos Opcionais)

```json
{
  "name": "seu-plugin",
  "description": "Descricao do plugin",
  "version": "1.0.0",
  "author": {
    "name": "Seu Nome",
    "email": "email@exemplo.com"
  }
}
```

### Referencia de Campos do plugin.json

| Campo | Obrigatorio | Tipo | Descricao |
|-------|-------------|------|-----------|
| `name` | **Sim** | string | Identificador do plugin (kebab-case). Define namespace dos comandos. |
| `description` | **Sim** | string | Descricao breve da funcionalidade do plugin |
| `author` | **Sim** | object | Informacoes do criador do plugin |
| `version` | Nao | string | Versao semantica (ex: "1.0.0") |

#### Objeto Author

| Campo | Obrigatorio | Tipo | Descricao |
|-------|-------------|------|-----------|
| `name` | **Sim** | string | Nome do autor/organizacao |
| `email` | **Sim** | string | Email de contato |

> **Nota:** Os plugins oficiais da Anthropic usam apenas `name`, `description` e `author`. O campo `version` e opcional mas recomendado para rastreamento de releases.

### Comportamento de Namespace

O campo `name` define o **namespace** dos comandos:
- `name: "ctx-monitor"` -> comandos aparecem como `/ctx-monitor:*`

---

## 4. Comandos (Slash Commands)

Localizacao: `commands/*.md`

### CRITICO: Comandos sao Instrucoes PARA Claude

**Comandos sao escritos para consumo do agente, nao para humanos.**

Quando um usuario invoca `/command-name`, o conteudo do comando se torna as instrucoes do Claude. Escrever comandos como diretivas PARA Claude sobre o que fazer.

**Abordagem correta (instrucoes para Claude):**
```markdown
Revisar este codigo para vulnerabilidades de seguranca incluindo:
- SQL injection
- XSS attacks
- Problemas de autenticacao

Fornecer numeros de linha especificos e ratings de severidade.
```

**Abordagem incorreta (mensagens para usuario):**
```markdown
Este comando vai revisar seu codigo para problemas de seguranca.
Voce recebera um relatorio com detalhes das vulnerabilidades.
```

### Formato Oficial

```yaml
---
description: Short description for /help
argument-hint: <required-arg> [optional-arg]
allowed-tools: [Read, Glob, Grep, Bash]
model: sonnet
---
```

### Frontmatter Options

| Campo | Descricao |
|-------|-----------|
| `description` | Descricao curta mostrada em /help |
| `argument-hint` | Dicas de argumentos mostradas ao usuario |
| `allowed-tools` | Ferramentas pre-aprovadas (reduz prompts de permissao) |
| `model` | Override do modelo: "haiku", "sonnet", "opus" |
| `disable-model-invocation` | Previne invocacao programatica |

### CRITICO: NAO Use Campo `name`

```yaml
# ERRADO - sobrescreve namespace automatico
---
name: start
description: Start monitoring
---
# Resultado: /start (sem namespace!)

# CORRETO - usa namespace do plugin.json
---
description: Start monitoring
---
# Resultado: /seu-plugin:start
```

### Argumentos Dinamicos

#### Usando $ARGUMENTS

```markdown
---
description: Fix issue by number
argument-hint: [issue-number]
---

Fix issue #$ARGUMENTS following our coding standards.
```

**Uso:** `/fix-issue 123` -> "Fix issue #123 following..."

#### Usando Argumentos Posicionais

```markdown
---
description: Review PR with priority and assignee
argument-hint: [pr-number] [priority] [assignee]
---

Review pull request #$1 with priority level $2.
After review, assign to $3 for follow-up.
```

**Uso:** `/review-pr 123 high alice`

### Referencias de Arquivo

```markdown
---
description: Review specific file
argument-hint: [file-path]
---

Review @$1 for:
- Code quality
- Best practices
- Potential bugs
```

**Uso:** `/review-file src/api/users.ts`

### Execucao Bash em Comandos

```markdown
---
description: Review code changes
allowed-tools: Read, Bash(git:*)
---

Files changed: !`git diff --name-only`

Review each file for code quality.
```

### ${CLAUDE_PLUGIN_ROOT}

Usar para referenciar arquivos do plugin de forma portavel:

```markdown
---
description: Analyze using plugin script
allowed-tools: Bash(node:*)
---

Run analysis: !`node ${CLAUDE_PLUGIN_ROOT}/scripts/analyze.js $1`
```

---

## 5. Agents

Localizacao: `agents/*.md`

Agents sao subprocessos autonomos que lidam com tarefas complexas e multi-step independentemente.

### Formato Completo

```markdown
---
name: agent-identifier
description: Use this agent when [triggering conditions]. Examples:

<example>
Context: [Situation description]
user: "[User request]"
assistant: "[How assistant should respond and use this agent]"
<commentary>
[Why this agent should be triggered]
</commentary>
</example>

model: inherit
color: blue
tools: ["Read", "Write", "Grep"]
---

You are [agent role description]...

**Your Core Responsibilities:**
1. [Responsibility 1]
2. [Responsibility 2]

**Analysis Process:**
[Step-by-step workflow]

**Output Format:**
[What to return]
```

### Frontmatter Fields

| Campo | Obrigatorio | Formato | Exemplo |
|-------|-------------|---------|---------|
| name | Sim | lowercase-hyphens (3-50 chars) | code-reviewer |
| description | Sim | Text + examples | Use when... <example>... |
| model | Sim | inherit/sonnet/opus/haiku | inherit |
| color | Sim | Color name | blue, cyan, green, yellow, magenta, red |
| tools | Nao | Array of tool names | ["Read", "Grep"] |

### Validacao de Identifier

```
Valido: code-reviewer, test-gen, api-analyzer-v2
Invalido: ag (muito curto), -start (comeca com hifen), my_agent (underscore)
```

**Regras:**
- 3-50 caracteres
- Apenas letras minusculas, numeros, hifens
- Deve comecar e terminar com alfanumerico

### Cores e Uso

| Cor | Uso Recomendado |
|-----|-----------------|
| blue/cyan | Analise, review |
| green | Tarefas orientadas a sucesso |
| yellow | Cautela, validacao |
| red | Critico, seguranca |
| magenta | Criativo, geracao |

### System Prompt Design

**DO:**
- Escrever em segunda pessoa ("You are...", "You will...")
- Ser especifico sobre responsabilidades
- Fornecer processo step-by-step
- Definir formato de output
- Incluir padroes de qualidade
- Manter abaixo de 10,000 caracteres

**DON'T:**
- Escrever em primeira pessoa ("I am...", "I will...")
- Ser vago ou generico
- Omitir passos do processo
- Deixar formato de output indefinido

---

## 6. Skills

Localizacao: `skills/<nome>/SKILL.md`

Skills sao pacotes modulares e auto-contidos que estendem as capacidades do Claude fornecendo conhecimento especializado.

### Anatomia de uma Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Codigo executavel (Python/Bash/etc.)
    ├── references/       - Documentacao para carregar conforme necessario
    ├── examples/         - Exemplos funcionais
    └── assets/           - Arquivos para output (templates, icones, fontes)
```

### Frontmatter de Skill

```yaml
---
name: Skill Name
description: This skill should be used when the user asks to "specific phrase 1", "specific phrase 2", or mentions "keyword". Include exact phrases users would say.
version: 1.0.0
---
```

| Campo | Obrigatorio | Descricao |
|-------|-------------|-----------|
| `name` | **Sim** | Identificador da skill |
| `description` | **Sim** | Condicoes de ativacao - quando Claude deve usar |
| `version` | Nao | Versao semantica |

### Escrevendo Descriptions Efetivas

A description e crucial - diz ao Claude quando invocar a skill.

**Bom exemplo:**
```yaml
description: This skill should be used when the user asks to "create a hook", "add a PreToolUse hook", "validate tool use", or mentions hook events (PreToolUse, PostToolUse, Stop).
```

**Mau exemplo:**
```yaml
description: Use this skill when working with hooks.  # Pessoa errada, vago
description: Provides hook guidance.  # Sem trigger phrases
```

**Importante:** Usar terceira pessoa ("This skill should be used when...") e incluir frases especificas que usuarios diriam.

### Bundled Resources

#### scripts/
Codigo executavel para tarefas que requerem confiabilidade deterministica.

**Quando incluir:** Quando o mesmo codigo e reescrito repetidamente ou confiabilidade deterministica e necessaria.

#### references/
Documentacao e material de referencia para carregar conforme necessario no contexto.

**Quando incluir:** Para documentacao que Claude deve referenciar enquanto trabalha.
**Best practice:** Se arquivos sao grandes (>10k palavras), incluir patterns de busca grep no SKILL.md.

#### examples/
Exemplos de codigo funcionais que usuarios podem copiar e adaptar.

#### assets/
Arquivos nao destinados a carregar no contexto, mas usados no output (templates, imagens, boilerplate).

### Estilo de Escrita

**SKILL.md body:** Escrever usando **forma imperativa/infinitiva** (instrucoes verb-first), nao segunda pessoa.

**Correto (imperativo):**
```
To create a hook, define the event type.
Configure the MCP server with authentication.
Validate settings before use.
```

**Incorreto (segunda pessoa):**
```
You should create a hook by defining the event type.
You need to configure the MCP server.
```

---

## 7. Hooks

Localizacao: `hooks/hooks.json`

Hooks sao scripts de automacao event-driven que executam em resposta a eventos do Claude Code.

### Tipos de Hook

#### Prompt-Based Hooks (Recomendado)

Usa decisao LLM-driven para validacao context-aware:

```json
{
  "type": "prompt",
  "prompt": "Evaluate if this tool use is appropriate: $TOOL_INPUT",
  "timeout": 30
}
```

**Eventos suportados:** Stop, SubagentStop, UserPromptSubmit, PreToolUse

#### Command Hooks

Executa comandos bash para checagens deterministicas:

```json
{
  "type": "command",
  "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh",
  "timeout": 60
}
```

### Formato hooks.json para Plugins

**IMPORTANTE:** Para hooks de plugin em `hooks/hooks.json`, usar formato wrapper:

```json
{
  "description": "Validation hooks for code quality",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/validate.sh"
          }
        ]
      }
    ]
  }
}
```

**Key points:**
- Campo `description` e opcional
- Campo `hooks` e required wrapper contendo os eventos
- Este e o formato **especifico de plugin**

### Eventos Disponiveis

| Evento | Quando | Uso |
|--------|--------|-----|
| PreToolUse | Antes de ferramenta | Validacao, modificacao |
| PostToolUse | Apos ferramenta | Feedback, logging |
| UserPromptSubmit | Input do usuario | Contexto, validacao |
| Stop | Agent parando | Check de completude |
| SubagentStop | Subagent terminou | Validacao de tarefa |
| SessionStart | Sessao inicia | Carregamento de contexto |
| SessionEnd | Sessao termina | Cleanup, logging |
| PreCompact | Antes de compact | Preservar contexto |
| Notification | Usuario notificado | Logging, reacoes |

### Matchers

```json
// Match exato
"matcher": "Write"

// Multiplas ferramentas
"matcher": "Read|Write|Edit"

// Wildcard (todas ferramentas)
"matcher": "*"

// Regex patterns
"matcher": "mcp__.*__delete.*"  // Todas ferramentas MCP delete
```

### Variaveis de Ambiente

Disponiveis em todos os command hooks:

- `$CLAUDE_PROJECT_DIR` - Caminho raiz do projeto
- `$CLAUDE_PLUGIN_ROOT` - Diretorio do plugin (usar para caminhos portaveis)
- `$CLAUDE_ENV_FILE` - Apenas SessionStart: persistir env vars aqui
- `$CLAUDE_CODE_REMOTE` - Definido se rodando em contexto remoto

### Exit Codes

- `0` - Sucesso (stdout mostrado no transcript)
- `2` - Erro bloqueante (stderr enviado para Claude)
- Outro - Erro nao-bloqueante

### Output para PreToolUse

```json
{
  "hookSpecificOutput": {
    "permissionDecision": "allow|deny|ask",
    "updatedInput": {"field": "modified_value"}
  },
  "systemMessage": "Explanation for Claude"
}
```

### IMPORTANTE: Hooks Carregam no Inicio da Sessao

Mudancas na configuracao de hooks requerem reiniciar o Claude Code.

---

## 8. MCP Servers

Localizacao: `.mcp.json` na raiz do plugin

### Formato

```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/servers/server.js"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### Tipos de MCP Server

| Tipo | Uso |
|------|-----|
| stdio | Local, subprocesso |
| http | REST endpoint |
| sse | Server-Sent Events (OAuth) |
| websocket | Real-time |

### Formato Alternativo

```json
{
  "server-name": {
    "type": "http",
    "url": "https://mcp.example.com/api"
  }
}
```

---

## 9. Arquivos de Configuracao Local

### known_marketplaces.json

Localizacao: `~/.claude/plugins/known_marketplaces.json`

```json
{
  "claude-plugins-official": {
    "source": {
      "source": "github",
      "repo": "anthropics/claude-plugins-official"
    },
    "installLocation": "/Users/user/.claude/plugins/marketplaces/claude-plugins-official",
    "lastUpdated": "2026-01-12T00:00:00.000Z"
  }
}
```

### Tipos de Source

**GitHub (usa SSH por padrao):**
```json
"source": {
  "source": "github",
  "repo": "user/repo"
}
```

**URL HTTPS (evita problemas de SSH):**
```json
"source": {
  "source": "url",
  "url": "https://github.com/user/repo.git"
}
```

### installed_plugins.json

Gerenciado automaticamente pelo Claude Code.

---

## 10. Processo de Instalacao

### Via Interface

```
/plugin > Discover > Selecionar plugin
```

### Via Comando

```
/plugin install plugin-name@marketplace-name
```

### Adicionar Marketplace

```
/plugin > Marketplaces > Add Marketplace
Inserir: user/repo
```

### Teste Local

```bash
# Testar com --plugin-dir
cc --plugin-dir /path/to/plugin

# Debug mode
claude --debug
```

---

## 11. Progressive Disclosure

Skills usam um sistema de carregamento de tres niveis para gerenciar contexto eficientemente:

### Niveis

1. **Metadata (name + description)** - Sempre no contexto (~100 palavras)
2. **SKILL.md body** - Quando skill e ativada (<5k palavras)
3. **Bundled resources** - Conforme necessario (Ilimitado*)

*Ilimitado porque scripts podem executar sem carregar na janela de contexto.

### O que vai no SKILL.md

**Incluir (sempre carregado quando skill ativa):**
- Conceitos core e overview
- Procedimentos e workflows essenciais
- Tabelas de referencia rapida
- Ponteiros para references/examples/scripts
- Casos de uso mais comuns

**Manter abaixo de 3,000 palavras, idealmente 1,500-2,000 palavras**

### O que vai em references/

**Mover para references/ (carregado conforme necessario):**
- Patterns detalhados e tecnicas avancadas
- Documentacao API comprehensiva
- Guias de migracao
- Edge cases e troubleshooting

---

## 12. Best Practices

### Organizacao

1. **Agrupamento logico**: Agrupar componentes relacionados
2. **Manifest minimo**: Manter `plugin.json` enxuto
3. **Documentacao**: Incluir README files

### Nomenclatura

1. **Consistencia**: Usar naming consistente entre componentes
2. **Clareza**: Usar nomes descritivos que indicam proposito
3. **Formato**: Usar kebab-case para tudo

### Portabilidade

1. **Sempre usar ${CLAUDE_PLUGIN_ROOT}**: Nunca hardcode paths
2. **Testar em multiplos sistemas**: Verificar em macOS, Linux, Windows
3. **Documentar dependencias**: Listar ferramentas e versoes necessarias
4. **Evitar features system-specific**: Usar construcoes bash/Python portaveis

### Seguranca em Hooks

1. **Validar todos inputs**: Nunca confiar em input do usuario
2. **Quotar todas variaveis**: `"$file_path"` nao `$file_path`
3. **Set timeouts apropriados**: Default: command (60s), prompt (30s)
4. **Checar path traversal**: Bloquear `..` em caminhos

### Documentacao

1. **README no plugin**: Proposito geral e uso
2. **README em diretorios**: Orientacao especifica
3. **Comentarios em scripts**: Uso e requisitos

---

## 13. Troubleshooting

### Comandos Sem Namespace

**Sintoma:** `/start` em vez de `/plugin:start`

**Causa:** Campo `name` no frontmatter do comando

**Solucao:** Remover `name:` de todos os comandos

### Permission denied (publickey)

**Sintoma:** Erro SSH ao instalar

**Causa:** `source: "github"` usa SSH

**Solucao:** Editar `known_marketplaces.json`:
```json
"source": {
  "source": "url",
  "url": "https://github.com/user/repo.git"
}
```

### Invalid schema

**Sintoma:** Erro de schema ao carregar marketplace

**Causa:** Formato incorreto ou arquivos extras

**Solucao:**
- Verificar `marketplace.json` segue padrao oficial
- Remover `plugin.json` da raiz do marketplace

### Plugin Nao Aparece

**Solucoes:**
1. Reiniciar Claude Code
2. Verificar `installed_plugins.json`
3. Verificar `.claude-plugin/plugin.json` existe no plugin
4. Verificar plugin esta em `plugins/<nome>/`

### Componente nao carregando

- Verificar arquivo esta no diretorio correto com extensao correta
- Checar sintaxe YAML frontmatter
- Garantir skill tem `SKILL.md` (nao `README.md`)
- Confirmar plugin esta habilitado nas settings

### Erros de resolucao de path

- Substituir todos hardcoded paths com `${CLAUDE_PLUGIN_ROOT}`
- Verificar paths sao relativos e comecam com `./` no manifest
- Testar com `echo $CLAUDE_PLUGIN_ROOT` em hook scripts

### Auto-discovery nao funcionando

- Confirmar diretorios estao na raiz do plugin (nao em `.claude-plugin/`)
- Checar file naming segue convencoes (kebab-case, extensoes corretas)
- Reiniciar Claude Code para recarregar configuracao

### Hooks nao executando

- Verificar `hooks/hooks.json` usa formato wrapper correto
- Checar scripts sao executaveis (`chmod +x`)
- Usar `claude --debug` para ver logs
- Lembrar: mudancas requerem reiniciar sessao

---

## 14. Checklist

### Marketplace (raiz do repositorio)

- [ ] `.claude-plugin/marketplace.json` existe
- [ ] `.claude-plugin/plugin.json` **NAO** existe
- [ ] `README.md` na raiz
- [ ] `LICENSE` na raiz
- [ ] Plugins em `plugins/` ou `external_plugins/`

### Cada Plugin

- [ ] Em `plugins/<nome>/`
- [ ] `.claude-plugin/plugin.json` existe (name, description, author)
- [ ] `README.md` no plugin
- [ ] Comandos **SEM** campo `name` no frontmatter
- [ ] Comandos **COM** campo `description`
- [ ] Skills com `name` e `description` no frontmatter (terceira pessoa)
- [ ] Agents com `name`, `description`, `model`, `color`
- [ ] Hooks usam formato wrapper `{"hooks": {...}}`

### Skills

- [ ] SKILL.md existe com frontmatter valido
- [ ] Description usa terceira pessoa ("This skill should be used when...")
- [ ] Description inclui trigger phrases especificas
- [ ] Body usa forma imperativa/infinitiva
- [ ] Body e enxuto (1,500-2,000 palavras)
- [ ] Conteudo detalhado em references/
- [ ] Recursos referenciados no SKILL.md

### Agents

- [ ] Identifier 3-50 chars, lowercase, hyphens
- [ ] Description inclui 2-4 <example> blocks
- [ ] Model especificado (inherit recomendado)
- [ ] Color especificada
- [ ] System prompt em segunda pessoa ("You are...")
- [ ] System prompt < 10,000 caracteres

### Hooks

- [ ] hooks.json usa formato wrapper correto
- [ ] Scripts usam ${CLAUDE_PLUGIN_ROOT}
- [ ] Scripts sao executaveis
- [ ] Inputs sao validados
- [ ] Variaveis sao quoted
- [ ] Timeouts apropriados definidos

### Teste

- [ ] Clone via HTTPS funciona
- [ ] Instalacao via `/plugin install` funciona
- [ ] Comandos aparecem com namespace correto (`/plugin:comando`)
- [ ] Skills ativam nos triggers esperados
- [ ] Agents sao invocados corretamente
- [ ] Hooks executam nos eventos corretos
- [ ] Reiniciar Claude Code e verificar

---

## Referencias Oficiais

- **Documentacao:** https://docs.claude.com/en/docs/claude-code/plugins
- **Documentacao Hooks:** https://docs.claude.com/en/docs/claude-code/hooks
- **Repositorio Oficial:** https://github.com/anthropics/claude-plugins-official
- **Plugin-Dev:** `/plugins/plugin-dev` no repositorio oficial
- **Example Plugin:** `/plugins/example-plugin` no repositorio oficial

---

## Workflow de Desenvolvimento Recomendado

```
┌─────────────────────────┐
│   Design Structure      │  → Definir componentes necessarios
│   (manifest, layout)    │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Create Plugin Base    │  → Criar diretorios e plugin.json
│   (directories)         │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Add Commands          │  → Comandos slash para usuarios
│   (user-facing)         │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Add Skills            │  → Conhecimento especializado
│   (domain knowledge)    │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Add Agents            │  → Tarefas autonomas complexas
│   (autonomous tasks)    │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Add Hooks             │  → Automacao event-driven
│   (event automation)    │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Integrate MCP         │  → Servicos externos
│   (external services)   │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Test & Validate       │  → claude --debug
│                         │     cc --plugin-dir
└──────────┬──────────────┘
           │
┌──────────▼──────────────┘
│   Document & Publish    │  → README, marketplace
└─────────────────────────┘
```

---

**Autor:** Murillo Dutt - Dutt Yeshua Technology Ltd
**Licenca:** MIT
