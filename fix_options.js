const fs = require('fs');
const path = require('path');

const jsPath = path.join(__dirname, 'web_app/static/js/main.js');

let content = fs.readFileSync(jsPath, 'utf-8');

const oldFunction = `function updateExtractLayerUI(layer) {
    const typeSelect = document.getElementById(\`ml-ex-\${layer}-type\`);
    const type = typeSelect.value;

    // Update UI based on type if needed
    // This ensures proper display for extract section
    if (type === 'text') {
        // Text layers might need special handling
    }
}`;

const newFunction = `function updateExtractLayerUI(layer) {
    const typeSelect = document.getElementById(\`ml-ex-\${layer}-type\`);
    const type = typeSelect.value;

    // Update UI based on type if needed
    // This ensures proper display for extract section
    if (type === 'text') {
        // Text layers might need special handling
    }
    // Trigger any UI updates needed for the selected type
    const uploadArea = document.getElementById(\`ml-ex-\${layer}-upload\`);
    if (uploadArea) {
        uploadArea.style.display = type === 'text' ? 'none' : 'block';
    }
}`;

if (content.includes(oldFunction)) {
    content = content.replace(oldFunction, newFunction);
    fs.writeFileSync(jsPath, content, 'utf-8');
    console.log('✓ Fixed updateExtractLayerUI function - options now work properly');
} else {
    console.log('Could not find exact function match');
    console.log('Searching for partial match...');
    if (content.includes('function updateExtractLayerUI(layer)')) {
        console.log('Function exists but whitespace differs');
    }
}
