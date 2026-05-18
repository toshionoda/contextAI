const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx');
const path = require('path');

async function build() {
    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';
    pptx.author = 'Malme';
    pptx.title = '橋梁の調査・設計・施工 DX導入提案';
    pptx.subject = '佐賀市 / 地元建設会社向け';

    const slides = [
        '01_title.html',
        '02_agenda.html',
        '03_three_walls.html',
        '04_three_phases.html',
        '05_dx_package.html',
        '06_civilink_value.html',
        '07_matrix.html',
        '08_poc_plan.html',
        '09_subsidy.html',
        '10_future_and_next.html',
        '11_closing.html',
    ];

    for (const file of slides) {
        const filePath = path.resolve(__dirname, file);
        console.log(`Processing: ${file}`);
        try {
            await html2pptx(filePath, pptx);
        } catch (err) {
            console.error(`Error in ${file}:`, err.message);
            throw err;
        }
    }

    const outputPath = path.resolve(__dirname, '../saga_bridge_dx_proposal.pptx');
    await pptx.writeFile({ fileName: outputPath });
    console.log(`\n✅ Built: ${outputPath}`);
}

build().catch(err => {
    console.error('Build failed:', err);
    process.exit(1);
});
