# PowerShell script to generate placeholder icons for the extension

# Create icons directory if it doesn't exist
$iconDir = Join-Path $PSScriptRoot "icons"
if (-not (Test-Path $iconDir)) {
    New-Item -ItemType Directory -Path $iconDir | Out-Null
}

# Icon sizes needed for the extension
$sizes = @(16, 32, 48, 64, 96, 128)

# Create a simple icon for each size
foreach ($size in $sizes) {
    $outputPath = Join-Path $iconDir "icon$size.png"
    
    # Create a simple colored square with text as a placeholder
    $bitmap = New-Object System.Drawing.Bitmap $size, $size
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    
    # Fill with a nice blue color
    $graphics.Clear([System.Drawing.Color]::FromArgb(25, 118, 210))
    
    # Add text in the center
    $font = New-Object System.Drawing.Font("Arial", ($size/4), [System.Drawing.FontStyle]::Bold)
    $brush = [System.Drawing.Brushes]::White
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center
    
    $graphics.DrawString("PM", $font, $brush, $size/2, $size/2, $format)
    
    # Save the image
    $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    
    Write-Host "Created icon: $outputPath"
    
    # Clean up
    $graphics.Dispose()
    $bitmap.Dispose()
}

Write-Host "\nIcons generated successfully in: $iconDir" -ForegroundColor Green
