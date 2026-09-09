# Implemented landscape UI

These 480×320 RGB565 captures render the production LVGL widgets with fixture
data. They show the approved styling applied to the firmware, including the
orange-filled selected navigation, larger controls, separated temperature/target
columns, and brighter secondary text. Cards and buttons share a 12-pixel corner
radius; dialogs use 16 pixels. The navigation has separate 52-pixel-high rounded
buttons, eight-pixel gaps and side margins, and four pixels below it. Dashboard
columns and the two unit choices have equal widths. See the
[aesthetics review](../ui-aesthetics-review/review.md) for the rationale and before images.

The subtle-polish refinement adds neutral fan/damper labels, sentence-case card
titles, aligned edit icons, and a line-chart navigation icon. Smaller raised
degree symbols follow the live temperature text through digit-width changes,
Fahrenheit/Celsius switches, and compact alarm layouts; disconnected readings
show dashes without a degree symbol. Selected navigation keeps its orange fill.

| View | Render |
| --- | --- |
| Home | [Dashboard](screens/dashboard.png) |
| Editors | [Pit at 500°F](screens/pit-editor.png), [Meat 2](screens/meat-editor.png), [Celsius](screens/celsius-editor.png) |
| History | [Graph](screens/graph.png), [Graph with alarm](screens/graph-alarm.png) |
| Alerts | [Home alarm](screens/alarm.png), [Editor with alarm](screens/editor-alarm.png), [Probe errors](screens/probe-errors.png) |
| Settings | [Controls](screens/settings.png), [Scrolled lower section](screens/settings-more.png), [Confirmation](screens/confirmation.png) |
| Setup | [Units](screens/wizard-units.png), [Wi-Fi](screens/wizard-wifi.png), [Probes](screens/wizard-probes.png), [Test running](screens/wizard-test-running.png), [Test feedback](screens/wizard-hardware.png) |

Editors copy each committed value when opened. Cancel discards changes, taps
adjust by one displayed degree, and holding adjusts by five. Display units now
convert at the UI boundary while control, alarms, and stored history consistently
use Fahrenheit. The graph labels show actual elapsed sample time through history
condensing, and the target line is dashed.

Active alerts share a reserved area on Home, Graph, and Settings. An open editor
moves the alert above the dialog and leaves Silence accessible. The existing
alarm manager's acknowledgment behavior is preserved: acknowledgment clears its
active alarm list; independent probe faults, lid state, and fire warnings continue
to follow their source state.

Regenerate the PNGs using the instructions in [test/ui/README.md](../../test/ui/README.md).
The original visual proposal remains in [ui-comparison](../ui-comparison/README.md).

Validation on 8 September 2026: firmware and simulator builds, 132 native test
cases, the splash/navigation check, and the production UI interaction check.
The interaction check also exercises changing digit widths, negative/zero Celsius
readings, disconnected and reconnected probes, and degree-symbol placement while
alarms appear and clear.
Captures were inspected for layout. Physical touch, glare, and device rendering
latency still require a check on the panel.
