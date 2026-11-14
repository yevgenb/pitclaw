# Pit Claw prototype: builder's guide

Start here for the independently maintained
[yevgenb/Pit Claw fork](https://github.com/yevgenb/pitclaw), based on
[MrMatt57's original project](https://github.com/MrMatt57/pitclaw).
This preview is intended for experienced electronics and 3D-printing builders.
It is still undergoing physical qualification.

## Choose a starting point

| Goal | Start here |
| --- | --- |
| See what changed | [Build story](build-story.md) and [fork overview](../README.md#what-this-fork-changes) |
| Try the interfaces without hardware | [Desktop simulator](../README.md#development-and-validation) |
| Review or build the electronics | [Carrier PCB](../hardware/carrier-revb/README.md), [BOM](../hardware/carrier-revb/bom/README.md) and [wiring](wiring.md) |
| Print the current case | [Fusion r13 print and assembly guide](../enclosure/fusion-r13/README.md) |
| Install firmware | [Build and flash](../README.md#2-build-and-flash) or the OTA steps below |

## Download a matching snapshot

The [14 November 2026 prototype release](https://github.com/yevgenb/pitclaw/releases/tag/prototype-2026-11-14)
combines firmware **0.2.0-wifi-log.1**, web UI **6**, the **Fusion r13** enclosure
and the **Rev B-T2F0-A5807-S4** carrier BOM.
The release tag identifies the whole project snapshot; the device reports the
firmware version, not the date-based release tag.

Use the dependency versions in the tagged `firmware/platformio.ini`. The preview
pins Espressif32 **7.1.2**, LVGL **9.5.0** and its other direct firmware libraries
to the tested versions. Espressif32 8.x selects a newer Arduino core whose LEDC
API is incompatible with this firmware; upgrading the toolchain is a separate
firmware migration, not an installation step.

- `firmware.bin`: application and embedded web UI for the WT32-SC01 Plus.
- `pitclaw-enclosure-r13.zip`: Fusion/STEP sources, five complete printable parts,
  coupons, shims, assembly illustrations and recorded geometry checks.
- `pitclaw-carrier-digikey-bom.xlsx` and `pitclaw-carrier-digikey-import.csv`:
  carrier purchasing aids. They are not a complete device shopping list; read
  the [BOM exclusions](../hardware/carrier-revb/bom/README.md#not-included-in-the-subtotal)
  and refresh stock/prices before ordering.
- `BUILD-GUIDE.md`: links to the instructions at the exact source commit.
- `release-manifest.json` and `SHA256SUMS`: source revision, versions and asset
  integrity checks. Source-code archives are also available on the release page.

On macOS, check downloaded assets with `shasum -a 256 -c SHA256SUMS` from the
directory containing all release assets. On Linux, use `sha256sum -c SHA256SUMS`.

Maintainers can reproduce the asset collection from a clean checkout after
building/testing firmware with `python3 scripts/package_prototype.py /tmp/pitclaw-preview`
(use a new output directory). The manual **Prototype release** GitHub Actions
workflow builds, tests and publishes a prerelease; ordinary pushes run CI only.
Update the build story and guide for each new preview before running that workflow.

## Assemble and bring up the hardware

1. Review the carrier's power and connector requirements before purchasing.
   Use protected/current-limited 12 V sources rated no more than 3 A. This
   carrier has no onboard or branch-selective overcurrent protection. Its
   blower/servo RJ45 carries power and is **not an Ethernet port**.
2. Follow the [wiring guide](wiring.md) and the
   [carrier assembly notes](../hardware/carrier-revb/README.md). Check supply
   voltage, polarity, module orientation and harness continuity before connecting
   the display or actuators. Remove JP1 before powering the WT32 through its
   programming USB port.
3. Print the enclosure coupons first, then follow the r13 guide's orientation,
   insert, screw and display-shim instructions. The supplied shim procedure
   accommodates the reported display gap; do not force the glass into position
   with the retainer screws.
4. Flash and complete the touchscreen setup. Check each probe and calibrate it,
   then verify the fan, servo endpoints and buzzer with the actual hardware.
5. Conduct a supervised temperature-control test and record the result before
   relying on the build for a cook. Check cable routing and enclosure temperature
   in the intended mounting position.

The included blower adapter is for a UDS pipe intake. A K24/Kamado intake adapter
and a controller-to-grill mount are not included in this preview.

## Install or update firmware

**First installation:** use the [PlatformIO USB instructions](../README.md#2-build-and-flash)
at the release tag. A bare ESP32 needs its bootloader and partition table as
well as the application; do not treat the standalone `firmware.bin` as a full
flash image. The carrier's external USB-C PD connector is for power, not programming.

**Existing compatible installation:** finish the cook, download any retained
session CSV, open `http://bbq.local/update` (or the controller's IP), authenticate
if enabled, and upload `firmware.bin`. The device restarts. Check Settings for
`0.2.0-wifi-log.1` and web UI build `6`, then set the desired pit/meat targets.
The pit defaults to 225°F on restart and meat targets clear; web logins also end.

The binary embeds the web interface. Firmware OTA preserves saved configuration,
history and Wi-Fi logs. **Do not run `uploadfs` for this update**: it replaces
the LittleFS contents. Automatic release updates are disabled in this build.

## Useful feedback

Open a [build report](https://github.com/yevgenb/pitclaw/issues/new?template=build_report.yml)
with the release/firmware version, board revision, display module, grill, probes,
blower/servo and print material/settings. Include measured results rather than
only saying it works: display fit, temperatures versus a reference, warm-up and
overshoot, lid recovery and behavior after a restart.

For connectivity trouble, download Settings → Diagnostics → Download Wi-Fi log
after reconnecting. Review all logs and screenshots before posting; omit passwords,
tokens and personal network details. Report defects in
[this fork's issue tracker](https://github.com/yevgenb/pitclaw/issues).

Software checks and CAD geometry checks do not establish probe accuracy,
thermal behavior, printed strength or weather resistance. The latest cold-start,
display-fit and carrier load/thermal checks remain open. The
[project license is unresolved](../README.md#license); this release grants no new
rights to inherited code or assets.
