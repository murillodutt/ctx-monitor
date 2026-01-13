# Design System - ctx-monitor

This document defines the visual identity, tokens, and component specifications for the **ctx-monitor** (Context Oracle) ecosystem. All interface updates (Web Dashboard, CLI, Reports) must strictly adhere to these guidelines.

---

## Design Tokens

Design tokens are the visual atoms of our design system.

### Colors

#### Brand Colors

| Token | Value | Use Case |
| :--- | :--- | :--- |
| `--color-primary` | `#10B981` | Primary brand, success actions |
| `--color-primary-light` | `#D1FAE5` | Light backgrounds, badges |
| `--color-primary-dark` | `#059669` | Hover states, emphasis |
| `--color-secondary` | `#F59E0B` | Warning states, secondary accents |
| `--color-secondary-light` | `#FEF3C7` | Warning backgrounds |
| `--color-accent` | `#3B82F6` | Info states, links |
| `--color-accent-light` | `#DBEAFE` | Info backgrounds |

#### Semantic Colors

| Status | Primary | Light (BG) | Use Case |
| :--- | :--- | :--- | :--- |
| **Success** | `#10B981` | `#D1FAE5` | Completed actions, healthy status |
| **Warning** | `#F59E0B` | `#FEF3C7` | Alerts, attention needed |
| **Error** | `#EF4444` | `#FEE2E2` | Failures, critical issues |
| **Info** | `#3B82F6` | `#DBEAFE` | Informational messages |

#### Neutral Scale

| Token | Value | Use Case |
| :--- | :--- | :--- |
| `--color-neutral-50` | `#F8FAFC` | Light backgrounds |
| `--color-neutral-100` | `#F1F5F9` | Tertiary backgrounds |
| `--color-neutral-200` | `#E2E8F0` | Borders, dividers |
| `--color-neutral-300` | `#CBD5E1` | Strong borders |
| `--color-neutral-400` | `#94A3B8` | Muted text |
| `--color-neutral-500` | `#64748B` | Secondary text |
| `--color-neutral-600` | `#475569` | Body text |
| `--color-neutral-700` | `#334155` | Dark mode borders |
| `--color-neutral-800` | `#1E293B` | Primary text |
| `--color-neutral-900` | `#0F172A` | Darkest background |

#### Semantic Aliases

| Token | Light Mode | Dark Mode |
| :--- | :--- | :--- |
| `--color-surface` | `#FFFFFF` | `#141414` |
| `--color-bg` | `#F8FAFC` | `#1A1A1A` |
| `--color-border` | `#E2E8F0` | `#2D2D2D` |
| `--color-border-strong` | `#CBD5E1` | `#404040` |
| `--text-primary` | `#1E293B` | `#F5F5F5` |
| `--text-secondary` | `#64748B` | `#A3A3A3` |
| `--text-muted` | `#94A3B8` | `#737373` |
| `--bg-primary` | `#F8FAFC` | `#1A1A1A` |
| `--bg-secondary` | `#FFFFFF` | `#141414` |
| `--bg-tertiary` | `#F1F5F9` | `#262626` |

> **Note:** Dark mode uses pure neutral grays without blue tint for a cleaner aesthetic.

---

### Typography

#### Font Families

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', monospace;
```

#### Font Sizes

| Token | Value | Line Height | Use Case |
| :--- | :--- | :--- | :--- |
| `xs` | `0.625rem` (10px) | `1rem` | Labels, badges |
| `sm` | `0.75rem` (12px) | `1.25rem` | Secondary text, table cells |
| `base` | `0.875rem` (14px) | `1.5rem` | Body text |
| `lg` | `1rem` (16px) | `1.75rem` | Headings |
| `xl` | `1.25rem` (20px) | `1.75rem` | Card titles |
| `2xl` | `1.5rem` (24px) | `2rem` | Section headers |
| `3xl` | `2rem` (32px) | `2.25rem` | Page titles |

---

### Spacing & Layout

#### Spacing Scale

| Token | Value | Pixels |
| :--- | :--- | :--- |
| `1` | `0.25rem` | 4px |
| `2` | `0.5rem` | 8px |
| `3` | `0.75rem` | 12px |
| `4` | `1rem` | 16px |
| `5` | `1.25rem` | 20px |
| `6` | `1.5rem` | 24px |
| `8` | `2rem` | 32px |
| `10` | `2.5rem` | 40px |

#### Layout Constraints

| Token | Value | Description |
| :--- | :--- | :--- |
| `sidebar.collapsed` | `56px` | Sidebar collapsed width |
| `sidebar.expanded` | `240px` | Sidebar expanded width |
| `header.height` | `64px` | Fixed header height |
| `content.maxWidth` | `1440px` | Max content width |
| `card.padding` | `clamp(16px, 3vw, 24px)` | Responsive card padding |

---

### Effects

#### Shadows

```css
/* Light Mode */
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);

