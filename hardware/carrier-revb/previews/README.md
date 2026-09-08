# Current carrier previews

- `pitclaw-carrier-schematic.pdf`: printable vector schematic.
- `pitclaw-carrier-schematic.png`: full schematic overview.
- `schematic-power-inputs.png`, `schematic-regulator.png`,
  `schematic-actuators.png`, `schematic-probes-adc.png`: enlarged sections.
- `schematic/pitclaw-carrier.svg`: native KiCad schematic drawing.
- `routed/carrier-front-copper.svg` and `carrier-back-copper.svg`: actual filled
  copper layers, with PNG versions alongside. The back is mirrored as viewed
  from the solder side.
- `routed/carrier-assembly.svg`: component placement and references.
- `routed/traces/`: routing views with ground fills hidden for readability.
  The ground planes are present in the PCB and in the filled-copper plots.

The editable `.kicad_sch`, `.kicad_pcb` and `.kicad_pro` one directory above
are authoritative. Native verification and its limits are in `../verification`.
`pitclaw-carrier.svg` is a compatibility copy of the current schematic.
