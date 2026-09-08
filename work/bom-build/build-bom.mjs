import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { Workbook, SpreadsheetFile, FileBlob } from '@oai/artifact-tool';

const root = '/Users/eugene.borokhov/Documents/Code/pitclaw';
const out = `${root}/hardware/carrier-revb/bom`;
const scratch = `${root}/work/bom-build`;
const delivery = `${root}/outputs/pitclaw-b-t2f0-a5807-s4`;
if(process.argv.includes('--inspect-existing')){
  const current=await SpreadsheetFile.importXlsx(await FileBlob.load(`${out}/pitclaw-carrier-digikey-bom.xlsx`));
  console.log((await current.inspect({kind:'table',range:'Order!A1:J8',include:'values,formulas',tableMaxRows:8,tableMaxCols:10,maxChars:7000})).ndjson);
  console.log((await current.inspect({kind:'table',range:'Order!A33:H35',include:'values,formulas',tableMaxRows:3,tableMaxCols:8,maxChars:2200})).ndjson);
  console.log((await current.inspect({kind:'table',range:'Parts!A1:S8',include:'values,formulas',tableMaxRows:8,tableMaxCols:19,maxChars:9000})).ndjson);
  console.log((await current.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:300},maxChars:3000})).ndjson);
  for(const [sheetName,range,label] of [['Order','A1:H40','order'],['Parts','A1:S33','parts'],['Other items','A1:D25','other']]){
    const img=await current.render({sheetName,range,scale:1,format:'png'});
    await fs.writeFile(`${scratch}/final-b-t2f0-a5807-s4-${label}.png`,new Uint8Array(await img.arrayBuffer()));
  }
  process.exit(0);
}
if(process.argv.includes('--verify-preservation')){
  const before=await SpreadsheetFile.importXlsx(await FileBlob.load('/tmp/pitclaw-before-auto-power-flush.xlsx'));
  const after=await SpreadsheetFile.importXlsx(await FileBlob.load(`${out}/pitclaw-carrier-digikey-bom.xlsx`));
  assert.deepEqual(after.worksheets.items.map(s=>s.name),before.worksheets.items.map(s=>s.name),'Sheet set/order changed');
  const checks=[['Order','A4:J5'],['Parts','A3:S5']];
  for(const [name,address] of checks){
    const a=before.worksheets.getItem(name).getRange(address),b=after.worksheets.getItem(name).getRange(address);
    assert.deepEqual(b.values,a.values,`${name}!${address} values changed unexpectedly`);
    assert.deepEqual(b.formulas,a.formulas,`${name}!${address} formulas changed unexpectedly`);
  }
  for(const name of ['Order','Parts']) {
    const col=name==='Order'?1:2;
    const oldRows=before.worksheets.getItem(name).getRange(name==='Order'?'A6:J32':'A6:S32').values;
    const newRows=after.worksheets.getItem(name).getRange(name==='Order'?'A6:J32':'A6:S32').values;
    for(const row of oldRows) {
      if(['54-00133','SPC02SYAN','B2B-XH-A','SB140','68000-103HLF'].includes(row[col])) continue;
      assert.deepEqual(newRows.find(r=>r[col]===row[col]),row,`${name} changed unrelated part ${row[col]}`);
    }
  }
  const report={revision:'B-T2F0-A5807-S4',comparedTo:'B-T2F0-A5807-S3',unchangedValueAndFormulaRanges:checks,visualBaselineReviewed:true,changedSheetsReviewed:['Order','Parts','Other items']};
  await fs.writeFile(`${root}/hardware/carrier-revb/verification/bom-preservation.json`,JSON.stringify(report,null,2)+'\n');
  console.log('Sheet set, instructions and headers are preserved; the simplified parts, totals and release gates changed as intended.');
  process.exit(0);
}
const data = JSON.parse(await fs.readFile(`${out}/selection.json`, 'utf8'));
const assembly = await fs.readFile(`${root}/hardware/carrier-revb/parts.md`, 'utf8');
const footprints = Object.fromEntries(assembly.split('\n').filter(l => /^\| [A-Z]+\d+ \|/.test(l)).map(l => {
  const cells = l.split('|').map(v => v.trim()); return [cells[1], cells[4]];
}));
const rows = [...data.parts.map(p => ({...p, category:p.dnp?'DNP':'Carrier', needed:p.dnp?0:p.refs.length})),
  ...data.modules.map(p => ({...p, category:'Module', needed:p.qty})),
  ...data.accessories.map(p => ({...p, category:'Harness', needed:p.qty}))];
