const fs = require('fs');
const path = require('path');

const NOTE_DIR = path.join(__dirname, 'note');
const OUT_FILE = path.join(__dirname, 'history.json');

function parseJsonFile(filePath, fileName) {
  const content = fs.readFileSync(filePath, 'utf8');
  let data;
  try {
    data = JSON.parse(content);
  } catch (e) {
    return null;
  }
  // Extract lottery code from filename if not in JSON
  let lottery = '';
  let draw = '';
  let date = '';
  if (data.lottery_name) {
    // Try to extract code from name, e.g. "DHANALEKSHMI (DL)"
    const codeMatch = data.lottery_name.match(/\(([A-Z]{2,3})\)/);
    lottery = codeMatch ? codeMatch[1] : '';
  }
  if (!lottery && fileName) {
    const fileMatch = fileName.match(/^([A-Z]{2,3})-/);
    lottery = fileMatch ? fileMatch[1] : '';
  }
  draw = data.draw_number ? String(data.draw_number).padStart(2, '0') : '';
  date = data.draw_date || '';
  // Prizes array
  const prizes = [];
  // For prediction
  const numbers4 = new Set();
  const numbers6 = new Set();
  if (data.prizes && typeof data.prizes === 'object') {
    for (const [prize_key, prize_obj] of Object.entries(data.prizes)) {
      prizes.push({
        prize_key,
        label: prize_obj.label || '',
        amount: prize_obj.amount || 0,
        winners: Array.isArray(prize_obj.winners) ? prize_obj.winners : []
      });
      // Collect numbers for prediction
      if (["4th_prize","5th_prize","6th_prize","7th_prize","8th_prize","9th_prize"].includes(prize_key)) {
        // 4-digit numbers
        if (Array.isArray(prize_obj.winners)) {
          prize_obj.winners.forEach(w => {
            const m = String(w).match(/\b(\d{4})\b/);
            if (m) numbers4.add(m[1]);
          });
        }
      } else if (["1st_prize","2nd_prize","3rd_prize","consolation_prize"].includes(prize_key)) {
        // 6-digit numbers
        if (Array.isArray(prize_obj.winners)) {
          prize_obj.winners.forEach(w => {
            const m = String(w).match(/\b(\d{6})\b/);
            if (m) numbers6.add(m[1]);
          });
        }
      }
    }
  }
  // Add downloadLink if present
  const downloadLink = data.downloadLink || '';
  // Add github_url for this file
  const github_url = `https://raw.githubusercontent.com/santhkhd/kerala_loto/main/note/${encodeURIComponent(fileName)}`;
  return {
    date,
    lottery,
    draw,
    filename: fileName,
    github_url,
    prizes,
    numbers4: Array.from(numbers4),
    numbers6: Array.from(numbers6),
    downloadLink
  };
}

function main() {
  const files = fs.readdirSync(NOTE_DIR).filter(f => f.endsWith('.json'));
  const history = [];
  for (const file of files) {
    const filePath = path.join(NOTE_DIR, file);
    const result = parseJsonFile(filePath, file);
    if (result && result.date && result.prizes.length) {
      history.push(result);
    }
  }
  // Sort by date descending
  history.sort((a, b) => {
    // Handle "Unknown-Date" entries by putting them at the end
    if (a.date === "Unknown-Date" && b.date === "Unknown-Date") return 0;
    if (a.date === "Unknown-Date") return 1;
    if (b.date === "Unknown-Date") return -1;
    
    // For regular dates, sort descending (newest first)
    return new Date(b.date) - new Date(a.date);
  });
  
  // Remove duplicate entries for the same date, keeping the most recent one
  const uniqueHistory = [];
  const seenDates = new Set();
  
  for (const entry of history) {
    if (entry.date !== "Unknown-Date" && seenDates.has(entry.date)) {
      // Skip duplicate dates
      continue;
    }
    seenDates.add(entry.date);
    uniqueHistory.push(entry);
  }
  
  fs.writeFileSync(OUT_FILE, JSON.stringify(uniqueHistory, null, 2), 'utf8');
  console.log(`Generated ${OUT_FILE} with ${uniqueHistory.length} draws.`);
}

main();