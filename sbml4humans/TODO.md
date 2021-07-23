## TODO 
Tables:
- make code more compact; remove `vbind`; remove unnecassary spans/divs; remove unnecessary closing tags
- [x] rename in *Table similar to SpeciesTable
- use Table mixin to remove redundant js code in tables
- [x] smaller font sizes (see styling in ListOfSpecies)
- [x] center align the boolean fields
- [x] add advanced table features: sorting rows; searching content; pagination(for many objects);datatables.js

- [x] icons for different type (e.g. box for compartment; ) use in cross links and headers

SBML information:
- [.] annotations/notes to SBase detail view

Low priority
- [.] fix npm deprecations and warnings: https://github.com/matthiaskoenig/sbmlutils/issues/251
- [ ] include offline version of font-awesome (either static files or npm package): https://fontawesome.com/v5.15/how-to-use/on-the-web/setup/hosting-font-awesome-yourself
  
Minor things
- [x] layout: no line break in example description on firefox
- [x] layout: use tags for packages and keywords  
- [ ] layout: better layout of images next to text (about breakpoints)

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
