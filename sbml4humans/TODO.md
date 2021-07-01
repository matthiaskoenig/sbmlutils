## TODO 
- [x] switch examples and about
- [x] fix modal to 80%  --- did to 40%, please take a look on how it looks
- [x] Detail View use background color instead of coloring the title
- [.] make the scss imports work (should be clickable in idea frontend; perhaps use `src` on style) -- still not working :/
- [x] hide scrollbars if not needed!
- [.] annotations/notes to SBase detail view
- [x] close filter menu on click
- [x] add icons in search field and button;
- [x] no horizontal scrollbar for detail view
- [x] fix corners in SBMLToaster
- [x] maxwidth for components
- [x] use available space better on report page
- [ ] use icons in Details View: true/false/none -> check/check-circle green/times-circle red/ fa-ban black
- [ ] constant/initialConcentration attribute missing on species
- [x] compartment must be link on species
- [ ] render null information;
- [ ] add boxes headers for inter-component navigation
- [x] drop "In" from reactantIn, productIn, speciesIn, ...; relatedSpecies -> Species
- [ ] in species: make reactant, product, modifier list next to each other

- [ ] Create ListOf Table Component for navigation;

Math rendering
- [ ] issues with google chrome

ModelDefinitions/comp
- [x] check all comp components (specification)
- [x] handle modeldefinitions; split component list in SBMLDocument/Model & Rest
- [x] use ICG model for Ports, replacedElements, Submodels

Intercomponent navigation
- [x] keep a stack for the detail view (only show previous & next)

Filter
- [.] more robust handling of state --- not migrating to localStorage for testing purposes
- [.] simplify filter by just iterating over list of SBases --- implemented via visibility flag

Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)

## List of existing problems:
- [] Unit math strings are not longer coming from backend
- [] Filter is slow (5-6 secs) on large models (e.g. Recon3D)
        - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
        - Solution: => refactor filter (see TODOs above)
   
- [] Search is slow (5-6 secs) on large models (e.g. Recon3D)
    - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
    - no solution for now -> switching to elasticsearch based on JSON in future

## Things to ask:
- [ ] do we need a forward button as well in the detail nav bar 
- [ ] how to handle multiple occurences of the same component in the detail nav bar
