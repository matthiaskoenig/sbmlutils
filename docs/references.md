# References

`sbmlutils` implements the specifications of the Systems Biology Markup Language. These are the publications behind the language and behind the packages the library supports; cite them when you describe a model, and cite `sbmlutils` itself as described in [Home](index.md#how-to-cite).

## SBML

**SBML Level 3.** The format and the package mechanism which the whole library builds on.

> Keating SM, Waltemath D, König M, Zhang F, Dräger A, Chaouiya C, Bergmann FT, Finney A, Gillespie CS, Helikar T, Hoops S, Malik-Sheriff RS, Moodie SL, Moraru II, Myers CJ, Naldi A, Olivier BG, Sahle S, Schaff JC, Smith LP, Swat MJ, Thieffry D, Watanabe L, Wilkinson DJ, Blinov ML, Begley K, Faeder JR, Gómez HF, Hamm TM, Inagaki Y, Liebermeister W, Lister AL, Lucio D, Mjolsness E, Proctor CJ, Raman K, Rodriguez N, Shaffer CA, Shapiro BE, Stelling J, Swainston N, Tanimura N, Wagner J, Meier-Schellersheim M, Sauro HM, Palsson B, Bolouri H, Kitano H, Funahashi A, Hermjakob H, Doyle JC, Hucka M; SBML Level 3 Community members.
> **SBML Level 3: an extensible format for the exchange and reuse of biological models.**
> *Molecular Systems Biology.* 2020 Aug;16(8):e9110.
> [doi:10.15252/msb.20199110](https://doi.org/10.15252/msb.20199110) · PMID: [32845085](https://pubmed.ncbi.nlm.nih.gov/32845085/) · PMCID: [PMC8411907](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8411907/)

**SBML Level 3 Version 2 Core.** The language specification itself, i.e., what a compartment, a species, a reaction, a rule and an event mean. See [Model creation](creation.md).

> Hucka M, Bergmann FT, Chaouiya C, Dräger A, Hoops S, Keating SM, König M, Novère NL, Myers CJ, Olivier BG, Sahle S, Schaff JC, Sheriff R, Smith LP, Waltemath D, Wilkinson DJ, Zhang F.
> **The Systems Biology Markup Language (SBML): Language Specification for Level 3 Version 2 Core Release 2.**
> *Journal of Integrative Bioinformatics.* 2019 Jun 20;16(2):20190021.
> [doi:10.1515/jib-2019-0021](https://doi.org/10.1515/jib-2019-0021) · PMID: [31219795](https://pubmed.ncbi.nlm.nih.gov/31219795/) · PMCID: [PMC6798823](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6798823/)

## SBML packages

**Flux balance constraints (fbc), version 3.** Flux bounds, objectives, gene products and user defined constraints. See [Flux balance constraints](fbc.md).

> Olivier BG, Bergmann FT, Keating S, König M.
> **SBML level 3 package: flux balance constraints version 3.**
> *Journal of Integrative Bioinformatics.* 2026 Aug 13. Epub ahead of print.
> [doi:10.1515/jib-2026-0006](https://doi.org/10.1515/jib-2026-0006) · PMID: [42590802](https://pubmed.ncbi.nlm.nih.gov/42590802/)

**Distributions (distrib), version 1.** Uncertainties on an element and distributions in a formula. See [Distributions and uncertainties](distrib.md).

> Smith LP, Moodie SL, Bergmann FT, Gillespie C, Keating SM, König M, Myers CJ, Swat MJ, Wilkinson DJ, Hucka M.
> **Systems Biology Markup Language (SBML) Level 3 Package: Distributions, Version 1, Release 1.**
> *Journal of Integrative Bioinformatics.* 2020 Jul 20;17(2-3):20200018.
> [doi:10.1515/jib-2020-0018](https://doi.org/10.1515/jib-2020-0018) · PMID: [32750035](https://pubmed.ncbi.nlm.nih.gov/32750035/) · PMCID: [PMC7756622](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7756622/)

## Specifications

The current specifications of the language and of every package are published at [sbml.org/documents/specifications](https://sbml.org/documents/specifications/), including the packages `sbmlutils` supports beyond the ones above: [comp](https://sbml.org/documents/specifications/level-3/version-1/comp/) for [model composition](comp.md) and [layout](https://sbml.org/documents/specifications/level-3/version-1/layout/) for the [layout information](visualization.md#the-sbml-layout-package) of a model.