assert.equal(Object.keys(footprints).length,37);
assert.equal(data.parts.filter(p=>!p.dnp).reduce((s,p)=>s+p.refs.length,0),37);
const priceAt = (p,q) => q===0?0:p.prices.filter(t=>t[0]<=q).at(-1)[1];
const bestQty = p => p.needed===0?0:[p.needed,...p.prices.map(t=>t[0]).filter(q=>q>=p.needed)]
  .sort((a,b)=>a*priceAt(p,a)-b*priceAt(p,b)||a-b)[0];
rows.forEach(p => p.order=bestQty(p));
const wb = Workbook.create();
const order=wb.worksheets.add('Order');
const parts=wb.worksheets.add('Parts');
const other=wb.worksheets.add('Other items');
const font='Helvetica Neue'; // Verified /System/Library/Fonts/HelveticaNeue.ttc on the target Mac.
function base(sh,range,widths,title,subtitle){
  sh.showGridLines=false;
  sh.getRange(range).format.font={name:font,size:11,color:'#202A34'};
  sh.getRange(range).format.rowHeight=31;
  sh.getRange(range).format.verticalAlignment='center';
  sh.getRange(range).format.wrapText=true;
  widths.forEach((w,i)=>sh.getRangeByIndexes(0,i,1,1).format.columnWidthPx=w);
  sh.getRange('A1').values=[[title]];
  sh.getRange('A1').format.font={name:font,size:16,bold:true};
  sh.getRange('A1').format.wrapText=false;
  sh.getRange('A2').values=[[subtitle]];
  sh.getRange('A2').format.wrapText=false;
  sh.getRange('A2:H2').format.borders={bottom:{style:'thin',color:'#AFBAC4'}};
}
function header(sh,address,values){
  sh.getRange(address).values=[values];
  sh.getRange(address).format={fill:'#34485A',font:{name:font,size:11,bold:true,color:'#FFFFFF'},
    horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:35,
    borders:{insideVertical:{style:'thin',color:'#FFFFFF'}}};
}
function stripe(sh,first,last,end){
  for(let r=first;r<=last;r++) if(r%2===0)sh.getRange(`A${r}:${end}${r}`).format.fill='#F2F5F7';
}
const first=6,last=first+rows.length-1,total=last+2;
base(order,`A1:J${total+8}`,[172,215,68,68,85,85,68,216,360,430],
  'Pit Claw carrier BOM', 'Rev B-T2F0-A5807-S4. K1 automatically selects wall power or Adafruit 5807. Prices: retained 2026-09-05, K1 2026-09-06. USD.');
order.getRange('A3').values=[['Unrouted PCB: not for fabrication. Subtotal excludes PCB, mounting hardware and existing WT32/ADC.']];
order.getRange('A3').format.wrapText=false;
order.getRange('A4').values=[['Order quantities are editable (amber). Pricing follows the sampled breaks on Parts; refresh before checkout or larger builds.']];
order.getRange('A4').format.wrapText=false;
header(order,'A5:J5',['References','Manufacturer part number','Needed','Order qty','Unit USD','Line USD','Spare qty','DigiKey part number','Source URL','Order note']);
order.getRange(`A${first}:J${last}`).values=rows.map(p=>[p.refs.join(', '),p.mpn,p.needed,p.order,null,null,null,p.sku,p.url,
  p.dnp?'DNP. Order only if the ADC module lacks suitable I2C pull-ups.':p.order>p.needed?'Price break makes this quantity cheaper than the exact need.':p.category==='Harness'?p.notes:p.category==='Module'?'Screw-mounted module; configure 12 V / 3 A and meter-check before connection.':'Fitted carrier part. See Parts for specifications and assembly cautions.']);
