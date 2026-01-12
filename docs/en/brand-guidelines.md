# Visual Identity and Branding

This document establishes the guidelines for the visual identity of **ctx-monitor** (Context Oracle), ensuring consistency across all communications, documentations, and plugin interfaces.

## 1. Core Concept

The design is based on the **Audit Shield** concept. It combines the solidity of compliance with the dynamism of real-time monitoring.

- **Shield**: Represents protection, data integrity, and the auditable nature of the system.
- **Pulse Line**: Symbolizes the event traces and the continuous monitoring of execution (heartbeat).

## 2. Color Palette

| Color | Hex | Recommended Use |
| :--- | :--- | :--- |
| **Deep Slate** | `#2C3E50` | Main symbols, text, and background elements (Dark Mode). |
| **Audit Blue** | `#3498DB` | Highlights, pulse lines, and active status icons. |
| **White** | `#FFFFFF` | Backgrounds (Light Mode) and negative icons. |
| **Light Gray** | `#F4F7F6` | Interface backgrounds and soft contrast areas. |

## 3. Logo Assets (SVG)

### 3.1. Main Symbol (Linear Bicolor)

```xml
<svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- Shield Outline -->
    <path d="M50 12L88 28V55C88 77.5 50 88 50 88C50 88 12 77.5 12 55V28L50 12Z" stroke="#2C3E50" stroke-width="5" stroke-linejoin="round"/>
    <!-- Pulse Line -->
    <path d="M28 50H41L47 38L53 62L59 50H72" stroke="#3498DB" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

### 3.2. Dark Mode Version

```xml
<svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M50 12L88 28V55C88 77.5 50 88 50 88C50 88 12 77.5 12 55V28L50 12Z" stroke="#FFFFFF" stroke-width="5" stroke-linejoin="round"/>
    <path d="M28 50H41L47 38L53 62L59 50H72" stroke="#3498DB" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

### 3.3. Adaptive Version (Auto Light/Dark)

This version uses internal media queries to automatically adjust colors based on the user's system theme preference.

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

## 4. Typography

To ensure a technical and professional aesthetic:

- **Interface/Documentation**: [Inter](https://rsms.me/inter/) (Geometric Sans-serif).
- **Code/CLI**: [JetBrains Mono](https://www.jetbrains.com/lp/mono/) or Roboto Mono.

## 5. Logotype Application

The official logo combines the symbol with the project name in **Sans-serif Bold** typography.

**Format**: `[Symbol] ctx-monitor`

- The term **ctx** should be in Deep Slate.
- The term **monitor** can be highlighted in Audit Blue to reinforce functionality.

## 6. Usage Guidelines

1. **Spacing**: Maintain a safety margin equal to 20% of the symbol's total width around the logo.
2. **Prohibition**: Do not alter the proportions of the shield or the relative thickness of the lines.
3. **Readability**: For sizes smaller than 32px, use only the symbol (glyph) without the text.
