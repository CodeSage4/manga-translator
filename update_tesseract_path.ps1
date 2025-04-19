# Ask for Tesseract path
$tesseractPath = Read-Host "Please enter the full path to tesseract.exe (including the filename)"

# Check if the path exists
if (-not (Test-Path $tesseractPath)) {
    Write-Host "WARNING: File not found at the specified path: $tesseractPath"
    $confirm = Read-Host "Do you want to continue anyway? (y/n)"
    if ($confirm -ne "y") {
        Write-Host "Operation cancelled."
        exit
    }
}

# Escape backslashes for the .env file
$envPath = $tesseractPath -replace "\\", "\\"

# Update the .env file
$envFile = ".\backend\.env"
$envContent = Get-Content $envFile -Raw

if ($envContent -match "TESSERACT_PATH=") {
    # Update existing line
    $envContent = $envContent -replace "TESSERACT_PATH=.*", "TESSERACT_PATH=$envPath"
    $envContent | Set-Content $envFile
} else {
    # Add new line
    Add-Content $envFile "`nTESSERACT_PATH=$envPath"
}

Write-Host "Updated .env file with Tesseract path: $envPath"

# Try to test Tesseract
try {
    Write-Host "Testing Tesseract..."
    $version = & $tesseractPath --version
    Write-Host "Tesseract is working! Version info:"
    Write-Host $version
} catch {
    Write-Host "Could not execute Tesseract. Please make sure it's installed correctly."
}

Write-Host "Done. Press any key to exit."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 