---
name: Blinkit Discover
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
  tertiary: '#5d5f5f'
  on-tertiary: '#ffffff'
  tertiary-container: '#d0d0d0'
  on-tertiary-container: '#575959'
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
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c7'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#454747'
  background: '#fcf9f8'
  on-background: '#1b1b1c'
  surface-variant: '#e5e2e1'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  container-max: 1280px
  gutter: 20px
---

## Brand & Style

The design system is built on the premise of "Instant Clarity." It translates the urgency of quick-commerce into a frictionless, cheerful interface that feels both dependable and surprisingly intelligent. The personality is helpful and energetic—moving at the speed of thought without overwhelming the user.

The aesthetic follows a **Corporate Modern** approach with **Minimalist** influences. It prioritizes high-speed scanning through significant whitespace, clear information hierarchy, and a vibrant, high-contrast color palette. AI-driven discovery elements are integrated through soft tonal shifts rather than intrusive overlays, ensuring the "discovery" aspect feels like a natural extension of the shopping experience.

## Colors

The palette is designed for high visibility and instant brand recognition. 

*   **Primary (Blinkit Yellow):** Used for key brand moments, top navigation accents, and highlighting search or "Blink" discovery features.
*   **Action (Blinkit Green):** Reserved exclusively for "Add to Cart" and primary conversion paths to build strong muscle memory.
*   **Neutral (Near-black Ink):** Used for high-legibility typography and iconography.
*   **Surface:** The background remains a cool, clean grey (#F8F8F8) to allow white product cards to "pop" and define the layout structure.

## Typography

This design system utilizes **Inter** across all levels to maintain a systematic, utilitarian, and modern feel. 

Headlines use heavy weights (Bold/ExtraBold) and tighter letter spacing to create a sense of urgency and impact. Body text prioritizes legibility with generous line heights. Small labels and price tags use semi-bold weights to ensure they remain clear even at small scales.

## Layout & Spacing

The layout follows a **Fluid Grid** philosophy optimized for desktop density.

*   **Desktop:** A 12-column grid with a maximum container width of 1280px. Gutters are fixed at 20px to maintain a compact, "packed shelf" feel.
*   **Spacing Rhythm:** All spacing tokens are multiples of 4px. Use `lg` (24px) for padding within product cards and `2xl` (48px) for vertical section margins.
*   **Discovery Reflow:** AI discovery sidebars or "nudges" should occupy a fixed 320px width on large screens or collapse into a top-scrollable tray on smaller viewports.

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Ambient Shadows**.

*   **Level 0 (Background):** #F8F8F8.
*   **Level 1 (Cards/Containers):** Pure White (#FFFFFF) with a very soft, diffused shadow (0px 4px 12px rgba(0,0,0,0.05)).
*   **Level 2 (Hover/Active):** Slightly lifted shadow (0px 8px 24px rgba(0,0,0,0.08)) to indicate interactivity.
*   **AI Discovery Elements:** Use a subtle primary-tinted glow (Yellow #F8CB46 at 5% opacity) as a background fill to differentiate suggested items from standard search results.

## Shapes

The shape language is friendly and approachable, utilizing a **Rounded** strategy. 

Standard components (buttons, input fields) use a 0.5rem (8px) radius. Product cards and large containers use `rounded-lg` (16px) to create a soft, modern "tray" look. Selection indicators and promotional chips use `rounded-xl` (24px) or full pill shapes to stand out as distinct, clickable objects.

## Components

*   **Product Cards:** White background, 16px corner radius, subtle shadow. Images should be centered with a 1:1 aspect ratio. Price is displayed in `body-lg` bold, with a secondary-colored "Add" button in the bottom right.
*   **Buttons:** 
    *   *Primary Add:* Solid Green (#0C831F), white text, 8px radius.
    *   *Ghost:* Transparent background, Near-black border, for secondary actions like "View Similar."
*   **AI Discovery Chips:** Small, pill-shaped tags with a light yellow background (#F8CB46 at 20%) and dark text, used to categorize AI suggestions (e.g., "Goes well with...").
*   **Search Bar:** Large, centered, with 12px radius. Uses a subtle yellow focus ring to reinforce brand identity.
*   **Lists:** High-density vertical stacks for cart views, using 1px #EEEEEE borders for separation instead of shadows.
*   **Discovery Nudge:** A specialized component with a soft yellow gradient border and an icon of a "sparkle" to indicate an AI-suggested product discovery.