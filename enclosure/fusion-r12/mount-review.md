# Future-mount insert review

Mounting interface reviewed 2026-09-11 and rechecked with the corrected guides on 2026-09-14. The final geometry is a reasonable **controller-weight
mounting prototype**. It defines a custom M3 accessory pattern; no load rating
or compatibility with a mounting standard is established.

| Feature | Final dimensions |
|---|---|
| Four insert centers | X±36, Y±37 mm: 72 × 74 mm rectangle |
| Bosses | Ø10 mm; Z2.5…7.5, joined to floor, sidewall and closure columns by webs |
| Insert pilots | Ø4 mm, 5 mm deep, opening from inside at Z7.5 |
| External screw access | Ø3.4 mm through the 2.5 mm floor |
| Inserts | Ruthex RX-M3Sx4.0; flush inside, occupying Z3.5…7.5 |
| Insert quantity | Four additional; 16 total if all enclosure inserts are fitted |
| Recommended screw reach | 6.5–7.0 mm above the outside-bottom plane |

Ruthex specifies a 4 mm length, 4.6 mm maximum outside diameter, 4 mm pilot and
1.6 mm minimum surrounding wall for this insert. The Ø10 boss provides 2.7 mm
radial plastic around its maximum diameter. See the
[manufacturer's RX-series dimension sheet](https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf)
and [official short M3 product](https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck).

## Load path and installation

Screws entering from outside pull the inserts toward the floor. The initial
load is carried through the heat-set joint, boss and connecting webs. The
1 mm space beneath each seated insert means the floor shoulder is **secondary
capture only**: it does not bear directly on the correctly seated insert.
The Ø4-to-Ø3.4 step is 0.3 mm wide radially. Its geometric presence does not
establish a pull-out capacity.

Measure screw protrusion from the future mount's **case-contact surface**.
A 6.5–7.0 mm reach gives approximately 3.0–3.5 mm thread engagement and leaves
the tip 0.5–1.0 mm below the inside boss top. Select screw length only after
including the bracket and washer thicknesses. Check actual protrusion rather
than choosing a fixed screw length for an unspecified mount. Nothing projects
below the bare enclosure's existing bottom.

Install the inserts with the shell empty and top removed. The checked working
tool is Ø8 mm from just above Z7.5 through Z35. Nominal clearance is 0.5 mm to
the sidewall and about 0.720 mm to the nearest closure column. The front guides'
rear caps were lowered to Z7.5 locally, clearing the tool while preserving the
fascia runner stop. The new bosses clear the grown PCB envelope by 0.8 mm.

The **16 × 21 × 10 mm mount coupon** checks the local heat-set process, external
screw entry and engagement. It omits the full wall/closure-column height and
does not reproduce every front-guide feature. A successful coupon therefore
does not prove access for a larger iron barrel: the actual working nose must
match the checked envelope, with larger tool sections kept above it.

## Evidence and limits

- The frozen reference passes **31 grouped fit/assembly checks and 10 mesh
  checks**. All reference meshes are single, watertight solids.
- Native verification passes **131 component/case checks**, all four Ø3.2 mm
  screw-shaft paths and all four Ø8 mm tool paths, with no timeline issues.
- Four negative controls displacing the modeled inserts 1.5 mm outward are
  blocked by the floor. This demonstrates the secondary geometric stop, not
  retention force. See [native-verification.json](native-verification.json).
- All four native case meshes pass integrity and sampled comparison with the
  reference within the 0.03 mm allowance. Their current native, reference and
  print STL hashes match [mesh-verification.json](mesh-verification.json).

Reference SCAD SHA-256:
`37b97045a014de0b7f250b26c06991e2e7b8c5c206489d3bf380c2b89a6706ca`.
Reference report SHA-256:
`21d141b4c76710e13b368a6feb172652d491a5c18645a54c0cf407b677b61ab9`.
Native archive SHA-256:
`ca7851904af2cbe75ff7c9a623b59fd13645fee92741013a807a5e538b02906f`.

Actual printed insert retention, mounting torque, material creep and the future bracket's
load distribution remain physical checks. The intended scope is supporting
the controller itself.

## Guide correction — 2026-09-14

The guide profiles were corrected in CAD to provide continuous upper capture.
The four mounting inserts, screw reach and tool envelope remain unchanged, and
their clearance checks pass with the new guides. See [guide-review.md](guide-review.md).
