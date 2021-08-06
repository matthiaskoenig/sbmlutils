## TODO

Annotations/Notes:
- [ ] build caching layer for resources, use cache adaptor
  https://github.com/RasCarlito/axios-cache-adapter
  https://www.npmjs.com/package/axios-cache-adapter
- [.] annotations/notes to SBase detail view;

Layout:
- [ ] restructure navbar: small on the left side; start tables & details on top of page (full height)
- [ ] remove colors from navigation menu & from DetailView
- [ ] make `name` a subtitle in the DetailView
- [ ] ids bold in table
- [ ] layout: add icon for SBMLDocument
- [ ] layout: add icon next to Document & models
- [ ] layout: Document & models width must be identical to components in toasters
- [ ] layout: Reduce space between tables by moving search & entries next to heading

Search:
- [ ] fix search: make search filter all tables for matching elements

Filter:
- [ ] remove filter functionality (hide)

Deployment:
- fix jquery issue -> use npm package for datatables: https://datatables.net/download/npm
- [.] fix npm deprecations and warnings: https://github.com/matthiaskoenig/sbmlutils/issues/251
- [ ] npm fontawesome (see https://www.npmjs.com/package/vue-awesome): include offline version of font-awesome (either static files or npm package): https://fontawesome.com/v5.15/how-to-use/on-the-web/setup/hosting-font-awesome-yourself

Static report:
- Remove/Fix websocket calls
- [ ] create static report 
- [ ]option for download static report
  
# ---------------------    
# MK:
## Annotations
- [ ] refactor backend annotation code into into separate package

## Units
- [ ] Unit math strings are not longer coming from backend
Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)

## Deployment

## OMEX
- [ ] Support of combine archives & resolve external model definitions
