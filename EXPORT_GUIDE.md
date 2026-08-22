# 📊 System Design Diagrams Export Guide

## Created Files

### Diagram Source Files (.mmd)
- `diagrams_exported/1_system_design.mmd`
- `diagrams_exported/2_uml_class_diagram.mmd`
- `diagrams_exported/3_user_flow.mmd`
- `diagrams_exported/4_data_flow.mmd`
- `diagrams_exported/5_entity_relationship.mmd`
- `diagrams_exported/6_sequence_diagram.mmd`

### Export Tools

#### Option 1: Use Browser (Easiest)
1. Open `export_diagrams.html` in a web browser
2. Right-click on any diagram
3. Select "Save image as..."
4. Choose PNG or SVG format

#### Option 2: Use Command Line (Best Quality)
1. Install mermaid-cli:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. **Windows**: Run `export_diagrams.bat`
3. **Linux/Mac**: Run `bash export_diagrams.sh`

#### Option 3: Manual CLI Export
```bash
mmdc -i diagrams_exported/1_system_design.mmd -o diagrams_exported/1_system_design.png
```

## Diagram List

| # | Diagram | Use Case |
|---|---------|----------|
| 1 | System Design | High-level architecture overview |
| 2 | UML Class Diagram | Entity relationships & methods |
| 3 | User Flow | User journey & workflows |
| 4 | Data Flow | Information transformation |
| 5 | Entity Relationship | Database schema |
| 6 | Sequence Diagram | Chat processing flow |

## Output Formats

- **PNG**: Best for presentations, web, documents
- **SVG**: Scalable, editable in design tools
- **PDF**: Printable, professional documents

## Tips

- PNG files are ~100-300KB each
- SVG files are editable in Inkscape, Adobe Illustrator, etc.
- High resolution: Use `--width 1920 --height 1080` with mmdc
- All diagrams use consistent color scheme for professional look

## Troubleshooting

**Issue**: "mmdc command not found"
- Solution: `npm install -g @mermaid-js/mermaid-cli`

**Issue**: PNG quality is poor
- Solution: Use `mmdc --scale 2` for 2x resolution

**Issue**: Can't edit exported PNG
- Solution: Export as SVG instead for editability

---
Generated: May 12, 2026