/* Dark Mode - Deeper shadows for contrast */
--shadow-sm: 0 1px 3px rgba(0,0,0,0.5);
--shadow-md: 0 4px 8px rgba(0,0,0,0.6);
--shadow-lg: 0 10px 20px rgba(0,0,0,0.7);
```

#### Border Radius

| Token | Value | Use Case |
| :--- | :--- | :--- |
| `--radius-sm` | `0.375rem` (6px) | Buttons, inputs |
| `--radius-md` | `0.5rem` (8px) | Cards, modals |
| `--radius-lg` | `0.75rem` (12px) | Large containers |
| `--radius-full` | `9999px` | Pills, avatars |

#### Transitions

```css
--transition-fast: 150ms ease;   /* Buttons, hovers */
--transition-normal: 200ms ease; /* Panels, toggles */
```

---

## Components Specification

### 1. Cards

Base container for dashboard modules.

```css
.card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    padding: clamp(16px, 3vw, 24px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
```

### 2. Buttons

#### Variants

| Variant | Background | Text | Border |
| :--- | :--- | :--- | :--- |
| **Primary** | `--color-primary` | `#FFFFFF` | none |
| **Secondary** | `#000000` | `#FFFFFF` | none |
| **Outline** | transparent | `--color-primary` | `--color-border` |
| **Ghost** | transparent | `--text-secondary` | none |

#### Icon Button (Copy)

```css
.copy-btn {
    padding: 4px;
    background: transparent;
    border: none;
    border-radius: 4px;
    color: var(--text-muted);
    cursor: pointer;
    width: 24px;
    height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.copy-btn:hover {
    background: var(--bg-tertiary);
    color: var(--accent-primary);
}

.copy-btn.copied {
    color: var(--success);
}

.copy-btn svg {
    width: 14px;
    height: 14px;
}
```

**Icons (SVG):**
- **Copy:** Clipboard icon with rectangle overlay
- **Copied:** Checkmark polyline

### 3. Badges (Pills)

```css
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
```

| Severity | Background | Text |
| :--- | :--- | :--- |
| **Critical** | `#FEE2E2` | `#DC2626` |
| **High** | `#FEF3C7` | `#D97706` |
| **Medium** | `#DBEAFE` | `#2563EB` |
| **Low** | `#F1F5F9` | `#64748B` |

### 4. Tables / Data Grids

```css
.data-grid {
    display: grid;
    font-family: var(--font-mono);
    font-size: 12px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    overflow: hidden;
}

.data-row {
    display: grid;
    gap: 8px;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-color);
}

.data-row:last-child {
    border-bottom: none;
}
```

### 5. Alerts Panel

#### Alert Item

```css
.alert-item {
    display: flex;
    gap: clamp(10px, 2vw, 14px);
    padding: clamp(12px, 2vw, 18px);
    border-bottom: 1px solid var(--border-color);
    transition: background 0.15s ease;
}

.alert-item:hover {
    background: var(--bg-tertiary);
}

.alert-item.expandable {
    cursor: pointer;
    flex-direction: column;
}
```

#### Alert Severity Indicator

```css
.alert-indicator {
    width: 10px;
    height: 10px;
    border-radius: var(--radius-full);
    flex-shrink: 0;
    margin-top: 4px;
}

/* Colors */
.alert-indicator.critical { background: #EF4444; }
.alert-indicator.high { background: #F59E0B; }
.alert-indicator.medium { background: #3B82F6; }
.alert-indicator.low { background: #94A3B8; }
```

#### Affected Events Grid

```css
.alert-events {
    background: var(--bg-tertiary);
    border-radius: 6px;
    overflow: hidden;
}

.alert-event {
    display: grid;
    grid-template-columns: 70px 90px 60px 1fr;
    gap: 8px;
    padding: 8px 12px;
    font-size: 12px;
    font-family: var(--font-mono);
    border-bottom: 1px solid var(--border-color);
}

.alert-event-time { color: var(--text-muted); }
.alert-event-type { color: var(--accent-primary); }
.alert-event-tool { color: var(--text-secondary); font-weight: 500; }
.alert-event-args {
    color: var(--text-muted);
    word-break: break-all;
    overflow-wrap: anywhere;
    line-height: 1.4;
}
```

#### Action Command Box

```css
.alert-action {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    font-size: 12px;
}

.alert-action code {
    font-family: var(--font-mono);
    background: var(--color-surface);
    padding: 4px 8px;
    border-radius: 4px;
    color: var(--accent-primary);
}
```

---

## Theming (Dark Mode)

Dark mode uses a **pure neutral gray palette** (no blue tint) for a cleaner, more professional appearance.

### Core Variables

```css
.dark {
    /* Core backgrounds - Pure neutral grays */
    --color-surface: #141414;
    --color-bg: #1A1A1A;
    --color-border: #2D2D2D;
    --color-border-strong: #404040;

    /* Text hierarchy - Warm whites */
    --text-primary: #F5F5F5;
    --text-secondary: #A3A3A3;
    --text-muted: #737373;

    /* Neutrals override */
    --color-neutral-50: #1A1A1A;
    --color-neutral-100: #262626;
    --color-neutral-200: #404040;
    --color-neutral-300: #525252;
    --color-neutral-400: #737373;

    /* Status badges - Semi-transparent */
    --success-light: rgba(16, 185, 129, 0.15);
    --warning-light: rgba(245, 158, 11, 0.15);
    --error-light: rgba(239, 68, 68, 0.15);
    --info-light: rgba(59, 130, 246, 0.15);

    /* Legacy mappings */
    --bg-primary: #1A1A1A;
    --bg-secondary: #141414;
    --bg-tertiary: #262626;
    --logo-shield: #F5F5F5;
}
```

### Component-Specific Overrides

```css
/* Header */
.dark .header {
    background: rgba(20, 20, 20, 0.95);
}

/* Navigation - Inverted active state */
.dark .nav-item.active {
    background: #FFFFFF;
    color: #000000;
}

/* Status badges - Brighter text */
.dark .status-ok { color: #34D399; }
.dark .status-warn { color: #FBBF24; }
.dark .status-alert { color: #F87171; }

/* Tables */
.dark .table th {
    background: var(--color-neutral-100);
}

/* Alerts */
.dark .alert-events {
    background: var(--color-bg);
    border: 1px solid var(--color-border);
}

/* Scrollbar */
.dark ::-webkit-scrollbar-track { background: var(--color-bg); }
.dark ::-webkit-scrollbar-thumb { background: var(--color-border-strong); }
```

---

## Data Limits

To prevent UI overflow and performance issues, data is truncated:

| Field | Max Length | Use Case |
| :--- | :--- | :--- |
| `args_preview` | 200 chars | Alert events, tool args |
| `result_preview` | 100 chars | Tool results |
| `error_message` | 100 chars | Error details |
| `prompt_preview` | 40 chars | Timeline events |
| `event_id` | 8 chars | Short ID display |
| `timestamp` | 7 chars | Time only (HH:MM:SS) |

---

## Interaction Patterns

### Expandable Alerts

1. Click alert header to expand/collapse
2. Chevron rotates 180deg on expand
3. Details fade in with 0.2s transition

### Copy to Clipboard

1. Click copy icon
2. Icon changes to checkmark
3. Reverts after 2 seconds
4. Tooltip shows "Copied!"

### Hover States

- Cards: `translateY(-2px)` + shadow increase
- Buttons: Background color change
- Table rows: Background highlight
- Links: Color shift to primary

---

## Responsive Breakpoints

| Breakpoint | Width | Adjustments |
| :--- | :--- | :--- |
| `sm` | `640px` | Stack cards vertically |
| `md` | `768px` | 2-column grid |
| `lg` | `1024px` | 3-column grid, sidebar visible |
| `xl` | `1280px` | Full layout |

---

## Logo Variants

| Variant | Shield Color | Pulse Color | Use Case |
| :--- | :--- | :--- | :--- |
| **Light Mode** | `--color-neutral-800` | `--color-primary` | Default |
| **Dark Mode** | `#F5F5F5` | `--color-primary` | Dark backgrounds |
| **Monochrome** | `#000000` | `#000000` | Print, B&W |

---

## Changelog

| Version | Date | Changes |
| :--- | :--- | :--- |
| 1.2.0 | 2026-01-12 | Rebuilt dark theme with pure neutral grays (no blue tint), added component-specific dark overrides |
| 1.1.0 | 2026-01-12 | Added Alerts components, Copy button icon, Data limits |
| 1.0.0 | 2026-01-10 | Initial design system |
