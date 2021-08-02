## TODO

DetailView:
- [ ] make table or similar thing (smaller font sizes)
- [ ] notes/cvterms and additional information at bottom; 
- [ ] use vue magic (slots/mixins?)

Annotations/Notes:
- [ ] build a fast api dummy backend endpoint which gives you `resource_info = {term: abcd, name: protein ABC, definition: This is the protein ABC important for ..., synonyms: [protein abc, ABC1B]`} with a time delay (sleep 0.2 s) which you query with resources of cvterms 'urn:miriam:chebi:CHEBI%3A33699'; 
'https://identifiers.org/CHEBI:33699'
  
- [ ] build simple rendering of information in DetailView
- [ ] build caching layer for resources: {resource: resource_info}; if resource in cache use cache else query; timeouts, cache sizes;
- [.] annotations/notes to SBase detail view;

Layout:
- [ ] JSON and XML should be closed on first loading
- [ ] fix colors in table headings

Tables:
- [ ] use Table mixin to remove redundant js code in tables

ModelSelection
- [ ] checkbox/radio buttons to switch available models; use `title` as explanation; more user friendly/intuitive


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

- [] Filter is slow (5-6 secs) on large models (e.g. Recon3D)
        - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
        - Solution: => refactor filter (see TODOs above)
   
- [] Search is slow (5-6 secs) on large models (e.g. Recon3D)
    - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
    - no solution for now -> switching to elasticsearch based on JSON in future
    
# MK:
## Annotations
- [ ] refactor backend annotation code into into separate package

## Units
- [ ] Unit math strings are not longer coming from backend
Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)

## OMEX
- [ ] Support of combine archives & resolve external model definitions
