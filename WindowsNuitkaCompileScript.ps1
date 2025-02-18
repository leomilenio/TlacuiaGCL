# Variables del proyecto
$PROJECT_DIR = Get-Location  # Directorio raíz del proyecto
$MAIN_SCRIPT = "app/main.py"
$ICON_FILE = "app/resources/icons/icon.ico"
$JSON_FILE = "app/models/dev_info.json"
$IMAGE_FILE = "app/resources/media/TlacuiaLogo.png"

# Comando de compilación con Nuitka
Write-Host "Compilando la aplicación con Nuitka..."

nuitka `
    --standalone `
    --onefile `
    --windows-icon-from-ico="$ICON_FILE" `
    --windows-console-mode=disable `
    --enable-plugin=pyqt5 `
    --include-data-file="$JSON_FILE=app/models/dev_info.json" `
    --include-data-file="$ICON_FILE=app/resources/icons/icon.ico" `
    --include-data-file="$IMAGE_FILE=app/resources/media/TlacuiaLogo.png" `
    --include-data-file="$LICENSE_FILE=LICENSE.txt" `
    "$MAIN_SCRIPT"

# Verificar si la compilación fue exitosa
if ($LASTEXITCODE -eq 0) {
    Write-Host "Compilación completada exitosamente."
} else {
    Write-Host "Error durante la compilación."
    exit 1
}

# Mover el ejecutable a una carpeta específica (opcional)
$OUTPUT_DIR = Join-Path $PROJECT_DIR "dist"
New-Item -ItemType Directory -Force -Path $OUTPUT_DIR | Out-Null
Move-Item "$PROJECT_DIR/main.exe" "$OUTPUT_DIR/"

Write-Host "Ejecutable generado en: $OUTPUT_DIR"