const pptxgen = require('pptxgenjs');
const html2pptx = require('../../../../skills/malme-slide-creator/scripts/html2pptx.js');
const path = require('path');
const fs = require('fs');

const slides = [
  'slides/01_title.html',
  'slides/02_background.html',
  'slides/03_current.html',
  'slides/04_risk.html',
  'slides/05_overview.html',
  'slides/06_tools.html',
  'slides/06a_bridge_inspection.html',
  'slides/06b_road_diagnosis.html',
  'slides/06c_crack_detection.html',
  'slides/06d_construction_plan.html',
  'slides/06e_photo_ledger.html',
  'slides/06f_approval_workflow.html',
  'slides/06g_quality_data.html',
  'slides/06h_rebar_inspection.html',
  'slides/07_platform.html',
  'slides/07a_poc_plan.html',
  'slides/08_support.html',
  'slides/09_budget.html',
  'slides/10_effect.html',
  'slides/11_partnership.html',
  'slides/12_summary.html',
];

async function main() {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = '佐賀市 デジタル推進課';
  pptx.company = '佐賀市';
  pptx.title = '佐賀市 地域建設業DX普及促進事業（案）';

  for (const slideFile of slides) {
    const filePath = path.resolve(__dirname, slideFile);
    console.log(`Processing: ${slideFile}`);
    try {
      const { slide, placeholders } = await html2pptx(filePath, pptx);
      console.log(`  -> OK (placeholders: ${placeholders.length})`);
    } catch (err) {
      console.error(`  -> ERROR: ${err.message.split('\n')[0]}`);
    }
  }

  const outputPath = path.resolve(__dirname, '../saga_dx_budget_proposal.pptx');
  const buffer = await pptx.write({ outputType: 'nodebuffer' });
  fs.writeFileSync(outputPath, buffer);
  console.log(`\nOutput: ${outputPath} (${(buffer.length / 1024).toFixed(0)} KB)`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
