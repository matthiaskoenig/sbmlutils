- [x] cleanup state variables (naming variables, ...); see store
- [x] document in the README what technology/frameworks are used with links
- [x] static switch
- [x] load examples from backend
- [x] add medium size examples (ICG)
- [x] use better color schemes: https://colorbrewer2.org
  https://colorbrewer2.org/#type=diverging&scheme=RdYlBu&n=9
  to color components; just small color patch at begining
- [x] remove "View Details" -> just make work on click  
- [x] SBases instead of "List of SBases", Compartments
- [x] Add all SBases to the Lists; make a scrollable list with fixed max length
- [x] make list much more compact; single list
- [x] make a filter option for the ListOfSbases -> Multiple [Type] selection
- [x] make a search option on the list;
- Detail view 
  - [x] => just provide a list of all information
  - [x] only show XML; on click

List of existing problems:
 - [] ICG_BODY and ICG_BODY_FLAT doesn't load
        - Reason: Somehow the JSON response has been over stringified and is full of escape     characters. Removing the escape characters on the frontend doesn't help because then it cannot be JSON parsed again. 
        
        - Solution: ??

 - [] XML container doesn't let the report to load if the XML is too large (e.g. for Recon3D)
        - Reason: Most probably the time it takes to render the huge XML in the container is what causing the problem. 

        - Solution: ?? (maybe rendering the XML only when the button for View XML is clicked)

 - [] Search and Filter are slow (5-6 secs) on large models (e.g. Recon3D)
        - Reason: It takes too much time to check conditions for showing and hiding the huge list of SBases. 

        - Solution: ??

    
=> intercomponent navigation
