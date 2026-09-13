---
name: Municipal Sentinel Modern
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#444651'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#757682'
  outline-variant: '#c5c5d3'
  surface-tint: '#4059aa'
  primary: '#00236f'
  on-primary: '#ffffff'
  primary-container: '#1e3a8a'
  on-primary-container: '#90a8ff'
  inverse-primary: '#b6c4ff'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#222a3e'
  on-tertiary: '#ffffff'
  tertiary-container: '#384055'
  on-tertiary-container: '#a4acc5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b6c4ff'
  on-primary-fixed: '#00164e'
  on-primary-fixed-variant: '#264191'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
  headline-xl-mobile:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-md: 1.25rem
  gutter-lg: 1.5rem
  margin: 1rem
  margin-md: 1.5rem
  margin-lg: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system embodies the rigor, dependability, and modern clarity required for municipal infrastructure and smart-city operations. It bridges public-sector stewardship with mission-critical computational precision, projecting unshakeable reliability, continuous vigilance, and data-backed civic intelligence.

The visual style is **Corporate / Modern** layered with specialized command-and-control dashboard conventions:
- High data legibility with systematic scanning zones for operational dispatchers and civil engineers.
- Tactful balance of authoritative structural containment and airy, light-mode cognitive relief during long monitoring shifts.
- Precision accents signaling real-time telemetry, automated road inspection triggers, and infrastructure life-cycle status without sensory fatigue.

## Colors

The palette establishes an authoritative municipal foundation using deep maritime blues complemented by a calibrated status system for instant situational awareness:

- **Primary Canvas & Surfaces**: Crisp base backgrounds (`#F8FAFC`), elevated panel cards (`#FFFFFF`), and nested telemetry sub-wells (`#F1F5F9`).
- **Structural Borders**: Neutral architectural boundaries (`#E2E8F0`) with hover/focus states advancing to `#CBD5E1`.
- **Primary Navy Stack**: Command Primary (`#1E3A8A`), Interactive Active Blue (`#2563EB`), and Structural Baseline Deep Slate (`#0F172A`).
- **Text & Content Hierarchy**: High-contrast header/critical metric text (`#0F172A`), body narrative and labeling (`#334155`), with secondary metadata and units (`#64748B`).
- **Municipal Severity Spectrum**:
  - **Healthy / Resolved / Nominal**: Emerald (`#10B981`) paired with surface fill (`#ECFDF5`) and outline (`#A7F3D0`).
  - **Medium / Preventive / Warning**: Amber (`#F59E0B`) paired with surface fill (`#FFFBEB`) and outline (`#FDE68A`).
  - **High / Critical Hazard / Impassable**: Red (`#EF4444`) paired with surface fill (`#FEF2F2`) and outline (`#FECACA`).

## Typography

The type system brings clarity to rapid operational decision-making:

- **Display & Section Headers (`Space Grotesk`)**: Provides an engineered, modern infrastructure presence. Subtle geometric character adds distinctiveness to high-level system summaries and zone titles without sacrificing structural formality.
- **Body & Controls (`Inter`)**: Delivers maximum legibility across complex incident reports, multi-row telemetry tables, and configuration menus.
- **Technical Metrics & Telemetry (`JetBrains Mono`)**: Handles GPS coordinates, speed vectors, pavement degradation indices (PCI), sensor IDs, timestamps, and confidence percentages. Monospaced consistency ensures live values do not cause layout reflow or eye fatigue during frequent polling.

## Layout & Spacing

A 12-column fluid grid accommodates high-density operational telemetry alongside multi-tiered geospatial layouts:

- **Desktop (1440px+)**: 12 columns with 24px (`space-lg`) gutters and 32px (`space-xl`) canvas margins. Primary navigation is pinned to a 280px left rail with a persistent incident triage panel anchored on the right.
- **Tablet (768px - 1439px)**: 8 columns with 20px gutters and 24px canvas margins. Auxiliary telemetry modules collapse into accessible drawer tabs.
- **Mobile (Up to 767px)**: 4 columns with 16px (`gutter`) and 16px (`margin`). Field inspection views stack sequentially; maps maintain priority screen real estate with floating action sheets.

## Elevation & Depth

Visual hierarchy uses a refined combination of crisp surface containment, subtle ambient elevation, and selective tonal backing:

