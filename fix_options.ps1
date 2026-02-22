$jsPath = 'C:\Users\hhari\Desktop\newfolder11\web_app\static\js\main.js'
$content = Get-Content -Path $jsPath -Raw

# Find and replace the incomplete updateExtractLayerUI function
$oldFunction = @"
function updateExtractLayerUI(layer) {
    const typeSelect = document.getElementById(\`ml-ex-`+"`${layer}"+@"-type`);
    const type = typeSelect.value;

    // Update UI based on type if needed
    // This ensures proper display for extract section
    if (type === 'text') {
        // Text layers might need special handling
    }
}
"@

$newFunction = @"
function updateExtractLayerUI(layer) {
    const typeSelect = document.getElementById(\`ml-ex-`+"`${layer}"+@"-type`);
    const type = typeSelect.value;

    // Update UI based on type if needed
    // This ensures proper display for extract section
    if (type === 'text') {
        // Text layers might need special handling
    }
    // Trigger any UI updates needed for the selected type
    const uploadArea = document.getElementById(\`ml-ex-`+"`${layer}"+@"-upload`);
    if (uploadArea) {
        uploadArea.style.display = type === 'text' ? 'none' : 'block';
    }
}
"@

if ($content -contains $oldFunction) {
    $content = $content.Replace($oldFunction, $newFunction)
    Set-Content -Path $jsPath -Value $content -Encoding UTF8
    Write-Host "Fixed updateExtractLayerUI function"
} else {
    Write-Host "Could not find exact function match, checking for partial match..."
    if ($content -contains "function updateExtractLayerUI(layer)") {
        Write-Host "Function found but pattern didn't match exactly"
    }
}
