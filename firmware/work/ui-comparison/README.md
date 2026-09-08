**Pit Claw screen comparison**

`screen-comparison.html` compares eight current/proposed landscape views using native 480×320 LVGL renders. The Screen selector changes both images together. In the conversation host, optional design controls switch the proposed navigation between orange fill and orange underline.

The "current" screens preserve the production UI before the approved changes. Proposed screens are standalone design prototypes in `render_comparison.cpp`; they use the same input values. The alarm scenario uses Meat 1 at its 203°F target. Proposed buttons demonstrate appearance, without controller callbacks. These are review snapshots; actual implemented screens and regeneration instructions are in [../ui-implementation/README.md](../ui-implementation/README.md).

The proposals cover brighter labels, larger flat buttons, consistent pressed styles in the prototype code, edit cues on cards, separated target columns, an alarm row, graph labels and a dashed target line, and setup navigation. The screenshots do not demonstrate fixes to production state/unit handling or alarms across every screen.

Validation: rendered all 24 PNGs with LVGL 9.5.0 using RGB565 output; inspected the proposed layouts; exercised all eight screen selections in the browser; checked layouts at 360, 736, and 1024 viewport widths and both host appearances. Images loaded at 480×320 with no horizontal overflow or observed JavaScript errors. The physical panel was not tested.

The comparison preserves native image size where space permits, places images side by side on wide surfaces, and stacks them on narrower surfaces.

The HTML embeds its PNGs for a self-contained review snapshot. The prototype renderer references the pre-change widget structure and is retained as design evidence; use `test/ui/run_checks.py` to render the implemented firmware UI.
