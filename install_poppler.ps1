# Create a temporary directory
$tempDir = "C:\temp"
if (-not (Test-Path $tempDir)) {
    New-Item -Path $tempDir -ItemType Directory -Force | Out-Null
}

# Download URL for Poppler
$url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.02.0-0/Release-24.02.0-0.zip"
$zipPath = "$tempDir\poppler.zip"
$extractPath = "C:\poppler"

Write-Host "Downloading Poppler for Windows..."
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
} catch {
    Write-Host "Error downloading Poppler: $_"
    Write-Host "Please download manually from: https://github.com/oschwartz10612/poppler-windows/releases/"
    exit 1
}

# Verify the download succeeded
if (-not (Test-Path $zipPath)) {
    Write-Host "Download failed. Zip file not found at $zipPath"
    exit 1
}

Write-Host "Download completed. Extracting Poppler..."

# Extract the ZIP file
try {
    if (Test-Path $extractPath) {
        Remove-Item -Path $extractPath -Recurse -Force
    }
    
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
    Write-Host "Poppler extracted to $extractPath"
} catch {
    Write-Host "Error extracting Poppler: $_"
    Write-Host "Please extract manually to C:\poppler"
    exit 1
}

# Update the .env file
$envPath = ".\backend\.env"
$popplerPath = "C:\\poppler\\bin"

if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    
    if ($envContent -match "POPPLER_PATH=") {
        # Update existing line
        $envContent = $envContent -replace "POPPLER_PATH=.*", "POPPLER_PATH=$popplerPath"
        $envContent | Set-Content $envPath
    } else {
        # Add new line
        Add-Content $envPath "`nPOPPLER_PATH=$popplerPath"
    }
    
    Write-Host "Updated .env file with Poppler path: $popplerPath"
} else {
    Write-Host "Warning: .env file not found at $envPath"
}

# Add to current session PATH
$env:Path += ";C:\poppler\bin"
Write-Host "Added Poppler to current session PATH"

# Try to add to system PATH (requires admin rights)
try {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $popplerDir = "C:\poppler\bin"
    
    if (-not $currentPath.Contains($popplerDir)) {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$popplerDir", "Machine")
        Write-Host "Added Poppler to system PATH"
    }
} catch {
    Write-Host "Unable to add Poppler to system PATH (requires admin rights): $_"
    Write-Host "You may need to add it manually"
}

Write-Host "Poppler installation completed. Try uploading your files again!" 