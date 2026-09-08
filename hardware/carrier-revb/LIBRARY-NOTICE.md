# KiCad library provenance

Standard device/transistor/power symbols in `PitClaw.kicad_sym` were extracted
from the installed KiCad 9.0.6 libraries. Inherited symbols were resolved and
project library identifiers were applied. Standard footprints embedded in the
PCB come from the installed KiCad footprint libraries; reference/annotation
placement was adjusted for this carrier. The RJ45 contact array began as an
adaptation of the related KiCad Amphenol RJHSE-5380 footprint. Its current
RJHSE5080 pin numbering, staggered contact locations, mounting pegs and body
offset were independently reconciled with Amphenol's
[P-RJHSE-X080 Rev A manufacturer drawing](https://cdn.amphenol-cs.com/media/wysiwyg/files/drawing/rjhsex080.pdf).
The drawing explicitly includes the RJHSE-5080 variant; this does not assert
interchangeability with a different RJ45 part or replace a first-article fit check.

Copyright: KiCad library contributors. The upstream library material is
licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode),
with KiCad's electronic-design exception. See the complete
[KiCad library license and exception](https://www.kicad.org/libraries/license/)
and [upstream license document](https://gitlab.com/kicad/libraries/kicad-symbols/-/blob/master/LICENSE.md).
The corresponding adapted library material retains that license. No license
change is asserted for the user's other project files.

Sources: [KiCad symbols](https://gitlab.com/kicad/libraries/kicad-symbols),
[KiCad footprints](https://gitlab.com/kicad/libraries/kicad-footprints).
Project-specific connector geometry was transcribed from the sources identified
in README and remains subject to the stated engineering validation gates.
