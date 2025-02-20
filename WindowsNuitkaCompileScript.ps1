# Variables del proyecto
$PROJECT_DIR = Get-Location  # Directorio raíz del proyecto
$MAIN_SCRIPT = "app/main.py"
$ICON_FILE = "app/resources/icons/icon.ico"
$JSON_FILE = "app/models/dev_info.json"
$IMAGE_FILE = "app/resources/media/TlacuiaLogo.png"

# Rutas a las fuentes y archivo de licencia
$FONTS_DIR = "app/utils/fonts"
$LICENSE_FILE = "LICENSE.txt"   # Definir la variable para el archivo de licencia
$FONT_LICENSE = "$FONTS_DIR/licenses/LICENSE.txt"

# Comando de compilación con Nuitka
Write-Host "Compilando la aplicación con Nuitka..."
nuitka `
    --standalone `
    --windows-icon-from-ico="$ICON_FILE" `
    --windows-console-mode=disable `
    --enable-plugin=pyqt5 `
    --include-data-file="$JSON_FILE=app/models/dev_info.json" `
    --include-data-file="$ICON_FILE=app/resources/icons/icon.ico" `
    --include-data-file="$IMAGE_FILE=app/resources/media/TlacuiaLogo.png" `
    --include-data-file="$LICENSE_FILE=LICENSE.txt" `
    --include-data-file="$FONTS_DIR/OfficeCodePro-Bold.ttf=app/utils/fonts/OfficeCodePro-Bold.ttf" `
    --include-data-file="$FONTS_DIR/OfficeCodePro-BoldItalic.ttf=app/utils/fonts/OfficeCodePro-BoldItalic.ttf" `
    --include-data-file="$FONTS_DIR/OfficeCodePro-Light.ttf=app/utils/fonts/OfficeCodePro-Light.ttf" `
    --include-data-file="$FONTS_DIR/OfficeCodePro-LightItalic.ttf=app/utils/fonts/OfficeCodePro-LightItalic.ttf" `
    --include-data-file="$FONTS_DIR/OfficeCodePro-Medium.ttf=app/utils/fonts/OfficeCodePro-Medium.ttf" `
    --include-data-file="$FONTS_DIR/OfficeCodePro-MediumItalic.ttf=app/utils/fonts/OfficeCodePro-MediumItalic.ttf" `
    --include-data-file="$FONTS_DIR/OfficeCodePro-Regular.ttf=app/utils/fonts/OfficeCodePro-Regular.ttf" `
    --include-data-file="$FONTS_DIR/OfficeCodePro-RegularItalic.ttf=app/utils/fonts/OfficeCodePro-RegularItalic.ttf" `
    --include-data-file="$FONT_LICENSE=app/utils/fonts/licenses/LICENSE.txt" `
    "$MAIN_SCRIPT"

# Verificar si la compilación fue exitosa
if ($LASTEXITCODE -eq 0) {
    Write-Host "Compilación completada exitosamente."
} else {
    Write-Host "Error durante la compilación."
    exit 1
}

# Mover el resultado a una carpeta específica
$OUTPUT_DIR = Join-Path $PROJECT_DIR "dist"
New-Item -ItemType Directory -Force -Path $OUTPUT_DIR | Out-Null
Move-Item "$PROJECT_DIR/main.dist" "$OUTPUT_DIR/"  # Mover la carpeta generada
Write-Host "Carpeta de salida generada en: $OUTPUT_DIR"