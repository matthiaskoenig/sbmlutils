## TODO

- [ ] table for examples (paginate & search & sort)
- [ ] click on icon should navigate to home page  
- [ ] make report 100%, so only tables scroll  
- [ ] use tooltips instead of alt/title tags (v-tooltip=)  
- [ ] render uncertainty nicer (currently only list)
- [~] Replace toaster with a real menu component: https://www.primefaces.org/primevue/showcase/#/menu  


Report via URL
- [ ] think about strategy for supporting reports: https://github.com/matthiaskoenig/sbmlutils/issues/257

Static report:
- [~] create static report 
- [~] option for download static report
  
# ---------------------    
# MK:
## Annotations
- [ ] refactor backend annotation code into into separate package
## OMEX
- [ ] Support of combine archives & resolve external model definitions
## Units
- [ ] Unit math strings are not longer coming from backend
Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)



