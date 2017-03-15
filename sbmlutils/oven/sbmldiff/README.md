# SBML diff
Calculate the difference between two XML files.
Brings the XML elements in a canonical order (striped via annotations and notes),
which allows displaying the difference with diff.

- calculation of unique hash.

See also
- XML normalization 
- Canonical XML
http://stackoverflow.com/questions/22959577/python-exclusive-xml-canonicalization-xml-exc-c14n


http://www.ibm.com/developerworks/library/x-c14n/
XML is careful to separate details of a file or other data source, bit-by-bit, from the abstract model of an XML document. This can be an inconvenience when comparing two XML documents for equality -- either directly (for instance, as part of a test suite) or by comparing digital signatures for security purposes -- to determine whether an XML document has been tampered with in some way. The W3C addresses this problem with the XML Canonicalization spec (c14n), which defines a standard form for an XML document that is guaranteed to provide proper bit-wise comparisons and thus consistent digital signatures. 

In addition sort the elements
- remove the annotations and units.