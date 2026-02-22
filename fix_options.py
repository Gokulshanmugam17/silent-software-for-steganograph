#!/usr/bin/env python3
import re

js_path = r'C:\Users\hhari\Desktop\newfolder11\web_app\static\js\main.js'

with open(js_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the updateExtractLayerUI function
old_function = '''function updateExtractLayerUI(layer) {
    const typeSelect = document.getElementById(`ml-ex-${layer}-type`);
    const type = typeSelect.value;

    // Update UI based on type if needed
    // This ensures proper display for extract section
    if (type === 'text') {
        // Text layers might need special handling
    }
}'''

new_function = '''function updateExtractLayerUI(layer) {
    const typeSelect = document.getElementById(`ml-ex-${layer}-type`);
    const type = typeSelect.value;

    // Update UI based on type if needed
    // This ensures proper display for extract section
    if (type === 'text') {
        // Text layers might need special handling
    }
    // Trigger any UI updates needed for the selected type
    const uploadArea = document.getElementById(`ml-ex-${layer}-upload`);
    if (uploadArea) {
        uploadArea.style.display = type === 'text' ? 'none' : 'block';
    }
}'''

if old_function in content:
    content = content.replace(old_function, new_function)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Fixed updateExtractLayerUI function - options now work properly")
else:
    print("Could not find exact function match")
    # Try to find it with regex and more flexible whitespace
    pattern = r'function updateExtractLayerUI\(layer\) \{[^}]*\}'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print(f"Found function: {match.group(0)[:100]}...")
