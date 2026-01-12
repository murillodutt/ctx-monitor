# Identidade Visual e Branding

Este documento estabelece as diretrizes para a identidade visual do **ctx-monitor** (Context Oracle), garantindo consistência em todas as comunicações, documentações e interfaces do plugin.

## 1. Conceito Central

O design baseia-se no conceito de **Escudo de Auditoria**. Ele une a solidez da conformidade (compliance) com o dinamismo do monitoramento em tempo real.

- **Escudo**: Representa proteção, integridade dos dados e a natureza auditável do sistema.
- **Linha de Pulso**: Simboliza o rastro de eventos (traces) e o monitoramento contínuo da execução (heartbeat).

## 2. Paleta de Cores

| Cor | Hex | Uso Recomendado |
| :--- | :--- | :--- |
| **Deep Slate** | `#2C3E50` | Símbolos principais, textos e elementos de fundo (Dark Mode). |
| **Audit Blue** | `#3498DB` | Destaques, linhas de pulso e ícones de status ativo. |
| **White** | `#FFFFFF` | Fundos (Light Mode) e ícones negativos. |
| **Light Gray** | `#F4F7F6` | Fundos de interface e áreas de contraste suave. |

## 3. Ativos da Logo (SVG)

### 3.1. Símbolo Principal (Linear Bicolor)

```xml
<svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- Shield Outline -->
    <path d="M50 12L88 28V55C88 77.5 50 88 50 88C50 88 12 77.5 12 55V28L50 12Z" stroke="#2C3E50" stroke-width="5" stroke-linejoin="round"/>
    <!-- Pulse Line -->
    <path d="M28 50H41L47 38L53 62L59 50H72" stroke="#3498DB" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

### 3.2. Versão Dark Mode

```xml
<svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M50 12L88 28V55C88 77.5 50 88 50 88C50 88 12 77.5 12 55V28L50 12Z" stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round"/>
    <path d="M28 50H41L47 38L53 62L59 50H72" stroke="#3498DB" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

### 3.3. Versão Adaptativa (Auto Light/Dark)

Esta versão utiliza consultas de mídia (media queries) internas para ajustar as cores automaticamente com base na preferência de tema do sistema do usuário.

```xml
<svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style>
        .shield { stroke: #2C3E50; }
        .pulse { stroke: #3498DB; }
        @media (prefers-color-scheme: dark) {
            .shield { stroke: #FFFFFF; }
        }
    </style>
    <!-- Shield Outline -->
    <path class="shield" d="M50 12L88 28V55C88 77.5 50 88 50 88C50 88 12 77.5 12 55V28L50 12Z" stroke-width="5" stroke-linejoin="round"/>
    <!-- Pulse Line -->
    <path class="pulse" d="M28 50H41L47 38L53 62L59 50H72" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

## 4. Tipografia

Para garantir uma estética técnica e profissional:

- **Interface/Documentação**: [Inter](https://rsms.me/inter/) (Sans-serif geométrica).
- **Código/CLI**: [JetBrains Mono](https://www.jetbrains.com/lp/mono/) ou Roboto Mono.

## 5. Aplicação no Logotipo

O logotipo oficial combina o símbolo com o nome do projeto em tipografia **Sans-serif Bold**.

**Formato**: `[Símbolo] ctx-monitor`

- O termo **ctx** deve estar em Deep Slate.
- O termo **monitor** pode ser destacado em Audit Blue para reforçar a funcionalidade.

## 6. Diretrizes de Uso

1. **Espaçamento**: Manter uma margem de segurança igual a 20% da largura total do símbolo em torno da logo.
2. **Proibição**: Não alterar as proporções do escudo ou a espessura relativa das linhas.
3. **Legibilidade**: Em tamanhos inferiores a 32px, utilizar apenas o símbolo (glyph) sem o texto.
