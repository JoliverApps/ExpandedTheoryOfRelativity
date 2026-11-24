# Building and publishing

The canonical manuscript is `ExpandedTheoryOfRelativity.tex`. Edit it or the included chapter, appendix, bibliography, and figure files, then push to `main`. The publishing workflow rebuilds both editions, saves the generated PDF and website in the repository, and deploys the website through GitHub Pages.

## Local build (Ubuntu)

Install the dependencies:

```sh
sudo apt-get update
sudo apt-get install -y latexmk latexml texlive-latex-extra texlive-publishers texlive-science texlive-fonts-recommended ghostscript python3-lxml
python3 scripts/build.py
```

The build script downloads the BOONDOX and mathalpha TeX dependencies from CTAN into `_build/texmf`. It leaves the manuscript source unchanged. The PDF uses REVTeX 4.2 and its matching `apsrev4-2` bibliography style.

The resulting files are `ExpandedTheoryOfRelativity.pdf`, `index.html`, and `assets/`. `_site/` contains the deployable website. `_build/` contains temporary sources and build logs.

The HTML conversion uses LaTeXML, native MathML, and an SVG version of the TikZ figure. It reads the PDF build's BibTeX output to preserve citation order, and uses the same section and appendix equation numbering. Font-only settings and the unused `diff` macro are omitted from the temporary HTML input to avoid converter incompatibilities; the canonical LaTeX source is preserved.

## GitHub Pages

In repository **Settings → Pages → Build and deployment**, choose **GitHub Actions** as the source. The `Publish manuscript` workflow handles subsequent publication. It can also be run manually from the Actions tab.

Failed builds stop before replacing the published website. The PDF and HTML remain downloadable from their existing addresses after successful updates.

## Reading accessibility

The HTML edition includes skip links, a main-content landmark, a consistent heading hierarchy, visible keyboard focus, larger-text and colour-scheme controls, and keyboard access to equations that need horizontal scrolling. Mathematics remains native MathML, and the figure is linked to its caption. Reading preferences are saved only in the reader's browser; browser zoom also works without JavaScript.

## Visits and PDF clicks

Edit `web/analytics.json` to connect your hosted GoatCounter site:

```json
{
  "goatcounter_url": "https://YOUR-SITE.goatcounter.com",
  "public_totals": true
}
```

An empty `goatcounter_url` disables analytics and hides the public totals. No API token or password belongs in the repository. In GoatCounter, enable **Allow adding visitor counts on your website** for public totals to work.

The page records visits to `/ExpandedTheoryOfRelativity/` and an event named `expanded-relativity-pdf-download` when its Download PDF link is clicked. The event counts each click; it does not prove a completed transfer and cannot count visits directly to the PDF URL. The default visit count groups repeat page loads within GoatCounter's session window. Statistics begin when tracking is enabled; there is no historical backfill.

Public totals can be cached by GoatCounter for up to four hours. Zero is shown when reported by GoatCounter; a dash means a total is not available. Do Not Track and Global Privacy Control disable the tracking script; public totals may still be read without sending a visit event. Blocking analytics or disabling JavaScript never prevents reading the paper or downloading the PDF.

Documentation: [getting started](https://www.goatcounter.com/help/start), [events](https://www.goatcounter.com/help/events), [public counters](https://www.goatcounter.com/help/visitor-counter), and [privacy](https://www.goatcounter.com/help/privacy).
