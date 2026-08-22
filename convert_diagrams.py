#!/usr/bin/env python3
"""
Convert Mermaid diagrams to PNG using Puppeteer/Playwright via browser rendering
Alternative method if mermaid-cli is not available
"""

import os
import subprocess
import sys
from pathlib import Path

def create_browser_converter():
    """Create a Node.js script using Puppeteer to convert Mermaid to PNG"""
    
    converter_js = '''const puppeteer = require('puppeteer');
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
  console.log("\\n✅ All diagrams exported successfully!");
})();
'''
    
    with open('convert_mermaid.js', 'w', encoding='utf-8') as f:
        f.write(converter_js)
    
    print("✅ Created: convert_mermaid.js")
    return True

def install_puppeteer():
    """Install puppeteer"""
    print("📦 Installing Puppeteer...")
    try:
        subprocess.run(['npm', 'install', 'puppeteer'], check=True)
        print("✅ Puppeteer installed")
        return True
    except:
        print("❌ Failed to install Puppeteer")
        return False

def convert_with_puppeteer():
    """Run the converter script"""
    print("\n🎨 Converting Mermaid diagrams to PNG...")
    try:
        subprocess.run(['node', 'convert_mermaid.js'], check=True)
        print("✅ Conversion complete!")
        return True
    except:
        print("❌ Conversion failed")
        return False

def create_simple_html_export():
    """Create a simple HTML page that allows manual saving of diagrams"""
    
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>Export Diagrams to PNG</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 { color: #667eea; }
        .diagram-card {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .mermaid {
            display: flex;
            justify-content: center;
            background: #fafafa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover { background: #764ba2; }
        .controls { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>📊 Export Diagrams as PNG</h1>
    
    <div class="controls">
        <button onclick="exportAll()">📥 Export All Diagrams</button>
        <button onclick="location.reload()">🔄 Refresh</button>
    </div>
    
    <div id="diagrams"></div>

    <script>
        const diagrams = {
            "1_system_design": "System Design - Architecture",
            "2_uml_class_diagram": "UML Class Diagram",
            "3_user_flow": "User Flow & Chat Workflow",
            "4_data_flow": "Data Flow Diagram",
            "5_entity_relationship": "Entity Relationship Diagram",
            "6_sequence_diagram": "Sequence Diagram"
        };

        async function loadDiagrams() {
            const container = document.getElementById('diagrams');
            
            for (const [key, title] of Object.entries(diagrams)) {
                try {
                    const response = await fetch(`diagrams_exported/${key}.mmd`);
                    const mermaidCode = await response.text();
                    
                    const card = document.createElement('div');
                    card.className = 'diagram-card';
                    card.innerHTML = `
                        <h2>${title}</h2>
                        <div class="mermaid" id="${key}">
${mermaidCode}
                        </div>
                        <button onclick="saveDiagram('${key}')">Save ${key}</button>
                    `;
                    container.appendChild(card);
                } catch (e) {
                    console.error(`Failed to load ${key}:`, e);
                }
            }
            
            mermaid.initialize({ startOnLoad: true, securityLevel: 'loose' });
            mermaid.contentLoaded();
        }

        async function saveDiagram(diagramId) {
            const element = document.getElementById(diagramId);
            const svg = element.querySelector('svg');
            
            if (!svg) {
                alert('Diagram not rendered yet. Please wait and try again.');
                return;
            }

            try {
                const canvas = await html2canvas(element, { 
                    scale: 2,
                    backgroundColor: '#ffffff'
                });
                const link = document.createElement('a');
                link.href = canvas.toDataURL('image/png');
                link.download = `${diagramId}.png`;
                link.click();
            } catch (e) {
                console.error('Export failed:', e);
                alert('Export failed. Try right-click > Save image as instead.');
            }
        }

        async function exportAll() {
            for (const key of Object.keys(diagrams)) {
                await new Promise(resolve => setTimeout(resolve, 500));
                saveDiagram(key);
            }
        }

        // Load diagrams on page load
        window.addEventListener('load', loadDiagrams);
    </script>
</body>
</html>
'''
    
    with open('export_to_png.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Created: export_to_png.html")
    return True

def main():
    print("🎨 Diagram Export Tool")
    print("=" * 60)
    
    # Create simple HTML export first
    create_simple_html_export()
    
    print("\n📋 Export Methods Available:")
    print("\n Method 1: Use HTML (Easy - No Installation)")
    print("   ✅ Open export_to_png.html in browser")
    print("   ✅ Click 'Export All Diagrams' button")
    print("   ✅ PNG files will download")
    
    print("\n Method 2: Use Puppeteer (Best Quality)")
    print("   1. Run: npm install puppeteer")
    print("   2. Run: node convert_mermaid.js")
    
    print("\n Method 3: Use CLI (Mermaid-cli)")
    print("   1. npm install -g @mermaid-js/mermaid-cli")
    print("   2. mmdc -i diagrams_exported/*.mmd -o diagrams_exported/")
    
    print("\n" + "=" * 60)
    print("🚀 Starting with easiest method...")
    print("=" * 60)
    
    # Check for Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"✅ Node.js found: {result.stdout.strip()}")
        
        # Ask user if they want to use Puppeteer
        print("\n💡 Tip: For better quality, you can use Puppeteer:")
        print("   1. Create convert_mermaid.js")
        print("   2. npm install puppeteer")
        print("   3. node convert_mermaid.js")
        
        response = input("\nWould you like to set up Puppeteer? (y/n): ").lower()
        if response == 'y':
            create_browser_converter()
            if install_puppeteer():
                convert_with_puppeteer()
    except:
        print("⚠️  Node.js not found, using HTML method only")
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("\n📁 Diagram source files in: diagrams_exported/")
    print("📂 Export using: export_to_png.html")
    print("=" * 60)

if __name__ == '__main__':
    main()
