# PowerShell script to install the native messaging host for Windows

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

# Paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$appName = "com.passmgr.extension"
$hostPath = "C:\Program Files\Password Manager\browser-host.exe"

# Create the installation directory if it doesn't exist
$installDir = Split-Path -Parent $hostPath
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# Copy the native host executable (placeholder - replace with actual build step)
# Copy-Item -Path "$scriptDir\..\dist\browser-host.exe" -Destination $hostPath -Force

# Create registry entries for each browser
$browsers = @(
    @{ Name = "Chrome"; Key = "HKCU:\SOFTWARE\Google\Chrome\NativeMessagingHosts\$appName" },
    @{ Name = "Edge"; Key = "HKCU:\SOFTWARE\Microsoft\Edge\NativeMessagingHosts\$appName" },
    @{ Name = "Firefox"; Key = "HKCU:\SOFTWARE\Mozilla\NativeMessagingHosts\$appName" },
    @{ Name = "Opera"; Key = "HKCU:\SOFTWARE\Opera Software\NativeMessagingHosts\$appName" }
)

$manifestPath = "$scriptDir\native-messaging\$appName.json"

foreach ($browser in $browsers) {
    try {
        # Create the registry key
        New-Item -Path $browser.Key -Force | Out-Null
        Set-ItemProperty -Path $browser.Key -Name "(Default)" -Value $manifestPath -Force
        Write-Host "Successfully installed for $($browser.Name)" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install for $($browser.Name): $_" -ForegroundColor Red
    }
}

Write-Host "\nNative messaging host installation complete!" -ForegroundColor Green
Write-Host "Note: You'll need to build and place the browser-host.exe in $installDir" -ForegroundColor Yellow
