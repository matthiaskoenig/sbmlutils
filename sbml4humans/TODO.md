## TODO

- [ ] make all images responsive via simple PrimeVue solution
- [ ] OrderList for examples; remove buttons; remove all CSS from examples; remove toaster css/remove toaster  
- [ ] render uncertainty nicer (currently only list)
- [x] make tables more compact
- [ ] think about strategy for supporting reports: https://github.com/matthiaskoenig/sbmlutils/issues/257

  Probably migrating datatables for now (some minor bugs exist)
- [x] Remove JS dependencies: datatables, jquery, bootstap
- [x] Remove bootstrap completely; use PrimeVue for spacing & grid & form
- [~] Replace toaster with a real menu component: https://www.primefaces.org/primevue/showcase/#/menu

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



