## TODO

- [~] Switch to some native Vue datatables (sorting, searching, filtering): https://www.primefaces.org/primevue/showcase/#/

Layout:
- [x] make `name` a subtitle in the DetailView
- [x] fix table navigation; on click should scroll to table
- [x] Table header replace "ListOf*" -> "*" e.g. ListOfCompartments -> Compartments  
- [x] hide tables if no results in global search  
- [x] re-add colors to navigation 
- [x] add count badges to the SBase navigation to get fast overview of number of components
- [x] icons for table sorting are missing
- [x] hide table & table navigation when switching visibility via toggle  
- [~] layout: Reduce space between tables by moving search & entries next to heading

Fixes:
- [x] fix: "Failed to resolve component: a-spin" warning on loading
- [ ] fix: "Query.Deferred exception: col is undefined DataTable" when loading models

- [ ] check dependency issues npm; remove package-lock.json and node_modules and do clean install

Static report:  // a server is always required 
- Remove/Fix websocket calls
- [~] create static report 
- [~] option for download static report
  
# ---------------------    
# MK:
## Annotations
- [ ] refactor backend annotation code into into separate package

## Units
- [ ] Unit math strings are not longer coming from backend
Improve generated latex (backend, MK)
- [] In components such as Parameters and Rules, units cannot be rendered in Katex as latex conversion is facing problems in the backend.
    - Reason: Most probably the cmathml (returned by the derived units function) is having xml prototypes, which is not being parsed by the cmathml_to_latex function. 
- [ ] update math string so it contains "sid = math"; eg. "a_tr = " (backend update math strings)

## Deployment

## OMEX
- [ ] Support of combine archives & resolve external model definitions
