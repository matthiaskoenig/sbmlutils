"""This module searches annotation terms from the ontology lookup service.

See https://www.ebi.ac.uk/ols/docs/api -> Search for documentation.

**Milestone 2.2 Develop backend functionality for the annotation search**
The frontend annotation query will be send to the python backend which will query the
various existing web services (Ontology Lookup Service, Bio Ontologies, AnnotateDB)
to fetch the ontology terms. Results will be processed/cached/ranked and returned to
the frontend as ranked results via the JSON annotation format.

TODO: Create a class which allows to search OLS via the REST API.
see for instance
https://www.ebi.ac.uk/ols/api/search?q=glucose


Do something similar for
https://data.bioontology.org/documentation -> Term search

-> (term_id, ontology, label, descriptions, synonyms, cross-references);

object.id, object.name, object.meta_id
"""



