---
name: ui
description: "Skill for the Ui area of cuttingboard. 22 symbols across 1 files."
---

# Ui

22 symbols | 1 files | Cohesion: 100%

## When to Use

- Working with code in `ui/`
- Understanding how safeGet, display, derivePosture work
- Modifying ui-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `ui/app.js` | safeGet, display, derivePosture, showStatus, showContract (+17) |

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `safeGet` | Function | `ui/app.js` | 68 |
| `display` | Function | `ui/app.js` | 77 |
| `derivePosture` | Function | `ui/app.js` | 86 |
| `showStatus` | Function | `ui/app.js` | 98 |
| `showContract` | Function | `ui/app.js` | 106 |
| `setText` | Function | `ui/app.js` | 111 |
| `renderSignalBar` | Function | `ui/app.js` | 119 |
| `renderPrimaryTrade` | Function | `ui/app.js` | 139 |
| `renderNoTrade` | Function | `ui/app.js` | 162 |
| `renderWatchlist` | Function | `ui/app.js` | 187 |
| `renderSecondarySetups` | Function | `ui/app.js` | 206 |
| `renderCorrelation` | Function | `ui/app.js` | 233 |
| `renderRejections` | Function | `ui/app.js` | 253 |
| `renderHeader` | Function | `ui/app.js` | 278 |
| `renderRouter` | Function | `ui/app.js` | 289 |
| `renderContract` | Function | `ui/app.js` | 304 |
| `loadJSON` | Function | `ui/app.js` | 321 |
| `autoFetch` | Function | `ui/app.js` | 336 |
| `currentThemeId` | Function | `ui/app.js` | 14 |
| `applyTheme` | Function | `ui/app.js` | 18 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `AutoFetch → SafeGet` | intra_community | 5 |
| `AutoFetch → DerivePosture` | intra_community | 5 |
| `AutoFetch → Display` | intra_community | 5 |
| `AutoFetch → ShowStatus` | intra_community | 3 |

## How to Explore

1. `gitnexus_context({name: "safeGet"})` — see callers and callees
2. `gitnexus_query({query: "ui"})` — find related execution flows
3. Read key files listed above for implementation details
