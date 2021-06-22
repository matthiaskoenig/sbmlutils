## TODO 
- [x] make loading report component (modal); use in Upload & Examples
- [x] define global styles for components to make large containers look consistent 
     (heading sizes, color scheme used for page)
- [x] include fontawesome icons: https://fontawesome.com/v6.0/; plus/minus icon for XML
- [x] color code DetailView with sbmlType color (mapping: sbmlType: color)  
- [x] add SId and Name to title of components: `<strong>UnitDefinition</strong> time (minute)`
- [.] make the scss imports work (should be clickable in idea frontend; perhaps use `src` on style) -- still not working :/
- [x] hide scrollbars if not needed
- [.] add cvterms & annotations to SBase Detail view --- annotation left
- [x] Fix Species in for loop

Math rendering
- [ ] issues with google chrome
- [x] reactions: kineticLaw Math

Intercomponent navigation
- [ ] intercomponent links: Species -> compartments; Reaction: -> Species
- [ ] back/forward navigation for via stack of ids;
- [ ] add models on SBMLDocument Details views for easy access/entry point (just links not green boxes)

Filter
- [x] move search (always visible) & filter to navigation bar (collapsable)
- [.] more robust handling of state --- not migrating to localStorage for testing purposes
- [.] simplify filter by just iterating over list of SBases --- implemented via visibility flag

Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)

Add intercomponent-links in JSON (MK):
- [ ] in processing JSON links have to be generated (backend); `links`: {'reactants': [pk1, pk2, ..], ..., parameters: [pk10, pk12], ...} 

## List of existing problems:
- [] Filter is slow (5-6 secs) on large models (e.g. Recon3D)
        - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
        - Solution: => refactor filter (see TODOs above)
   
- [] Search is slow (5-6 secs) on large models (e.g. Recon3D)
    - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
    - no solution for now -> switching to elasticsearch based on JSON in future
