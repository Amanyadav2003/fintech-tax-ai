const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  const diagramsDir = './diagrams_exported';
  const files = fs.readdirSync(diagramsDir).filter(f => f.endsWith('.mmd'));
  
  for (const file of files) {
    const mmdPath = path.join(diagramsDir, file);
    const pngPath = path.join(diagramsDir, file.replace('.mmd', '.png'));
    
    const mermaidCode = fs.readFileSync(mmdPath, 'utf-8');
    
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"><\/script>
        <style>
          body { margin: 0; padding: 20px; background: white; }
          .mermaid { display: flex; justify-content: center; }
        </style>
      </head>
      <body>
        <div class="mermaid">
${mermaidCode}
        </div>
        <script>
          mermaid.initialize({ startOnLoad: true, theme: 'default', securityLevel: 'loose' });
          mermaid.contentLoaded();
        </script>
      </body>
      </html>
    `;
    
    await page.setContent(html);
    
    // Wait for mermaid to render
    await page.waitForTimeout(2000);
    
    const element = await page.$('.mermaid');
    if (element) {
      await element.screenshot({ path: pngPath });
      console.log(`✅ Exported: ${pngPath}`);
    }
  }
  
  await browser.close();
  console.log("\n✅ All diagrams exported successfully!");
})();
