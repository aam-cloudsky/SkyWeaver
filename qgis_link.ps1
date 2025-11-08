param([string]$PythonArgs = "")

# --- Path to your Conda environment python.exe ---
$venvPython = "C:\Users\davi_\.conda\envs\skyweaver312\python.exe"

# --- QGIS installation root ---
$QGIS_ROOT = "C:\Program Files\QGIS 3.40.8"
$o4w_env = Join-Path $QGIS_ROOT "bin\o4w_env.bat"

if (-not (Test-Path $o4w_env)) {
    Write-Error "Cannot find $o4w_env. Adjust QGIS_ROOT if necessary."
    exit 1
}

Write-Host "Loading QGIS environment from $o4w_env ..."

# --- Call o4w_env.bat inside cmd.exe and capture its output ---
$envOutput = cmd /c "call `"$o4w_env`" && set"

foreach ($line in $envOutput) {
    if ($line -match "^[^=]+=.*$") {
        $name, $val = $line -split "=", 2
        switch ($name) {
            "PATH" {
                # Prepend QGIS PATH so its DLLs come first
                $env:PATH = "$val;$env:PATH"
            }
            "QGIS_PREFIX_PATH" { $env:QGIS_PREFIX_PATH = $val }
            "GDAL_DATA" { $env:GDAL_DATA = $val }
            "PROJ_LIB" { $env:PROJ_LIB = $val }
            "QT_PLUGIN_PATH" { $env:QT_PLUGIN_PATH = $val }
            "QT_QPA_PLATFORM_PLUGIN_PATH" { $env:QT_QPA_PLATFORM_PLUGIN_PATH = $val }
            "PYTHONPATH" {
                if ($env:PYTHONPATH) { $env:PYTHONPATH = "$val;$env:PYTHONPATH" }
                else { $env:PYTHONPATH = $val }
            }
        }
    }
}

# --- Add explicit Python folders (for safety) ---
$QGIS_PYTHON1 = "$QGIS_ROOT\apps\qgis-ltr\python"
$QGIS_PYTHON2 = "$QGIS_ROOT\apps\Python312\Lib\site-packages"
$QGIS_PLUGINS = "$QGIS_PYTHON1\plugins"

# --- Inline Python verification ---
$pycmd = @"
import sys, os
for p in [r'$QGIS_PYTHON1', r'$QGIS_PYTHON2', r'$QGIS_PLUGINS']:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
print('sys.executable =', sys.executable)
print('QGIS_PREFIX_PATH =', os.environ.get('QGIS_PREFIX_PATH'))
print('PATH head:')
for p in os.environ['PATH'].split(';')[:8]:
    print('  ', p)
from qgis.core import QgsApplication
print('✅ QGIS imported successfully')
"@

& $venvPython -c $pycmd

# --- Run Python if arguments were passed, otherwise stay open interactively ---
if ($PythonArgs) {
    # Non-interactive mode – run the Python command and exit
    & $venvPython -c $PythonArgs
}
else {
    Write-Host ""
    Write-Host "───────────────────────────────────────────────"
    Write-Host "🌐  QGIS environment loaded for SkyWeaver"
    Write-Host "💻  Active Python: $venvPython"
    Write-Host "🧭  QGIS root:    $QGIS_ROOT"
    Write-Host "───────────────────────────────────────────────"
    Write-Host ""
    Write-Host "Your Conda environment skyweaver312 is active."
    Write-Host "Type 'python' to open Python with QGIS support, or run your scripts normally."
    Write-Host ""

    # Drop into an interactive PowerShell session that inherits this environment
    powershell -NoExit -NoLogo -ExecutionPolicy Bypass
}
