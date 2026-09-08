# Relay-free power input review

Reviewed 2026-09-06 against the S4 electrical design and r6 enclosure.
**Final decision: retain K1 and D3.** USB-PD connects to the normally closed
contact, wall power to normally open, and raw wall voltage powers the coil.
The user selected the relay after comparing blower-voltage loss, price and
assembly complexity. The schematic and routed PCB implement this choice.

The alternatives below are retained as comparison records. No diode ORing or
power-mux substitution is applied.

## Price and assembly comparison

DigiKey US prices checked 2026-09-06, quantities sufficient for one controller.
These are selector-circuit costs only; connectors, PD module, shared bulk
capacitor, PCB fabrication, assembly, shipping, tax and tariffs are excluded.
Small-passive budgets are estimates, not a completed purchasing selection.

| Option | Selector parts cost, USD | Complexity | Voltage drop at 1 A total input current |
|---|---:|---|---|
| Dual Schottky STPS10L40CT | $1.28 | One three-pin through-hole package; check flat mounting and heat | About 0.35–0.45 V; planning estimate |
| Existing G5Q-1 relay + SB140 | $2.03 | Two through-hole parts; straightforward assembly, bulky relay | Up to 0.10 V from initial specified contact resistance |
| Two separate SB540A diodes | $2.84 | Two axial through-hole parts; low height | About 0.3–0.5 V; planning estimate |
| TPS2121 + basic passives | About $3–$4 | Six-part basic circuit; tiny QFN requires suitable surface-mount assembly | 0.056 V typical, 0.070 V maximum at 25 °C |

The dual package saves $0.75 against the current relay circuit. Two separate
Vishay diodes are more expensive at the current single-board quantity. A
TPS2121 circuit adds roughly $1–$2 in components over the relay; its assembly
method is the larger practical difference.

