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
