@echo off
REM Export Mermaid Diagrams to PNG using mermaid-cli
REM First, install mermaid-cli: npm install -g @mermaid-js/mermaid-cli

echo Creating diagrams folder...
if not exist diagrams_exported mkdir diagrams_exported

echo.
echo Checking if mermaid-cli is installed...
where mmdc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ mermaid-cli not found. Installing...
    npm install -g @mermaid-js/mermaid-cli
)

echo.
echo 📊 Exporting diagrams to PNG...
echo ======================================

mmdc -i diagrams_exported/1_system_design.mmd -o diagrams_exported/1_system_design.png
mmdc -i diagrams_exported/2_uml_class_diagram.mmd -o diagrams_exported/2_uml_class_diagram.png
mmdc -i diagrams_exported/3_user_flow.mmd -o diagrams_exported/3_user_flow.png
mmdc -i diagrams_exported/4_data_flow.mmd -o diagrams_exported/4_data_flow.png
mmdc -i diagrams_exported/5_entity_relationship.mmd -o diagrams_exported/5_entity_relationship.png
mmdc -i diagrams_exported/6_sequence_diagram.mmd -o diagrams_exported/6_sequence_diagram.png

echo.
echo ✅ Export complete!
echo 📁 Check diagrams_exported folder for PNG files
pause
