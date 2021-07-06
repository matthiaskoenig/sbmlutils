## TODO 
- [ ] add support for uncertainties & add uncertainty examples (`distributions_example.xml` and `uncertainty_example.xml`)
- [ ] move local scss in files; cleanup css (use bootstrap grid & spacing)
- [.] annotations/notes to SBase detail view
- [ ] color of compartment & reaction is identical on Species
- [ ] use icons in Details View: true/false/none -> check/check-circle green/times-circle red/ fa-ban black
- [.] constant/initialConcentration attribute missing on species

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


## List of New Changes in the Backend:
- [] Changed the PK to the form "{sbmlType}:{_uuid}". This was required as the change introducing the model specific components list was not working without it.

# MK:
- [ ] Support of combine archives & resolve external model definitions

Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)
