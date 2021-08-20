## TODO
Layout fixes
- [ ] make DocumentMenu look like ComponentMenu
- [ ] table for examples (paginate & search & sort)
- [ ] click on icon should navigate to home page 
- [ ] fix offset on navbar or bring on top  
- [ ] make searchbar 100%  
- [ ] make report 100%, so only tables scroll
- [ ] remove pagination if not needed from tables
- [ ] use tooltips instead of alt/title tags (v-tooltip=)  
- [ ] render uncertainty nicer (currently only list)

# ---------------------    
# MK:
## Annotations
- [ ] refactor backend annotation code into into separate package

## Units
- Fix assignments (not listed)

Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)
- replace: alpha, beta, ..., gamma, ....

# Later features
Report via URL 
- [ ] think about strategy for supporting reports: https://github.com/matthiaskoenig/sbmlutils/issues/257
- [ ] python function to create report

Static report:
- [~] create static report 
- [~] option for download static report

## OMEX
- [ ] Support of combine archives & resolve external model definitions