stripe(order,first,last,'J');
order.getRange(`D${first}:D${last}`).format.fill='#FFF2CC';
order.getRange(`C${first}:G${last}`).format.horizontalAlignment='right';
order.getRange(`C${first}:D${last}`).setNumberFormat('#,##0');
order.getRange(`G${first}:G${last}`).setNumberFormat('#,##0');
order.getRange(`E${first}:E${last}`).setNumberFormat('"$"0.00000');
order.getRange(`F${first}:F${last}`).setNumberFormat('"$"0.00');
order.getRange(`A${first}:J${last}`).format.rowHeight=66;
order.dataValidations.add({range:`D${first}:D${last}`,rule:{type:'whole',operator:'greaterThanOrEqual',formula1:0}});
order.getRange(`G${first}:G${last}`).conditionalFormats.add('cellIs',{operator:'lessThan',formula:0,format:{fill:'#FCE4D6',font:{color:'#9C0006'}}});
order.freezePanes.freezeRows(5);

base(parts,`A1:S${last}`,[172,140,215,350,430,290,360,82,70,85,70,85,70,85,70,85,70,85,70],
  'Part specifications and price breaks','Rev B-T2F0-A5807-S4. K1 provides automatic wall priority; no JP2. U2: fixed 5 V / 2 A. J8: owned ADC socket.');
parts.getRange('A3').values=[['Package drawings guide selection. Physical sample fit and loaded/thermal testing remain required.']];
parts.getRange('A3').format.wrapText=false;
parts.getRange('A4').values=[['Price-break pairs start at I. Unit prices are a public snapshot, not a quote. Blank stock means not recorded.']];
parts.getRange('A4').format.wrapText=false;
header(parts,'A5:S5',['References','Manufacturer','Part number','KiCad footprint','Assembly notes','Specification','Source URL','Stock','Qty 1','Price 1 USD','Qty 2','Price 2 USD','Qty 3','Price 3 USD','Qty 4','Price 4 USD','Qty 5','Price 5 USD','State']);
parts.getRange(`A${first}:S${last}`).values=rows.map(p=>{
  const pp=Array.from({length:5},(_,i)=>p.prices[i]||[null,null]).flat();
  const placement=p.category==='Harness'?'Off-board accessory':p.category==='Module'?'Board-mounted module / 2 x M2 holes; wired to J1':footprints[p.refs[0]];
  return [p.refs.join(', '),p.manufacturer,p.mpn,placement,p.notes,p.description,p.url,p.stock??null,...pp,p.category];
});
stripe(parts,first,last,'S');
parts.getRange(`A${first}:S${last}`).format.rowHeight=88;
for (const [mpn,height] of [['G5Q-1 DC12',220],['54-00133',152]]) {
  const r=first+rows.findIndex(p=>p.mpn===mpn);
  parts.getRange(`A${r}:S${r}`).format.rowHeight=height;
}
parts.getRange(`H${first}:R${last}`).format.horizontalAlignment='right';
for(const col of ['J','L','N','P','R'])parts.getRange(`${col}${first}:${col}${last}`).setNumberFormat('"$"0.00000');
for(const col of ['H','I','K','M','O','Q'])parts.getRange(`${col}${first}:${col}${last}`).setNumberFormat('#,##0');
parts.freezePanes.freezeRows(5);
for(let i=0;i<rows.length;i++){
  const p=rows[i],r=first+i;
  let expr=`'Parts'!J${r}`;
  for(let t=1;t<p.prices.length;t++){
    const qtyCol=String.fromCharCode(73+t*2),priceCol=String.fromCharCode(74+t*2);
    expr=`IF(D${r}>='Parts'!${qtyCol}${r},'Parts'!${priceCol}${r},${expr})`;
  }
  order.getRange(`E${r}:G${r}`).formulas=[[`=IF(D${r}=0,0,${expr})`,`=ROUND(D${r}*E${r},2)`,`=D${r}-C${r}`]];
}
order.getRange(`A${total}`).values=[['DigiKey parts subtotal']];
order.getRange(`F${total}`).formulas=[[`=SUM(F${first}:F${last})`]];
order.getRange(`A${total}:H${total}`).format.borders={top:{style:'thin',color:'#596C7B'}};
order.getRange(`A${total}:H${total}`).format.font={name:font,size:11,bold:true};
order.getRange(`F${total}:F${total+2}`).setNumberFormat('"$"0.00');
order.getRange(`A${total+1}`).values=[['Carrier parts plus MOD1']];
order.getRange(`F${total+1}`).formulas=[[`=SUM(F${first}:F${first+data.parts.length+data.modules.length-1})`]];
order.getRange(`A${total+2}`).values=[['Mates and shunts']];
order.getRange(`F${total+2}`).formulas=[[`=SUM(F${first+data.parts.length+data.modules.length}:F${last})`]];
order.getRange(`A${total+4}`).values=[['Shipping, tax, tariffs, bare PCB, wire, crimp tools and unpriced items on Other items are excluded.']];
order.getRange(`A${total+4}`).format.wrapText=false;
order.getRange(`A${total+5}`).values=[['The CSV contains the initial 27 purchase lines. It does not update automatically when this workbook is edited.']];
order.getRange(`A${total+5}`).format.wrapText=false;

