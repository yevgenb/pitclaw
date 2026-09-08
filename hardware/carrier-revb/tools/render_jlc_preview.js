// Rasterize the independently parsed CAM previews. Does not modify CAD or CAM.
// node render_jlc_preview.js RELEASE_DIRECTORY NODE_MODULES_DIRECTORY
const fs = require('fs');
const path = require('path');
const [release, modules] = process.argv.slice(2);
const sharp = require(require.resolve('sharp', {paths: [modules]}));
const review = path.join(release, 'review');
const manifest = JSON.parse(fs.readFileSync(path.join(release, 'manifest.json')));
async function main() {
  const layers = [];
  for (const [i, side] of ['top', 'bottom'].entries()) {
    const svg = path.join(review, `gerber-${side}.svg`);
    const png = path.join(review, `gerber-${side}.png`);
    await sharp(svg, {density: 300}).flatten({background: '#fff'})
      .resize({height: 1180}).png().toFile(png);
    const meta = await sharp(png).metadata();
    layers.push({input: png, left: Math.round(i * 850 + (850-meta.width)/2), top: 150});
  }
  const labels = `<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="1420">
    <rect width="1700" height="1420" fill="white"/>
    <g font-family="Arial, sans-serif" fill="#17232e" text-anchor="middle">
      <text x="850" y="48" font-size="30" font-weight="bold">PitClaw carrier · JLCPCB manufacturing preview</text>
      <text x="850" y="82" font-size="20">60 × 92 mm · 2 layers · 1.6 mm FR-4 · 1 oz copper</text>
      <text x="425" y="128" font-size="23">Front · component side</text>
      <text x="1275" y="128" font-size="23">Back · solder side, mirrored</text>
      <text x="850" y="1365" font-size="19">Rendered from the verified Gerber/drill ZIP · bare-board prototype</text>
      <text x="850" y="1394" font-size="16" fill="#526270">PCB SHA-256 ${manifest.pcb_sha256}</text>
    </g></svg>`;
  await sharp(Buffer.from(labels)).composite(layers).png()
    .toFile(path.join(review, 'manufacturing-preview.png'));
}
main().catch(e => { console.error(e); process.exit(1); });
