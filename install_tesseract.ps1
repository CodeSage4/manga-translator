# Create a temporary directory
$tempDir = "C:\temp"
if (-not (Test-Path $tempDir)) {
    New-Item -Path $tempDir -ItemType Directory -Force | Out-Null
}

# Download URL for Tesseract
$url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.1.20230401/tesseract-ocr-w64-setup-5.3.1.20230401.exe"
$installerPath = "$tempDir\tesseract-installer.exe"

Write-Host "Downloading Tesseract OCR installer..."
try {
    # Using System.Net.WebClient which might work better in some environments
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($url, $installerPath)
    
    # If the download fails, try an alternative method
    if (-not (Test-Path $installerPath)) {
        Write-Host "First download method failed, trying alternative method..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $installerPath -UseBasicParsing
    }
} catch {
    Write-Host "Error downloading Tesseract using WebClient: $_"
    try {
        Write-Host "Trying alternative download method..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $installerPath -UseBasicParsing
    } catch {
        Write-Host "Error downloading Tesseract using Invoke-WebRequest: $_"
        Write-Host "Please download Tesseract installer manually from:"
        Write-Host "https://github.com/UB-Mannheim/tesseract/releases/"
        Write-Host "Save it to $installerPath and run this script again"
        exit 1
    }
}

# Verify the download succeeded
if (-not (Test-Path $installerPath)) {
    Write-Host "Download failed. Installer not found at $installerPath"
    exit 1
}

Write-Host "Download completed. Installing Tesseract OCR silently..."

# Install Tesseract with the required languages (English and Japanese are included by default)
try {
    # Use /D parameter to specify installation directory, with quotes to handle spaces
    $installArgs = '/S /D="C:\Program Files\Tesseract-OCR"'
    Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait
} catch {
    Write-Host "Error installing Tesseract: $_"
    Write-Host "Please try running the installer manually: $installerPath"
    exit 1
}

# Give the installer some time to finish
Start-Sleep -Seconds 5

# Verify the installation
$tesseractExe = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tesseractExe) {
    Write-Host "Tesseract OCR installed successfully at: $tesseractExe"
    
    # Create or update the .env file with the Tesseract path
    $envPath = ".\backend\.env"
    $tesseractPath = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    
    if (Test-Path $envPath) {
        $envContent = Get-Content $envPath -Raw
        if ($envContent -match "TESSERACT_PATH=") {
            $envContent = $envContent -replace "TESSERACT_PATH=.*", "TESSERACT_PATH=$tesseractPath"
        } else {
            $envContent += "`nTESSERACT_PATH=$tesseractPath"
        }
        $envContent | Set-Content $envPath
    } else {
        "TESSERACT_PATH=$tesseractPath" | Set-Content $envPath
    }
    
    Write-Host "Updated .env file with Tesseract path"
    
    # Add to current session PATH
    $env:Path += ";C:\Program Files\Tesseract-OCR"
    Write-Host "Added Tesseract to current session PATH"
    
    # Try to add to system PATH (requires admin rights)
    try {
        $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
        $tesseractDir = "C:\Program Files\Tesseract-OCR"
        if (-not $currentPath.Contains($tesseractDir)) {
            [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$tesseractDir", "Machine")
            Write-Host "Added Tesseract to system PATH"
        }
    } catch {
        Write-Host "Unable to add Tesseract to system PATH (requires admin rights): $_"
        Write-Host "You may need to add it manually"
    }
} else {
    Write-Host "Tesseract OCR installation could not be verified at expected location: $tesseractExe"
    Write-Host "The installer may have used a different path. Please check if Tesseract was installed successfully."
    
    # Try to find tesseract.exe
    $possiblePaths = @(
        "C:\Program Files\Tesseract-OCR\tesseract.exe",
        "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "C:\Tesseract-OCR\tesseract.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            Write-Host "Found Tesseract at: $path"
            # Update the .env file with this path
            $envPath = ".\backend\.env"
            $tesseractPath = $path -replace "\\", "\\"
            
            if (Test-Path $envPath) {
                $envContent = Get-Content $envPath -Raw
                if ($envContent -match "TESSERACT_PATH=") {
                    $envContent = $envContent -replace "TESSERACT_PATH=.*", "TESSERACT_PATH=$tesseractPath"
                } else {
                    $envContent += "`nTESSERACT_PATH=$tesseractPath"
                }
                $envContent | Set-Content $envPath
            } else {
                "TESSERACT_PATH=$tesseractPath" | Set-Content $envPath
            }
            
            Write-Host "Updated .env file with found Tesseract path"
            break
        }
    }
}

Write-Host "Installation process completed. If Tesseract is not working, please install it manually from:"
Write-Host "https://github.com/UB-Mannheim/tesseract/releases/" 