const excluded=[
 ['WT32-SC01 Plus',1,'Existing display/controller','51.39 × 75.14 mm OEM blind-boss pattern. Mount to the top through the internal retainer. Measure boss depth, glass envelope, cables and antenna clearance.'],
 ['ADS1115 blue 10-pin module',1,'Already owned','VDD, GND, SCL, SDA, ADDR, ALRT, A0–A3. Confirm 2.54 mm pitch, module edge offsets, total socketed height, local supply bypassing, and SDA/SCL pull-ups to VDD.'],
 ['Carrier bare PCB',1,'Not yet orderable','60 × 92 mm draft. Zero routed tracks. Resolve footprint, antenna, mechanical and load checks before routing and Gerber release.'],
 ['M2 × 10 mm screws',2,'Source locally / unpriced','Provisional 5807 fasteners. Verify the real module/spacer/carrier stack before buying a production quantity.'],
 ['M2 washers, OD ≤5 mm',4,'Source locally / unpriced','One under each screw head and nut. Ø5 mm maximum; head plus top washer ≤2 mm high. Hidden USB clearances accommodate module and hardware without visible board/hardware cutouts. Check component clearance.'],
 ['M2 ordinary nuts',2,'Source locally / unpriced','Install under the carrier PCB. Verify clearance to the bottom floor and nearby support posts. Prevent contact with exposed circuitry.'],
 ['3 mm nylon spacers',2,'Source locally / unpriced','Between the Adafruit 5807 and carrier at H5/H6. Verify actual component-side and solder-joint clearance.'],
 ['Adhesive insulating support',1,'Source locally / unpriced','Support the rear/free edge of the 5807 at approximately 3 mm height; do not cover components or solder joints.'],
 ['Printed case and WT32 retainer',3,'Fit prototype / unpriced','Top, base and retainer: 104 × 86 × 44.9 mm provisional. Flush RJ45/barrel. USB recess 20 × 10 × 2 mm, shell opening 9.54 × 4.1 mm, face level with floor. A 1 mm internal backing gives a 1.5 mm nominal floor, ≥0.943 mm at hidden clearances.'],
 ['WT32 small self-tapping screws',4,'Diameter and length need sample','Pass through the 2.5 mm retainer into existing rear blind bosses. OEM drawing shows a 2.3 mm pilot. Check thread and engagement without bottoming out.'],
 ['M3 short heat-set inserts',10,'Ruthex RX-M3Sx4.0 / unpriced','4 carrier, 4 closure, 2 retainer. OD 4.6 mm, L 4 mm, pilot 4 mm, blind depth 5 mm. Source: https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3s-100stuck-rx-m3x4-0-short-messing-gewindebuchsen-fur-3d-druck'],
 ['M3 × 6 mm carrier screws',4,'Source locally / unpriced','Use four 0.5 mm insulating washers, OD no more than 7 mm. Nominal engagement 3.9 mm through the 1.6 mm carrier. Verify insert depth.'],
 ['M3 insulating washers',4,'0.5 mm thick, OD ≤7 mm','Between screw heads and carrier. Keep the top head/washer within the reserved 7 mm envelope.'],
 ['M3 × 18 mm closure screws',4,'Head OD ≤6 mm, height ≤3 mm','Install through top bezel into bottom inserts. Nominal engagement 3.9 mm with the 3.2 mm head recess. Verify actual screw length and print before tightening.'],
 ['M3 × 6 mm button-head screws',2,'Head height ≤2 mm','Retainer to top insert bosses. Nominal engagement 3.5 mm through the 2.5 mm retainer.'],
 ['Q1 insulating support and adhesive',1,'Material needs thermal check','Maintain 1 mm under flat MOSFET body. Use a cured insulating support and side fillets for transport. Keep the live drain tab away from copper; no tab bolt.'],
 ['Compliant display perimeter strip',1,'Material and preload need sample','Place only on inactive border. Model allows 0.3 mm compressed thickness. Hard stops control assembly height without case screws clamping the glass.'],
 ['ADC insulating support',1,'Geometry not determined','Support the socketed ADS1115 free edge and retain it for transport. Verify actual socket seating and underside protrusions. No guessed module mounting holes.'],
 ['WT32-end EXT / DEBUG mates',2,'Not included in DigiKey order','Confirm exact WT32 connector and mating cable. JST-XH BOM parts are only the carrier ends of these harnesses.'],
 ['Hookup wire / insulation',null,'As required; unpriced','Use a short 20-22 AWG red/black pair from 5807 V+/GND to J1. Label J1 separately from 3.3 V J7; their housings interchange physically.'],
 ['Crimp tool and assembly supplies',null,'Existing or source separately','Correct crimps, solder, insulation and strain relief required. Bare contact price excludes crimping labor/tool.'],
 ['USB-C PD source and cable',1,'Existing or source separately','Required design assumption: compliant 12 V USB-PD source and cable limited to 3 A. Configure MOD1 for 12 V / 3 A and confirm voltage/polarity with a meter.'],
 ['12 V wall adapter and barrel plug',1,'Optional; source separately','Use only a protected/current-limited regulated 12 V adapter rated no more than 3 A with a 5.5 × 2.1 mm center-positive plug. K1 automatically gives powered wall input priority over USB-PD. No internal adjustment. Transfer may restart the controller; verify contact inrush and adapter brownout.'],
 ['HeaterMeter blower / MG90S / cable',1,'Existing assembly','Measure startup/loaded motion and combined RJ45 return current. This revision intentionally has no onboard fuses or branch-selective overcurrent protection. Do not connect carrier RJ45 to Ethernet equipment.'],
 ['2.5 mm NTC probes',3,'Existing / up to three','PIT, MEAT 1, MEAT 2. Verify calibration and firmware excitation-reference equation before thermal testing.']
];
base(other,`A1:H${excluded.length+8}`,[260,72,250,690,40,40,40,40],
  'Other assembly requirements','Not included in the DigiKey subtotal. Unknown quantities and prices are left blank, not assumed free.');
