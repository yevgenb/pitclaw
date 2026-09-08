# Visual aesthetics review — 8 September 2026

The main inconsistency was the navigation's explicit zero-radius override. Its
joined orange/black rectangles looked like a different component family from the
rounded cards, settings choices, and editor actions. The bar also touched the
bottom of the screen, leaving its lower corners visually undefined.

Reviewed the production 480×320 RGB565 captures of Home, Settings, editors,
graphs, alarms, and setup. The existing large readings, dark surfaces, short
labels, and orange action emphasis already provide a useful hierarchy.

| Area | Applied refinement |
| --- | --- |
| Shape | Shared 12-pixel radius for cards, buttons, settings surfaces, and alerts. Larger dialogs use a related 16-pixel radius. Removed the square navigation override. |
| Navigation | Three separate rounded controls with eight-pixel gaps and outer side margins. Neutral fills make every destination visible; orange and an underline identify selection. |
| Bottom spacing | Navigation is 52 pixels high at y=264, leaving four pixels below it so all four corners are visible. |
| Proportion | Both dashboard columns are 228 pixels wide with an eight-pixel gutter. Fahrenheit and Celsius choices are both 88 pixels wide. |
| Hierarchy and states | Primary actions use orange with dark text, secondary actions use neutral fills, and destructive actions use dark red. Shared normal, pressed, checked, and disabled styles retain the same shape. |
| Typography | Retained 36–48-pixel main readings and 16–18-pixel control labels. The reduced navigation width still fits icons and labels without wrapping. |

The shape settings live in `src/display/ui_styles.h`, so future controls inherit
the same appearance. Full-screen backgrounds, chart axes, and QR codes retain
their functional rectangular geometry.

Material 3 defines a theme through color, typography, and a customizable shape
scale. It also uses surface tones to distinguish hierarchy in dark interfaces.
This supports a shared visual system; it does not require every component to have
identical corners. The 12/16-pixel choices here are a design judgment for this
panel, not Android dp values or a conformance claim.
[Material 3 theming](https://developer.android.com/develop/ui/compose/designsystems/material3)

Current Material 3 Expressive also offers varied shapes and motion. For this
temperature controller, a consistent rounded family, legible values, and clear
selected/pressed states are the relevant choices. The U.S. Web Design System
likewise recommends distinctive primary actions, visible interaction states, and
short sentence-case button labels.
[Material 3](https://m3.material.io/),
[USWDS button guidance](https://designsystem.digital.gov/components/button/)

| View | Before | Updated |
| --- | --- | --- |
| Home | [Before](before/dashboard.png) | [Updated](../ui-implementation/screens/dashboard.png) |
| Settings | [Before](before/settings.png) | [Updated](../ui-implementation/screens/settings.png) |
| Pit editor | [Before](before/pit-editor.png) | [Updated](../ui-implementation/screens/pit-editor.png) |
| Alarm | [Before](before/alarm.png) | [Updated](../ui-implementation/screens/alarm.png) |

The native LVGL checks exercise actual pointer presses/releases at tab bounds,
including visually rounded corners, and rapid navigation. The existing editor,
unit, alarm, graph, scrolling, and setup checks also run against these production
widgets. Screenshots validate the rendered geometry; panel glare and physical
finger accuracy remain device checks.
