# MathJax 3.2.2

Vendored so that the documentation does not request any script or font from a third party at view time. It is the combined component `tex-mml-chtml.js` (TeX and MathML input, CHTML output) of the [`mathjax@3.2.2`](https://www.npmjs.com/package/mathjax/v/3.2.2) npm package, `package/es5/tex-mml-chtml.js`, and the web fonts it loads next to itself from `output/chtml/fonts/woff-v2/`. The license is Apache 2.0, see `LICENSE`.

The files are byte for byte those of the tarball `https://registry.npmjs.org/mathjax/-/mathjax-3.2.2.tgz`, whose integrity hash in the npm registry is `sha512-Bt+SSVU8eBG27zChVewOicYs7Xsdt40qm4+UpHyX7k0/O9NliPc+x77k1/FEsPsjKPZGJvtRZM1vO+geW0OhGw==`. The files are minified third party code and are excluded from the whitespace hooks of pre-commit; do not edit them. To update, take the same files from the new version of the package and change the version here and in `zensical.toml`.
