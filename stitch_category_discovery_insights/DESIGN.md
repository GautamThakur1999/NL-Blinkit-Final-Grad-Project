---
name: Category Discovery Insights
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1b1b1c'
  on-surface-variant: '#4e4634'
  inverse-surface: '#303030'
  inverse-on-surface: '#f3f0ef'
  outline: '#7f7662'
  outline-variant: '#d1c5ae'
  surface-tint: '#755b00'
  primary: '#755b00'
  on-primary: '#ffffff'
  primary-container: '#f8cb46'
  on-primary-container: '#6e5600'
  inverse-primary: '#edc13d'
  secondary: '#006e16'
  on-secondary: '#ffffff'
  secondary-container: '#8ffb87'
  on-secondary-container: '#007518'
  tertiary: '#00687b'
  on-tertiary: '#ffffff'
  tertiary-container: '#64e0ff'
  on-tertiary-container: '#006274'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffe08f'
  primary-fixed-dim: '#edc13d'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#584400'
  secondary-fixed: '#8ffb87'
  secondary-fixed-dim: '#74dd6e'
  on-secondary-fixed: '#002203'
  on-secondary-fixed-variant: '#00530e'
  tertiary-fixed: '#aeecff'
  tertiary-fixed-dim: '#58d6f5'
  on-tertiary-fixed: '#001f26'
  on-tertiary-fixed-variant: '#004e5d'
  background: '#fcf9f8'
  on-background: '#1b1b1c'
  surface-variant: '#e5e2e1'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-tabular:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-margin: 24px
  gutter: 16px
  sidebar-width: 260px
  card-padding: 20px
  stack-gap: 12px
---

## Brand & Style
The design system is engineered for high-velocity decision-making in the quick-commerce sector. It balances the urgency of retail with the precision of data science. The aesthetic is **Corporate Modern** with a focus on functional clarity and high information density.

The interface prioritizes scanability, using a light neutral foundation to let colorful status indicators and data visualizations command attention. By utilizing generous whitespace and a "cards-on-canvas" approach, the design system ensures that complex metric sets feel approachable and organized rather than overwhelming.

## Colors
The palette is rooted in the functional requirements of a dashboard. 
- **Primary Accent (#F8CB46):** Used for interactive elements like primary buttons and active states. It provides high visibility against white surfaces without the fatigue associated with harsher tones.
- **Success (#0C831F):** Used for positive growth indicators, "In Stock" statuses, and completed targets.
- **Neutral / Text (#1F1F1F):** Provides high-contrast legibility for data points and labels.
- **Surface & Background:** A distinct separation between the canvas (#F4F5F7) and the content containers (#FFFFFF) creates a clear mental model for grouped information.

## Typography
Inter is the foundation of this design system, chosen for its exceptional legibility in data-heavy environments. 
- **Numerical Data:** For tables and metric cards, always enable tabular lining (`tnum`) to ensure numbers align vertically for easier comparison.
- **Hierarchy:** Use `label-caps` for secondary metadata and table headers to distinguish them from actionable data.
- **Scaling:** On mobile devices, `display-lg` should scale down to 24px to maintain readability within smaller card widths.

## Layout & Spacing
The design system utilizes a **Fixed Sidebar / Fluid Content** model. 
- **Sidebar:** A persistent 260px left navigation allows for deep categorization of tools.
- **The Grid:** A 12-column responsive grid on the main canvas. Cards typically span 3 columns for "Hero Metrics," 6 columns for "Trend Charts," and 12 columns for "Deep Dive Tables."
- **Rhythm:** An 8px base unit drives all spacing. Standard internal card padding is 20px (2.5 units) to provide a premium, airy feel even when data density is high.

## Elevation & Depth
This design system uses **Tonal Layers** combined with **Ambient Shadows** to create a structured hierarchy.
- **Level 0 (Canvas):** The #F4F5F7 background serves as the lowest point of the UI.
- **Level 1 (Cards):** White surfaces (#FFFFFF) with a soft, diffused shadow (0px 4px 12px rgba(0,0,0,0.05)). This provides enough lift to separate content from the background without creating visual clutter.
- **Level 2 (Overlays):** Modals and dropdown menus use a more pronounced shadow (0px 12px 24px rgba(0,0,0,0.1)) to indicate temporary interaction priority.

## Shapes
The shape language is defined by **Rounded XL (1.5rem / 24px)** corners for primary content containers. This approachable geometry softens the technical nature of the analytics data. Smaller interactive elements like buttons and input fields follow a standard 8px (0.5rem) radius to maintain a professional, crisp appearance.

## Components
- **Buttons:** Primary buttons use the #F8CB46 fill with #1F1F1F text for maximum contrast. Secondary buttons use a subtle grey stroke with no fill.
- **Metric Cards:** Should feature a `title-sm` label, a `display-lg` metric, and a `body-sm` sparkline or percentage change indicator in #0C831F.
- **Data Tables:** Clean, borderless rows with 1px #E2E8F0 bottom dividers. Use `data-tabular` for all numeric values. Hover states should use a subtle #F9FAFB background tint.
- **Status Chips:** Small, high-radius (pill) badges. Use low-opacity fills of the status color (e.g., 10% Green) with full-opacity text for an accessible, modern "tag" look.
- **Input Fields:** Minimalist design with a 1px #D1D5DB border that thickens and changes to #F8CB46 on focus.
- **Sidebar Items:** High-contrast active states using a vertical 4px bar of #F8CB46 on the left edge of the active menu item.