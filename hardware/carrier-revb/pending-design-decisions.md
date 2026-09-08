# Pending design decisions — Rev B-T2F0-A5807-S4

## Decisions implemented

- U2 is a Traco Power TSR 2-2450N fixed 5 V / 2 A SIP-3 converter.
- F1, F2, F3 and F4 are deleted. All four former protected branches are direct.
- JP1 stays as removable WT32 USB/carrier power isolation.
- Q3, R7 and R19 are deleted; GPIO14 drives BZ1 through R6 = 330 ohm.
- The ADS1115 uses the WT32 DEBUG 3.3 V rail; no 3.3 V LDO is fitted.
- MOD1 is the Adafruit 5807 HUSB238 breakout, directly mounted through H5/H6.
- J9 is the Tensility 54-00133 barrel inlet. Its sleeve switch (pins 2–3) is
  unused; pin 1 feeds WALL_12V. K1 automatically selects wall power when its coil
  is energized, and PD otherwise. D3 suppresses the relay coil. JP2 is removed.
- D1, C5, C7, C13, R17 and R18 are deleted; the ADC module must provide local
  bypassing and SDA/SCL pull-ups to VDD.
- Q1 is IRF5305PBF, D2 is SB140, BZ1 is TDK PS1240P02BT, and R10-R12 are common
  10 k, 1% parts requiring per-channel calibration.

## Assumption attached to fuse removal

Only use protected/current-limited regulated 12 V sources rated no more than
3 A. Configure and verify MOD1 for a 12 V / 3 A request; use only a regulated
5.5 × 2.1 mm center-positive wall adapter at J9. K1 selects one positive input
at a time. The carrier intentionally provides no
branch-selective overcurrent protection. The TSR 2-2450N's internal protection
primarily protects the converter and does not establish safe current limits for
the MG90S, blower, RJ45 cable/contact or PCB traces.

## Still blocking routing/fabrication

1. Measure WT32 plus MG90S startup and loaded current on 5 V, including voltage
   droop and converter temperature in the intended enclosure.
2. Identify the exact blower current and verify Q1, D2, RJ45 contacts and shared
   return at startup and PWM operation.
3. Fit-check U2, RJ45, J9 and all three 2.5 mm jacks from real samples. Verify
   J9 pins 2–3 are continuous only with no barrel plug inserted. Pin 3 remains
   unconnected on the carrier; check K1 NC/NO continuity and both source states
   before powering loads. Verify source transfer/restart, coil release, contact
   inrush and brownout with the actual adapter and loads.
4. Confirm the owned ADS1115 pitch, edge offsets, insertion height, pull-ups and
   insulating support.
5. Fit-test the 5807 with M2 hardware, 3 mm spacers, rear support and actual USB
   cable; verify screw, nut, connector and WT32 clearances.
6. Confirm WT32 antenna location and freeze enclosure openings before routing.
7. Complete the WT32 display/touch driver integration described in
   `docs/hardware-review.md`; temperature conversion and provisional blower defaults
   are corrected, but embedded display/touch operation remains unverified.

This file records prototype decisions, not a safety certification.
