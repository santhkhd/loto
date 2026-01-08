const fs = require('fs');
const path = require('path');

// Configuration
const PDF_DATA_FILE = 'pdf_data.json';
const TIMEZONE = 'Asia/Kolkata';

// Lottery Schedule: 0=Sunday, 1=Monday, ... 6=Saturday (JS getDay() format)
// Note: Python was 0=Monday. JS is 0=Sunday. adjusted accordingly.
const SCHEDULE = {
    1: { name: 'BHAGYATHARA', code: 'BT' },    // Monday
    2: { name: 'STHREE-SAKTHI', code: 'SS' },  // Tuesday
    3: { name: 'DHANALEKSHMI', code: 'DL' },   // Wednesday
    4: { name: 'KARUNYA PLUS', code: 'KN' },   // Thursday
    5: { name: 'SUVARNA KERALAM', code: 'SK' },// Friday
    6: { name: 'KARUNYA', code: 'KR' },        // Saturday
    0: { name: 'SAMRUDHI', code: 'SM' }        // Sunday
};

function getIndianDate() {
    const now = new Date();
    const invdate = new Date(now.toLocaleString('en-US', { timeZone: TIMEZONE }));
    return invdate;
}

function parseDateStr(dateStr) {
    // dd/mm/yyyy
    const parts = dateStr.split('/');
    return new Date(parts[2], parts[1] - 1, parts[0]);
}

function formatDateStr(dateObj) {
    const d = String(dateObj.getDate()).padStart(2, '0');
    const m = String(dateObj.getMonth() + 1).padStart(2, '0');
    const y = dateObj.getFullYear();
    return `${d}/${m}/${y}`;
}

function getLatestDrawNo(data, code) {
    let max = 0;
    data.forEach(item => {
        if (item.draw_no.startsWith(code + '-')) {
            try {
                const num = parseInt(item.draw_no.split('-')[1]);
                if (num > max) max = num;
            } catch (e) { }
        }
    });
    return max;
}

function main() {
    const filePath = path.join(__dirname, PDF_DATA_FILE);

    if (!fs.existsSync(filePath)) {
        console.log("No existing data found.");
        return;
    }

    let data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

    // Assume data[0] is latest as per previous logic
    const latestEntry = data[0];
    const lastDate = parseDateStr(latestEntry.date);
    let lastSerial = parseInt(latestEntry.drawserial);

    const today = getIndianDate();
    // Reset time for comparison
    today.setHours(0, 0, 0, 0);
    lastDate.setHours(0, 0, 0, 0);

    if (lastDate >= today) {
        console.log(`Data is up to date (${formatDateStr(lastDate)}). No new PDFs to generate.`);
        return;
    }

    const newEntries = [];
    let currDate = new Date(lastDate);
    currDate.setDate(currDate.getDate() + 1); // Start from next day
    let currSerial = lastSerial + 1;

    while (currDate <= today) {
        const dayIdx = currDate.getDay(); // 0-6
        const info = SCHEDULE[dayIdx];

        if (info) {
            // Get last draw number mostly from existing data
            let lastNum = getLatestDrawNo(data, info.code);

            // Check newly added ones in this loop
            newEntries.forEach(e => {
                if (e.draw_no.startsWith(info.code + '-')) {
                    const num = parseInt(e.draw_no.split('-')[1]);
                    if (num > lastNum) lastNum = num;
                }
            });

            const newDrawNo = `${info.code}-${lastNum + 1}`;
            const dateStr = formatDateStr(currDate);

            const entry = {
                lottery: info.name,
                draw_no: newDrawNo,
                date: dateStr,
                drawserial: String(currSerial),
                url: `https://result.keralalotteries.com/viewlotisresult.php?drawserial=${currSerial}`
            };

            newEntries.unshift(entry); // Add to front
            console.log(`Generated: ${entry.date} - ${entry.lottery} (${entry.draw_no})`);
        }

        currDate.setDate(currDate.getDate() + 1);
        currSerial++;
    }

    if (newEntries.length > 0) {
        const updatedData = newEntries.concat(data);
        fs.writeFileSync(filePath, JSON.stringify(updatedData, null, 2));
        console.log(`Added ${newEntries.length} new entries to ${PDF_DATA_FILE}`);
    } else {
        console.log("No valid lottery days found in the gap.");
    }
}

main();
