## TODO

- [~] Switch to some native Vue datatables (sorting, searching, filtering): https://www.primefaces.org/primevue/showcase/#/ 
  Probably migrating datatables for now (some minor bugs exist)
  - [ ] Create working example for SpeciesTable
  - [ ] Fix Proxy issue with data in global map -> should just be objects!  
  - [ ] Global search: search on all table fields    
  - [ ] fix: "Query.Deferred exception: col is undefined DataTable" when loading models
  - [ ] fix: remove datatables and nginx  

Layout:
- [ ] Remove bootstrap completely; use PrimeVue for spacing & grid & form
- [ ] Replace toaster with a real menu component: https://www.primefaces.org/primevue/showcase/#/menu
- [~] layout: Reduce space between tables by moving search & entries next to heading

Fixes:
- [ ] check dependency issues npm; remove package-lock.json and node_modules and do clean install

Static report:  // a server is always required 
- Remove/Fix websocket calls
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

## Deployment
- [ ] FIXME: fix sbmlimport error in orchestration
- [ ] FIXME: hardcoded backend urls in frontend (-> env variables)
- [ ] FIMXE: caching of requirements.txt and npm packages
- [ ] FIXME: test on server


