# Rev B-T2F0-A5807-S4 assembly parts

DigiKey selection checked 2026-09-05/06; see bom/ for priced purchasing lists.
Engineering draft, not fabrication approval.
U2 is the soldered TSR 2-2450N converter; J8 sockets the owned ADC module.
MOD1 is the screw-mounted Adafruit 5807 breakout and connects to J1 by a short
20-22 AWG power pair. J9 is the switched 5.5 x 2.1 mm, center-positive 12 V
barrel inlet. K1 automatically selects wall power when its raw 12 V coil is
energized; otherwise its normally closed contact selects USB PD. The SPDT
contacts select only one positive input at a time; grounds remain common.
J9 pin 3 is unused because its switch closes to sleeve/GND. D3 protects the
relay coil: banded cathode to WALL_12V, anode to GND. A source change can restart
the controller; verify switching and supply brownout behavior on the assembly.

| Ref | Value | Manufacturer part number | Footprint | Assembly |
|---|---|---|---|---|
| J1 | PD module output / 12V ONLY | B2B-XH-A | Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical | THT |
| J9 | 54-00133 / 12V CENTER + | 54-00133 | PitClaw:Tensility_54-00133_Horizontal | THT |
| K1 | G5Q-1 DC12 / WALL PRIORITY | G5Q-1 DC12 | PitClaw:Omron_G5Q1_SPDT_MaxBody | THT |
| D3 | SB140 / COIL FLYBACK | SB140 | Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal | THT |
| C1 | 470u / 35V | 35PX470MEFC10X12.5 | Capacitor_THT:CP_Radial_D10.0mm_P5.00mm | THT |
| C2 | 100n / 50V | FG28X7R1H104KNT06 | PitClaw:C_TDK_FG28X7R1H104KNT06_P5 | THT |
| U2 | TSR 2-2450N / 5V 2A | TSR 2-2450N | PitClaw:TRACO_TSR_2N_SIP3 | THT |
| C3 | 470u / 16V | 16ZLH470MEFC8X11.5 | Capacitor_THT:CP_Radial_D8.0mm_P3.50mm | THT |
| C4 | 100n / 50V | FG28X7R1H104KNT06 | PitClaw:C_TDK_FG28X7R1H104KNT06_P5 | THT |
| JP1 | REMOVE FOR WT32 USB | 68000-102HLF | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical | THT |
| Q1 | IRF5305PBF | IRF5305PBF | PitClaw:IRF5305_TO220_Horizontal_TabDown | THT |
| R1 | 1k / 0.25W | MFR-25FBF52-1K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| Q2 | 2N3904 | 2N3904BU | Package_TO_SOT_THT:TO-92_Inline_Wide | THT |
| R2 | 2.2k | MFR-25FBF52-2K2 | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| R3 | 100k | MFR-25FBF52-100K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| D2 | SB140 | SB140 | Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal | THT |
| R4 | 220R | MFR-25FBF52-220R | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| R5 | 10k | MFR-25FBF52-10K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| J2 | RJHSE-5080 / CHECK FOOTPRINT | RJHSE5080 | PitClaw:RJHSE-5080_DRAFT | THT |
| J3 | WT32 EXT harness | B8B-XH-A | Connector_JST:JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical | THT |
| J7 | WT32 DEBUG 2 / 7 ONLY | B2B-XH-A | Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical | THT |
| BZ1 | PS1240P02BT / PIEZO | PS1240P02BT | PitClaw:Piezo_TDK_PS1240P02BT_D12.2_P5 | THT |
| R6 | 330R / PIEZO SERIES | MFR-25FBF52-330R | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| J4 | MJ1-2503A / PIT | MJ1-2503A | PitClaw:MJ1-2503A | THT |
| R10 | 10k / 1% | MFR-25FBF52-10K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| R13 | 1k | MFR-25FBF52-1K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| C10 | 100n / 50V | FG28X7R1H104KNT06 | PitClaw:C_TDK_FG28X7R1H104KNT06_P5 | THT |
| J5 | MJ1-2503A / MEAT 1 | MJ1-2503A | PitClaw:MJ1-2503A | THT |
| R11 | 10k / 1% | MFR-25FBF52-10K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| R14 | 1k | MFR-25FBF52-1K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| C11 | 100n / 50V | FG28X7R1H104KNT06 | PitClaw:C_TDK_FG28X7R1H104KNT06_P5 | THT |
| J6 | MJ1-2503A / MEAT 2 | MJ1-2503A | PitClaw:MJ1-2503A | THT |
| R12 | 10k / 1% | MFR-25FBF52-10K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| R15 | 1k | MFR-25FBF52-1K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |
| C12 | 100n / 50V | FG28X7R1H104KNT06 | PitClaw:C_TDK_FG28X7R1H104KNT06_P5 | THT |
| J8 | ADS1115 BLUE / 1x10 SOCKET | PPPC101LFBN-RC | PitClaw:ADS1115_Blue_1x10_DRAFT | THT |
| R16 | 1k | MFR-25FBF52-1K | Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal | THT |

K1 uses the exact SPDT G5Q-1 DC12: pins 1/5 coil, 2 COM, 3 NO, 4 NC.
Reserve 16.2mm seated height, including its 0.4mm molded feet. Wall input
powers pin 1 and NO; pin 5 is GND, NC is PD_12V, COM is +12V.

Q1 mounts flat with the live drain tab downward. Form the leads before soldering;
use a 6mm body-to-pad-row distance, bend only beyond the widened 4.06mm lead
section, and use an inner bend radius of at least 0.8mm. Clamp/support the leads
between the bend and package; do not bend against the plastic body. Reserve
6.5mm seated height including a 1mm insulating under-body support. Cure small
electrically insulating, electronics-compatible adhesive support/side fillets
against a 1mm temporary spacing jig before soldering to retain Q1 for transport.
Remove the jig after curing. Do not install a tab bolt. Fit-check the lead form,
minimum under-body gap, adhesion and thermal behavior with the actual part.

Also required: WT32; owned blue 10-pin ADS1115; Adafruit 5807 MOD1; ADC
free-edge insulating support; insulating adhesive for Q1; 2x M2x10 provisional screws, 2x 3mm nylon spacers,
4x M2 washers (5mm maximum OD) and 2x M2 nuts under the carrier; one adhesive insulating rear
module support; harness mates, contacts, wire and one shunt for JP1; 4 M3 carrier screws into heat-set inserts in the bottom shell; WT32 mounts
separately inside the top bezel using an internal retainer and four small screws
matched to the WT32 rear blind bosses (diameter, thread and length require
sample verification). Enclosure closure uses separate M3 screws/inserts.
Confirm the owned ADC module has local bypassing and suitable SDA/SCL pull-ups
to VDD before assembly. Use only protected/current-limited regulated 12 V input
sources rated no more than 3 A; this revision has no onboard fuses. See
bom/README.md for assembly cautions.
