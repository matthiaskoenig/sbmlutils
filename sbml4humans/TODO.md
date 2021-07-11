## TODO 
- [ ] fix npm deprecations and warnings: https://github.com/matthiaskoenig/sbmlutils/issues/251

- [ ] bug: filter menu should not close on select/deselect click  
- [x] bug: no scrollbar on examples  
- [x] layout: upload only half-width on landing page 
- [x] layout: add SBML logo and GSOC logo to about page  
- [.] annotations/notes to SBase detail view
- [.] use icons in Details View: true/false/none -> check/check-circle green/times-circle red/ fa-ban black
- [.] constant/initialConcentration attribute missing on species

- [ ] refactor the TableView (drop ListOf prefixes from table navigation; make all tables visible at once with scrolling via menu)
- [ ] refactor navigation: Tables/Details/ListOf ...


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