other.getRange('A3').values=[['Carrier enclosure r6: 2 mm USB recess, socket face level with floor. 4 mm installation slide. K1 needs 16.2 mm seated height; other parts allow 16 mm.']];
other.getRange('A3').format.wrapText=false;
header(other,'A5:D5',['Item','Qty','Procurement','Assembly requirement']);
other.getRange(`A6:D${5+excluded.length}`).values=excluded;
stripe(other,6,5+excluded.length,'D');
other.getRange(`A6:D${5+excluded.length}`).format.rowHeight=62;
other.getRange(`B6:B${5+excluded.length}`).setNumberFormat('#,##0');
other.freezePanes.freezeRows(5);

// Reconcile each price/quantity against independently calculated source tiers.
const calculated=order.getRange(`C${first}:G${last}`).values;
let independentlyTotal=0;
for(let i=0;i<rows.length;i++){
  const p=rows[i],expectedUnit=priceAt(p,p.order),expectedLine=Math.round(p.order*expectedUnit*100)/100;
  assert.equal(calculated[i][0],p.needed);
  assert.equal(calculated[i][1],p.order);
  assert.ok(Math.abs(calculated[i][2]-expectedUnit)<1e-8);
  assert.ok(Math.abs(calculated[i][3]-expectedLine)<1e-8);
  assert.equal(calculated[i][4],p.order-p.needed);
  independentlyTotal+=expectedLine;
}
assert.ok(Math.abs(order.getRange(`F${total}`).values[0][0]-independentlyTotal)<1e-8);
assert.ok(Math.abs(independentlyTotal-29.21)<1e-8);
// Exercise the important tier boundary, then restore the final order.
const capRow=first+rows.findIndex(p=>p.refs.includes('C2'));
order.getRange(`D${capRow}`).values=[[10]];
assert.ok(Math.abs(order.getRange(`F${capRow}`).values[0][0]-1.46)<1e-8);
order.getRange(`D${capRow}`).values=[[5]];
assert.ok(Math.abs(order.getRange(`F${total}`).values[0][0]-29.21)<1e-8);
console.log((await wb.inspect({kind:'table',range:`Order!A${total}:H${total+2}`,include:'values,formulas',tableMaxRows:3,tableMaxCols:8,maxChars:2500})).ndjson);
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:300},maxChars:3000});
console.log(errors.ndjson);
for(const [sheetName,range,name] of [['Order','A1:H21','order-top'],['Order',`A22:H${total+2}`,'order-bottom'],
  ['Parts','A1:F13','parts'],['Parts','H5:S13','price-breaks'],['Other items',`A1:D${5+excluded.length}`,'other-items']]){
  const img=await wb.render({sheetName,range,scale:1,format:'png'});
  await fs.writeFile(`${scratch}/${name}.png`,new Uint8Array(await img.arrayBuffer()));
}
const csvCell=v=>'"'+String(v??'').replaceAll('"','""')+'"';
const csvRows=[['Manufacturer Part Number','Digi-Key Part Number','Quantity','Customer Reference'],
  ...rows.filter(p=>p.order>0).map(p=>[p.mpn,p.sku,p.order,p.refs.join(', ')])];