- **Base Layer (Level 0)**: Background `#F8FAFC`. Zero elevation, pure baseline.
- **Surface Panels (Level 1)**: Base cards `#FFFFFF` bounded by a 1px solid border of `#E2E8F0` and an ambient shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04)`.
- **Interactive Card Hover (Level 2)**: Border shifts to `#CBD5E1` with elevated depth: `0 4px 6px -1px rgba(15, 23, 42, 0.06), 0 2px 4px -2px rgba(15, 23, 42, 0.05)`.
- **Floating Controls & Tooltips (Level 3)**: Overlay controls (map controls, dropdowns) leverage: `0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04)`.
- **Emergency Modal & Overlays (Level 4)**: Command dialogs and severe alert popovers float with: `0 20px 25px -5px rgba(15, 23, 42, 0.12), 0 8px 10px -6px rgba(15, 23, 42, 0.08)`.
- **Recessed Telemetry Wells**: Inset cards housing live data use background `#F1F5F9` with an inner border `#E2E8F0` and no drop shadow to indicate static sensor ingest.

## Shapes

The design system employs **Level 2 (Rounded)** architecture to create an approachable civic tool while maintaining structural balance:

- **Standard Cards & Data Modules**: Utilize `rounded-xl` (1.5rem / 24px outer corner radius) to convey modern product craftsmanship. Internal child elements conform to `rounded-lg` (1rem / 16px) or `rounded-md` (0.5rem / 8px) to preserve nested geometric rhythm.
- **Controls, Input Fields, & Telemetry Chips**: Standardized at `rounded-md` (0.5rem / 8px) for buttons, text inputs, and table filters.
- **Status Badges & Indicators**: Fully circular or pill forms for real-time telemetry pills (`rounded-full`), preventing confusion between interactive action buttons and informational status tags.

## Components

### Buttons
- **Primary Action**: Solid `#1E3A8A` background, white text, 8px corner radius (`rounded-md`), medium font-weight. Hover triggers `#2563EB` transition. Active state shifts to `#0F172A`. Focus state shows a 2px ring of `#2563EB` offset by 2px white.
- **Secondary Action**: White surface with 1px border `#E2E8F0`, `#0F172A` text. Hover background `#F8FAFC` with border `#CBD5E1`.
- **Destructive/Emergency Action**: `#EF4444` background with crisp white text, reserved exclusively for critical dispatch triggers or road closure confirmations.

### Live Status Indicators & Badges
- **Pulsing Indicator**: An 8px solid dot enveloped in an automated expanding CSS radar pulse (`@keyframes pulse`). Healthy feeds use `#10B981` with an outer ring fading from `rgba(16, 185, 129, 0.6)` to `0`.
- **Severity Badges**: High-contrast labels wrapped in lightweight tinted pills:
  - Critical: Background `#FEF2F2`, border `#FECACA`, text `#B91C1C` (`JetBrains Mono`, 10px, uppercase).
  - Warning: Background `#FFFBEB`, border `#FDE68A`, text `#B45309`.
  - Nominal: Background `#ECFDF5`, border `#A7F3D0`, text `#047857`.

### Cards & Module Containers
- Built on `#FFFFFF` surfaces with `rounded-xl` corners and standard 1px `#E2E8F0` borders.
- Header bars feature an integrated top border divider (`#F1F5F9`), housing the module title in `Space Grotesk` (16px), live status pill, and auxiliary action icon.
- Dedicated interior telemetry wells use `#F1F5F9` padding with `JetBrains Mono` readouts.

### Tables & Data Lists
- Tabular figures rendered in alternating or border-separated rows (`#F8FAFC` hover state).
- Header row fixed in `#F8FAFC` background with tracking-wide uppercase labels in `JetBrains Mono` (`label-sm`).
- Numeric readouts and coordinates align right; status tags and roadway names align left.

### Inputs, Filters & Selectors
- Height pinned to 40px for desktop touch-and-click safety.
- `#FFFFFF` surface, `#E2E8F0` border, `#0F172A` input value, and `#94A3B8` placeholder.
- Focus displays an explicit blue outline (`#2563EB`) with a light glow (`rgba(37, 99, 235, 0.15)`).

### Specialized Domain Components
- **Road Degradation Index Card (PCI)**: Radial gauge or segmented linear health bar ranging from 0–100 with Emerald, Amber, and Red thresholds.
- **Incident Coordinate Well**: Monospaced chip with a copy-to-clipboard action and direct GIS mapping linkage.
- **Video / AI Inference Feed Container**: 16:9 viewport bounded by a 1px `#CBD5E1` edge, featuring an overlaid top-left live telemetry tag and bounding-box overlay markers for potholes, cracks, and debris.