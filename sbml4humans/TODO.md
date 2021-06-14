## TODO
- [x] `about` component providing information on the project (see https://pk-db.com/)
  - [x] project, team, license, funding, how to cite (link to repository)
- [x] remove file format and math rendering from landing page;
- [x] add tool tips for landing page
- [ ] add SId and Name to title of components: `<strong>UnitDefinition</strong> time (minute)`
- [x] remove examples & Upload SBML from navigation menu
- [ ] add logo: https://github.com/matthiaskoenig/sbmlutils/raw/develop/docs_builder/images/sbmlutils-logo-60.png
- [ ] add tooltips to links (navigation and other linking, e.g. `Show details`)
- [ ] update XML: make visible/invisible, do not use modal; don't show/load XML for model/SBMLDocument
- [x] start frontend on different port: > 3000; 3245
- [ ] figure out how to document components & document them (https://vue-styleguidist.github.io/docs/Documenting.html)
- [ ] use typescript; required tags on properties; (see XMLContainer for example), type annotations
- [ ] make the scss imports work (should be clickable in idea frontend; perhaps use `src` on style)
- [ ] in detailView use attribute names (no whitespaces)
Math rendering
- [ ] implement MathRendering using Katex; https://katex.org/ (npm install katex) -> send Latex




Filter
- [ ] more robust handling of state
- [x] select/deselct in filter should be button; all buttons should have same style in frontent (see submit)
- [ ] indicate on filter how much is filtered; `Filter`; `Filter (10/123)`
- [x] filter buttons without linestyle/or linestyle black
- [x] create component for filter object and create all filter objects via a `v-for` from
      list
- [x] name fields in `visibility` identical to SBMLType
- [.] simplify filter by just iterating over list of SBases --- implemented via visibility flag
- [ ] use a global set to track filtered/searched SBases via `pk`: What is currently selected!
Backend JSON:
- [x]  add pk in JSON -> use metaId/SId/uuid)
Frontend:
- [x] List of SBMLTypes: ["SBMLDocument", "Model", "UnitDefinition", ...]  
- [ ] use a global HashMap of all objects: <pk: SBaseJSON>: This allows to lookup Details very fast for pk
- [ ] use a global for component: <'reaction': List[pk]> --> pks['Reaction']: This allows to get pks for a certain component type

## List of existing problems:
 - [] Filter is slow (5-6 secs) on large models (e.g. Recon3D)
        - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
        - Solution: => refactor filter (see TODOs above)
   
- [] Search is slow (5-6 secs) on large models (e.g. Recon3D)
    - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases.
    - no solution for now -> switching to elasticsearch based on JSON in future
    
=> intercomponent navigation