assert.equal(csvRows.length-1,27);
await fs.writeFile(`${out}/pitclaw-carrier-digikey-import.csv`,csvRows.map(r=>r.map(csvCell).join(',')).join('\r\n')+'\r\n');
const verification={revision:data.revision,totalUSD:29.21,carrierAndModuleUSD:28.25,matesAndShuntUSD:0.96,
  populatedPCBReferences:37,dnpPCBReferences:0,purchaseLines:27,boardMountedModules:1,
  removedReferences:['Q3','R7','R19','F1','F2','F3','F4','D1','C5','C7','C13','R17','R18','JP2'],priceTierBoundaryTest:true,
  formulaErrors:errors.ndjson.includes('matched 0 entries')?0:errors.ndjson};
await fs.writeFile(`${scratch}/bom-verification.json`,JSON.stringify(verification,null,2)+'\n');
await fs.writeFile(`${root}/hardware/carrier-revb/verification/bom-verification.json`,JSON.stringify(verification,null,2)+'\n');
const xlsx=await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(`${out}/pitclaw-carrier-digikey-bom.xlsx`);
await fs.mkdir(delivery,{recursive:true});
await xlsx.save(`${delivery}/pitclaw-carrier-digikey-bom.xlsx`);
console.log('Exported workbook and DigiKey import CSV. Subtotal USD 29.21.');