Price sources: [ST dual diode](https://www.digikey.com/en/products/detail/stmicroelectronics/STPS10L40CT/1039594),
[G5Q-1 relay, $1.80](https://www.digikey.com/en/products/detail/aratas-america-llc/G5Q-1-DC12/355239),
[SB140, $0.23](https://www.digikey.com/en/products/detail/smc-diode-solutions/SB140/6022959),
[SB540A, $1.42 each](https://www.digikey.com/en/products/detail/vishay-general-semiconductor-diodes-division/SB540A-E3-54/2146218),
and [TPS2121RUXR, $2.44](https://www.digikey.com/en/products/detail/texas-instruments/TPS2121RUXR/9859001).

The [ST dual diode](https://www.st.com/resource/en/datasheet/stps10l40c.pdf)
contains two 5 A paths sharing a cathode. Only one diode drop is in the selected
path. Using its DC loss model gives about 0.36 W at 1 A and 1.22 W at 3 A;
temperature, mounting and actual waveforms still matter. Its exposed tab is
the common cathode, so a flat mount needs electrical clearance or insulation.

The [relay specification](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf)
gives 100 mΩ maximum initial contact resistance. The table therefore uses a
maximum, not an invented typical value. Its 0.4 W coil loss is additional while
wall-powered; the coil is off on USB-only power.

The [TPS2121 datasheet](https://www.ti.com/lit/ds/symlink/tps2121.pdf) specifies
56 mΩ typical resistance: at 3 A, calculate 0.168 V drop and 0.504 W conduction
loss. Its 2 × 2.5 mm, 12-pad QFN needs reflow/hot-air or factory assembly.
The basic automatic circuit needs the IC, one current-limit resistor, three
local bypass capacitors and one soft-start capacitor. The $0.50–$1.50 passive
allowance produces the rounded $3–$4 budget. Wall-priority sensing adds two
resistors. Layout, input hotplug behavior and current-limit tolerance need
checking before this becomes an implemented design.

For the existing through-hole build, the relay remains a reasonable low-drop
choice. To remove the relay and retain nearly all blower voltage, TPS2121 is
the preferred candidate if surface-mount assembly is acceptable. The dual
diode is the simplest inexpensive choice when the voltage drop is acceptable.

## Diode option connections

| Connection | Proposed wiring |
|---|---|
| USB-PD | J1 pin 1 / PD_12V → first diode anode |
| Wall adapter | J9 pin 1 / WALL_12V → second diode anode |
| Main supply | Both banded cathodes → existing +12V load rail |
| Returns | Both input grounds remain connected to GND |
| Jack switch | J9 pin 3 stays unused |

Each diode must carry the entire input load by itself. The existing 1 A SB140
coil diode is not the proposed power diode. The dual STPS10L40CT above is the
lower-cost candidate; the previously researched separate part is Vishay
[SB540A](https://www.vishay.com/docs/88903/sb520a.pdf), a through-hole 5 A / 40 V
Schottky in DO-201AD. Its current rating depends on lead temperature and
mounting. Final purchasing choice and placement need a thermal check.

| Inputs | Expected normal behavior |
|---|---|
| USB only | USB supplies the load through its diode |
| Wall only | Wall supplies the load through its diode |
| Both | The higher effective voltage normally supplies most of the load; closely matched inputs may share |
| One powered, the other connected but unpowered | The other diode blocks substantial reverse feed into that input |

This is conventional [diode ORing, described by TI in section 3](https://www.ti.com/lit/an/slvae57b/slvae57b.pdf).
It does not guarantee wall priority. Connecting two adapters does not force
twice the normal current into the device: the load determines demand.

## Tradeoffs and rebuttal

Two independent reviews challenged source selection and searched for a jack
that could replace the relay mechanically. The earlier conclusion that possible
combined fault current required a relay was too restrictive for this prototype.

- **Keep source isolation.** Directly joining the positive inputs could feed a
  powered supply into a connected but unpowered adapter. Rare simultaneous use
  does not remove that case. Schottky diodes still have reverse leakage; they
  are not galvanic isolation.
- **Account for diode loss.** For the candidate, allow roughly 0.3–0.5 V drop
  over relevant operating currents. At an assumed 0.4 V and 1 A, dissipation is
  0.4 W; at 0.5 V and 3 A it is 1.5 W in the conducting diode. These are planning
  estimates, not measured temperatures. The regulated 5 V converter has ample
  input-voltage margin; check blower startup at the reduced supply voltage and
  diode temperature inside the enclosure.
- **Preserve the existing no-fuse prototype choice explicitly.** Diodes block
  reverse feed but do not limit total fault current. Two connected sources can
  both contribute to a short, so 3 A per adapter is not a 3 A system ceiling.
  A common fuse can be added after measuring startup/load current if that
  additional protection is wanted. Its time-current behavior must be matched
  to the wiring; it would not be an instantaneous 3 A clamp.
- **The jack switch still does not select positive power.** The current
  [Tensility drawing](https://tensility.s3.us-west-2.amazonaws.com/imports/product_spec_sheets/54-00133.pdf)
  switches the sleeve. Targeted alternatives from
  [Same Sky](https://www.sameskydevices.com/product/resource/pj-002ah.pdf),
  [Cliff](https://www.cliffuk.co.uk/products/dcconnectors/DualDCSockets.pdf) and
  [Switchcraft](https://www.switchcraft.com/assets/1/24/PC721A_CD_.pdf?6698=)
  also switch the sleeve. This was a targeted search, not proof that no suitable
  center-switched jack exists anywhere.

A low-loss power-mux IC addresses the blower-voltage concern with a modest
parts-cost increase, provided surface-mount assembly is acceptable. Separate
ideal-diode controllers and MOSFETs require at least two controller ICs and two
FETs; the controllers alone cost more than TPS2121, so that approach offers no
clear simplicity advantage here. Removing the relay does not itself justify
reducing case height: other component and display envelopes remain.

Before applying either proposal, finalize the selected option's parts and update
the schematic, PCB generator, source-state checks and BOM together. Then check
each source alone, both together, an unpowered connected adapter, cable hotplug,
blower startup and enclosed component temperature. No physical testing was
performed for this review.
