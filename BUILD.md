# Editing and publishing the website

The canonical manuscript is `index.html`. Edit that file for changes to the paper and update its displayed date when the manuscript content changes. Keep equation identifiers, reference links, and MathML markup consistent.

Website files:

- `assets/paper.css`: reader layout, colour schemes, and accessibility styles.
- `assets/reader.js`: reading preferences, keyboard access to wide equations, and visit counting.
- `assets/document.css` and `assets/article.css`: document formatting.
- `404.html`: directs unavailable website paths back to the current manuscript.

## Validate locally

The build uses Python 3.9 or newer and only its standard library:

```sh
python3 scripts/build.py
python3 -m http.server 8000 --directory _site
```

The validator checks document landmarks, mathematical content, internal references, assets, and visits-only analytics. The `_site/` directory is cleared and rebuilt for each publication. Asset versions are added during packaging so browser caches pick up updated styles and reader controls.

## Publish

Push changes to `main`. The GitHub Actions workflow validates the HTML and publishes `_site/` through GitHub Pages. In repository **Settings → Pages**, the publishing source is **GitHub Actions**.

The website itself is the maintained edition. No document compilation or downloadable manuscript files are part of this project.

## Visits

The `reader-config` JSON element in `index.html` connects the website to `https://joliverapps.goatcounter.com`. The visits path remains `/ExpandedTheoryOfRelativity/`, so existing visit statistics continue.

The page shows the public visit total. Public counters must remain enabled in GoatCounter's settings. An empty analytics URL disables tracking; no password or API token is needed in the repository.

GoatCounter can cache public totals for up to four hours. Repeat page loads are grouped according to its session settings. Do Not Track and Global Privacy Control disable visit tracking; public totals can still be read. Reader preferences are saved locally in the reader's browser.
