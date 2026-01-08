/**
 * Kerala Lottery App Logic
 * Optimized for mobile-first UI and fast loading
 */

let currentLang = localStorage.getItem('lang') || 'en';
let manifestData = [];
let historyData = [];
let currentCategory = 'ALL';

const i18n = {
    en: {
        pageTitle: "Kerala Lottery",
        allResults: "All Results",
        noResults: "No results found for this category.",
        draw: "Draw",
        date: "Date",
        loading: "Loading results...",
        home: "Results",
        live: "Live",
        lucky: "Lucky",
        search: "Search",
        scanner: "Download"
    },
    ml: {
        pageTitle: "കേരള ലോട്ടറി",
        allResults: "എല്ലാ ഫലങ്ങളും",
        noResults: "ഫലങ്ങളൊന്നുമില്ല.",
        draw: "ഡ്രോ",
        date: "തീയതി",
        loading: "ഫലങ്ങൾ ശേഖരിക്കുന്നു...",
        home: "ഫലങ്ങൾ",
        live: "ലൈവ്",
        lucky: "ലക്കി",
        search: "തിരയുക",
        scanner: "ഡൗൺലോഡ്"
    },
    ta: {
        pageTitle: "கேரளா லாட்டரி",
        allResults: "அனைத்து முடிவுகள்",
        noResults: "முடிவுகள் இல்லை.",
        draw: "டிரா",
        date: "தேதி",
        loading: "முடிவுகள் ஏற்றப்படுகின்றன...",
        home: "முடிவுகள்",
        live: "நேரலை",
        lucky: "லக்கி",
        search: "தேடல்",
        scanner: "பதிவிறக்க"
    }
};

const catMap = {
    'SAMRUDHI': 'SM', 'BHAGYATHARA': 'BT', 'STHREE_SAKTHI': 'SS',
    'DHANALEKSHMI': 'DL', 'KARUNYA_PLUS': 'KN', 'SUVARNA_KERALAM': 'SK',
    'KARUNYA': 'KR', 'AKSHAYA': 'AK', 'WIN_WIN': 'WW', 'NIRMAL': 'NR'
};

const lotteryNames = {
    SM: { en: 'Samrudhi', ml: 'സമൃദ്ധി', ta: 'சம்ருத்தி' },
    BT: { en: 'Bhagyathara', ml: 'ഭാഗ്യതാര', ta: 'பாக்யதாரா' },
    SS: { en: 'Sthree Sakthi', ml: 'സ്ത്രീ ശക്തി', ta: 'ஸ்த்ரீ-சக்தி' },
    DL: { en: 'Dhanalekshmi', ml: 'ധനലക്ഷ്മി', ta: 'தனலட்சுமி' },
    KN: { en: 'Karunya Plus', ml: 'കരുണ്യ പ്ലസ്', ta: 'கருண்யா பிளസ്' },
    SK: { en: 'Suvarna Keralam', ml: 'സുവർണ കേരളം', ta: 'சுவர்ண கேരளம்' },
    KR: { en: 'Karunya', ml: 'കരുണ്യ', ta: 'கருண்யா' },
    AK: { en: 'Akshaya', ml: 'അക്ഷയ', ta: 'அக்ஷயா' },
    WW: { en: 'Win Win', ml: 'വിൻ വിൻ', ta: 'வின் வின்' },
    NR: { en: 'Nirmal', ml: 'നിർമ്മൽ', ta: 'நிர்மல்' }
};

// Theme Logic
let currentTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
document.body.className = currentTheme;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    updateDate();
    initLang();
    initCategories();
    initTheme();
    fetchManifest();

    // Offline Check
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
});

function initTheme() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    updateThemeIcon();
    toggle.addEventListener('click', () => {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.body.className = currentTheme;
        localStorage.setItem('theme', currentTheme);
        updateThemeIcon();
    });
}

function updateThemeIcon() {
    const icon = document.querySelector('#theme-toggle i');
    if (icon) icon.textContent = currentTheme === 'dark' ? 'light_mode' : 'dark_mode';
}

function updateOnlineStatus() {
    const banner = document.getElementById('offline-banner');
    if (banner) {
        banner.style.display = navigator.onLine ? 'none' : 'block';
    }
}

function updateDate() {
    const now = new Date();
    const options = { weekday: 'long', day: 'numeric', month: 'short' };
    const el = document.getElementById('today-date');
    if (el) el.textContent = now.toLocaleDateString(undefined, options);
}

function initLang() {
    const btns = document.querySelectorAll('.lang-btn');
    btns.forEach(btn => {
        if (btn.dataset.lang === currentLang) btn.classList.add('active');
        btn.addEventListener('click', () => {
            currentLang = btn.dataset.lang;
            localStorage.setItem('lang', currentLang);
            btns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateTranslations();
            renderResults();
        });
    });
    updateTranslations();
}

function updateTranslations() {
    const t = i18n[currentLang];
    const title = document.querySelector('h1');
    if (title) title.textContent = t.pageTitle;

    const empty = document.getElementById('empty-msg');
    if (empty) empty.textContent = t.noResults;

    const allChip = document.querySelector('[data-category="ALL"]');
    if (allChip) allChip.textContent = t.allResults;

    // Update nav labels
    const navItems = document.querySelectorAll('.nav-item');
    if (navItems.length >= 5) {
        navItems[0].querySelector('span').textContent = t.home;
        navItems[1].querySelector('span').textContent = t.live;
        navItems[2].querySelector('span').textContent = t.lucky;
        navItems[3].querySelector('span').textContent = t.search;
        navItems[4].querySelector('span').textContent = t.scanner;
    }
}

function initCategories() {
    const chips = document.querySelectorAll('.cat-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            currentCategory = chip.dataset.category;
            renderResults();
        });
    });
}

async function fetchManifest() {
    try {
        const response = await fetch('result_manifest.json');
        manifestData = await response.json();
        renderResults();
    } catch (e) {
        console.error("Failed to load manifest", e);
    }
}

function renderResults() {
    const list = document.getElementById('results-list');
    if (!list) return;
    const empty = document.getElementById('empty-state');

    // Filter
    const filtered = manifestData.filter(item => {
        if (currentCategory === 'ALL') return true;
        return item.code === catMap[currentCategory];
    }).slice(0, 365);

    if (filtered.length === 0) {
        list.innerHTML = '';
        if (empty) empty.style.display = 'block';
        return;
    }

    if (empty) empty.style.display = 'none';

    // Build fragment
    const fragment = document.createDocumentFragment();

    filtered.forEach(item => {
        const card = document.createElement('a');
        const isLocal = window.location.protocol === 'file:';
        const targetPage = isLocal ? 'result.html' : 'result';
        card.href = `${targetPage}?file=${item.filename}`;
        card.className = 'result-card fade-in';

        const name = lotteryNames[item.code] ? (lotteryNames[item.code][currentLang] || lotteryNames[item.code].en) : item.code;
        const date = item.date.split('-').reverse().join('/');

        // Check if item is "new" (e.g. from today or yesterday, or first item)
        // For simplicity, let's mark the very first item as NEW or check date
        const isNew = (filtered.indexOf(item) === 0);

        card.innerHTML = `
            <div class="card-upper">
                 ${isNew ? '<span class="badge-new">NEW</span>' : ''}
                 <span class="badge-code">${item.code}-${item.draw_number}</span>
                 <div class="card-title">${name}</div>
            </div>
            <div class="card-lower">
                 <div class="card-date">${date}</div>
            </div>
        `;
        fragment.appendChild(card);
    });

    list.innerHTML = '';
    list.appendChild(fragment);
}
