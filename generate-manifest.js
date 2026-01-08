// Node.js script to generate a manifest of available result files in the note folder
// This will output a file called result_manifest.json with metadata for each result

const fs = require('fs');
const path = require('path');

const NOTE_DIR = path.join(__dirname, 'note');
const MANIFEST_FILE = path.join(__dirname, 'result_manifest.json');

function parseResultFilename(filename) {
  // Example: SK-17-2025-08-29.json
  const match = filename.match(/^([A-Z]{2,3})-(\d+)-(\d{4}-\d{2}-\d{2})\.json$/);
  if (!match) return null;
  return {
    code: match[1],
    draw_number: match[2],
    date: match[3],
    filename
  };
}

fs.readdir(NOTE_DIR, (err, files) => {
  if (err) throw err;
  const manifest = files
    .filter(f => f.endsWith('.json'))
    .map(parseResultFilename)
    .filter(Boolean);
  // Sort by date descending
  manifest.sort((a, b) => {
    // Handle date comparison properly
    const dateA = new Date(a.date);
    const dateB = new Date(b.date);
    
    // Invalid dates go to the end
    if (isNaN(dateA) && isNaN(dateB)) return 0;
    if (isNaN(dateA)) return 1;
    if (isNaN(dateB)) return -1;
    
    return dateB - dateA;
  });
  
  // Remove duplicate entries for the same date, keeping the most recent one
  const uniqueManifest = [];
  const seenDates = new Set();
  
  for (const entry of manifest) {
    if (seenDates.has(entry.date)) {
      // Skip duplicate dates
      continue;
    }
    seenDates.add(entry.date);
    uniqueManifest.push(entry);
  }
  
  fs.writeFileSync(MANIFEST_FILE, JSON.stringify(uniqueManifest, null, 2));
  console.log(`Manifest written to ${MANIFEST_FILE} with ${uniqueManifest.length} results.`);
});