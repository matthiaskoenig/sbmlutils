## TODO

DetailsView:
- [ ] add JSON button with Icon to show backend JSON for details
- [x] PRIORITY 3:! sbml: fields such as initialAmount not rendered for species (e.g. repressilator PX); `info.initialAmount != null`; update for all checks !!!
- [x] PRIORITY 3:! sbml: same for tables

Tables:
- [x] PRIORITY 1: layout: hide horizontal scrollbars if not necessary (padding/layout issue)
- [x] PRIORITY 2: layout: use datatables: "compact" option and remove grids
- [x] PRIORITY 4: layout make table rows clickable with selecting DetailView
- [ ] make code more compact; remove `vbind`; remove unnecassary spans/divs; remove unnecessary closing tags
- [ ] use Table mixin to remove redundant js code in tables

ModelSelection
- checkbox/radio buttons to switch available models; use `title` as explanation; more user friendly/intuitive

SBML information:
- [.] annotations/notes to SBase detail view; 
- [ ] nice rendering of CVTerms as badges: [qualifier][resource][identifier]; which is clickable; split in individual triples

Low priority
- [.] fix npm deprecations and warnings: https://github.com/matthiaskoenig/sbmlutils/issues/251
- [ ] include offline version of font-awesome (either static files or npm package): https://fontawesome.com/v5.15/how-to-use/on-the-web/setup/hosting-font-awesome-yourself
  
Minor things
- [ ] layout: add icon for SBMLDocument
- [ ] layout: add icon next to Document & models
- [ ] layout: ensure headings look the same (ListOf and Detail)
- [ ] layout: Document & models width must be identical to components in toasters
Math rendering
- [ ] issues with google chrome

Filter
- [.] more robust handling of state --- not migrating to localStorage for testing purposes
- [.] simplify filter by just iterating over list of SBases --- implemented via visibility flag

## List of existing problems:
- [] Unit math strings are not longer coming from backend
- [] Filter is slow (5-6 secs) on large models (e.g. Recon3D)
        - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
        - Solution: => refactor filter (see TODOs above)
   
- [] Search is slow (5-6 secs) on large models (e.g. Recon3D)
    - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
    - no solution for now -> switching to elasticsearch based on JSON in future
    
# MK:
- [ ] Support of combine archives & resolve external model definitions

Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)
