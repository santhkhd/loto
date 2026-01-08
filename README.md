# Kerala Lottery Results Website

A modern, mobile-friendly, multilingual Kerala lottery results site powered by static files and real historical data.

## Features

- Google Sheets backend for easy editing
- Automated static site generation (HTML/JSON)
- Search, prediction, and scanner tools
- Beautiful, responsive UI with language support
- Fully automated publishing with GitHub Actions

## Workflow

1. **Edit results** in Google Sheets.
2. **Export or fetch** latest results as HTML into `githublotery/note/`.
3. **Run** `node generate-history.js` in `githublotery/` to update `history.json`.
4. **Push** changes to GitHub.
5. **GitHub Actions** auto-generates and deploys the site.

## Local Development

```sh
cd githublotery
node generate-history.js
# Open index.html in your browser
```

## Deployment

- All files in `githublotery/` are published as a static site (e.g., via GitHub Pages).
- The workflow in `.github/workflows/build-and-deploy.yml` automates build and deployment.

## Folder Structure

```
your-repo/
│
├─ githublotery/
│   ├─ index.html
│   ├─ prediction.html
│   ├─ search.html
│   ├─ scanner.html
│   ├─ resultgen3.html
│   ├─ history.json
│   ├─ generate-history.js
│   ├─ note/
│   │   └─ [draw HTML files...]
│   └─ [other assets, e.g. CSS, images, etc.]
│
├─ .github/
│   └─ workflows/
│       └─ build-and-deploy.yml
│
├─ README.md
└─ [other project files]
```

## License

MIT 