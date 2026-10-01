"""The uncertainties of the distrib package.

`Uncertainty` with its `UncertParameter` and `UncertSpan`, which a
model definition attaches to an element with `uncertainties`.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

import libsbml

from sbmlutils.factory._core import (
    KeyValuePair,
    OptionalAnnotationsType,
    Sbase,
    _set_math,
)
from sbmlutils.factory.units import UnitDefinition, UnitType, _check_unit_type
from sbmlutils.notes import Notes
from sbmlutils.validation import check

logger = logging.getLogger(__name__)


class _UncertChild(Sbase):
    """The part an `UncertParameter` and an `UncertSpan` have in common.

    Both are children of the `distrib:listOfUncertParameters` of an
    uncertainty or of an uncert parameter, and both state what is known about
    a value: an `UncertParameter` states one value, an `UncertSpan` a lower
    and an upper bound. Everything else is the same on both and lives here:
    the `type` which says what the value is, the `unit` of the value, the
    `definitionURL` which names the distribution or the external parameter
    the element stands for, the `math` which states a distribution, and the
    uncert parameters and spans of its own, which an external distribution
    states its parameters as.

    Both are SBML `SBase` objects: libsbml writes and reads back `id`,
    `name`, `metaId`, `sboTerm`, notes, annotations and fbc key value pairs
    on a `distrib:uncertParameter` and a `distrib:uncertSpan`, so all of them
    are offered.

    The three `Sbase` fields which are written from the `libsbml.Model` are
    not offered, and passing one is a `TypeError` rather than a value which is
    accepted and dropped:

    - `uncertainties`: libsbml does attach a distrib plugin to an uncert
      parameter, but it then writes the `listOfUncertainties` twice, which
      makes the document invalid (`distrib-20201`, only one list is allowed).
      `uncertParameters` is how an uncert parameter holds children.
    - `port` and `replacedBy`: a comp port which references an uncert
      parameter is written as a `Port` of the model with an `idRef` or a
      `metaIdRef`, which is how the parser reads it back; the shorthand on the
      element would have to be written with the model, which the children of
      an uncertainty are not written with, see `_set_fields`.
    """

    #: the `distrib:type` values SBML allows on the element of this class
    _types: ClassVar[frozenset[int]] = frozenset()

    def __init__(
        self,
        type: int | None,
        unit: UnitType = None,
        definitionURL: str | None = None,
        math: str | None = None,
        uncertParameters: list[UncertParameter | UncertSpan] | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Construct the fields an uncert parameter and an uncert span share.

        Args:
            type: the kind of the value, a `libsbml.DISTRIB_UNCERTTYPE_*`;
                `None` for an element which states no `distrib:type`, which
                SBML requires and libsbml reads and writes without
            unit: the unit of the value
            definitionURL: the URL which defines the distribution or the
                external parameter the element stands for, e.g. a term of
                ProbOnto or the csymbol of a distribution of distrib
            math: the math of the element as an SBML L3 formula, which an
                uncert parameter of the type `distribution` states its
                distribution as
            uncertParameters: the uncert parameters and spans of the element,
                in the order they are written in; the parameters of an
                external distribution
            sid: the id of the element, which is optional in SBML
            name: the name of the element
            sboTerm: the SBO term of the element
            metaId: the meta id of the element, which its annotations are
                referenced by
            annotations: the annotations of the element
            notes: the notes of the element
            keyValuePairs: the fbc key value pairs of the element
        """
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )
        self.type: int | None = type
        self.unit: UnitType = unit
        self.definitionURL: str | None = definitionURL
        self.math: str | None = math
        self.uncertParameters: list[UncertParameter | UncertSpan] = (
            list(uncertParameters) if uncertParameters else []
        )
        _check_unit_type(self.unit, "unit", self)
        self._check_states_a_value()

    def __str__(self) -> str:
        """Get string representation.

        `Sbase.__str__` lists the `Sbase` fields, which are all optional on a
        child of an uncertainty and empty on most of them. The messages which
        name the element are only useful with its type and its value, which is
        what `__repr__` prints, so both representations are the same here.
        """
        return repr(self)

    def _states_a_value(self) -> bool:
        """Test whether the element states anything about the value.

        Returns:
            whether the element has a value, a variable it reads the value
            from, a definitionURL, math, or uncert parameters of its own
        """
        return bool(
            self.definitionURL is not None
            or self.math is not None
            or self.uncertParameters
        )

    def _check_states_a_value(self) -> None:
        """Report an element which states nothing about the value.

        SBML requires neither a value nor anything else of an uncert
        parameter, and libsbml reads and validates an element which states
        nothing, so this is reported rather than refused: the parser has to be
        able to hold every document libsbml reads.

        This is a hint about a hand written element, so it is silent inside
        `Sbase.no_authoring_hints`, which is what `_distribution_parameter`
        builds its parameter in: the caller which knows why the element states
        nothing says it precisely instead.
        """
        if Sbase._authoring_hints.get() and not self._states_a_value():
            logger.error(
                "'%s' states nothing about the value: none of 'value', 'var', "
                "'definitionURL', 'math' and 'uncertParameters' is set.",
                self,
            )

    def _supports_type(self) -> bool:
        """Test whether SBML allows the type of the element on it.

        A span states an interval and a parameter a single value, so the types
        of the two are disjoint; a type of the other element, or no type of
        distrib at all, is reported and the element is not written, since
        libsbml would write an element SBML does not define.

        An element which states no type at all is written as it is: SBML
        requires a `distrib:type` and libsbml reads an element without one,
        which the round trip of such a document has to write back as it was.
        The missing attribute is reported by the validation of the written
        document, as it is for the document it was read from.

        Returns:
            whether the element is written
        """
        if self.type is None or self.type in self._types:
            return True
        logger.error(
            "Unsupported type for %s: '%s' in '%s'.",
            type(self).__name__,
            self.type,
            self,
        )
        return False

    def _set_fields(self, sbase: Any, model: libsbml.Model) -> None:
        """Set the shared fields on the created libsbml object.

        `sbase` is declared `Any` for the reason `Sbase._set_fields` declares
        it `Any`: each subclass narrows it to the one libsbml type it creates,
        and a `libsbml.UncertParameter` here would make the `libsbml.UncertSpan`
        of `UncertSpan._set_fields` an LSP violation.

        Args:
            sbase: the libsbml.UncertParameter or libsbml.UncertSpan created
                by `create_sbml`
            model: the libsbml.Model the uncertainty is created in, which the
                math of the child is parsed against; handed down, never
                looked up, see `Model._fill_sbml`. It is never passed on to
                `Sbase._set_fields`, which gets `None`: that is what keeps it
                from descending into the `uncertainties` and the comp fields
                of a child.
        """
        super()._set_fields(sbase, None)
        if self.type is not None:
            check(sbase.setType(self.type), f"Set type '{self.type}' on {sbase}")
        if self.definitionURL is not None:
            check(
                sbase.setDefinitionURL(self.definitionURL),
                f"Set definitionURL '{self.definitionURL}' on {sbase}",
            )
        _set_math(sbase, self.math, model)
        if self.unit:
            uid = UnitDefinition.get_uid_for_unit(unit=self.unit)
            check(sbase.setUnits(uid), f"Set unit '{uid}' on {sbase}")

        child: UncertParameter | UncertSpan
        for child in self.uncertParameters:
            child.create_sbml(sbase, model)


class UncertParameter(_UncertChild):
    """A single value of an `Uncertainty`, e.g. a mean or a standard deviation.

    The value is either a number (`value`), a reference to a parameter of the
    model (`var`), or, for an uncert parameter of the type `distribution`, the
    distribution the value is drawn from, as `math` or as a `definitionURL`
    with the `uncertParameters` of the distribution. The `type` states which of
    them it is, e.g. `libsbml.DISTRIB_UNCERTTYPE_MEAN`.

    The fields it shares with an `UncertSpan`, and the fields neither of them
    offers, are documented in `_UncertChild`.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    _types: ClassVar[frozenset[int]] = frozenset(
        {
            libsbml.DISTRIB_UNCERTTYPE_COEFFIENTOFVARIATION,
            libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION,
            libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER,
            libsbml.DISTRIB_UNCERTTYPE_KURTOSIS,
            libsbml.DISTRIB_UNCERTTYPE_MEAN,
            libsbml.DISTRIB_UNCERTTYPE_MEDIAN,
            libsbml.DISTRIB_UNCERTTYPE_MODE,
            libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE,
            libsbml.DISTRIB_UNCERTTYPE_SKEWNESS,
            libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
            libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR,
            libsbml.DISTRIB_UNCERTTYPE_VARIANCE,
        }
    )

    def __init__(
        self,
        type: int | None,
        value: float | None = None,
        var: str | None = None,
        unit: UnitType = None,
        definitionURL: str | None = None,
        math: str | None = None,
        uncertParameters: list[UncertParameter | UncertSpan] | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Construct UncertParameter.

        Args:
            type: the kind of the value, a `libsbml.DISTRIB_UNCERTTYPE_*`,
                `None` for an element without one, see `_UncertChild`
            value: the numerical value
            var: the id of the element which holds the value, an alternative
                to `value`
            unit: the unit of the value
            definitionURL: see `_UncertChild`
            math: see `_UncertChild`
            uncertParameters: see `_UncertChild`
            sid: the id of the uncert parameter, which is optional in SBML
            name: the name of the uncert parameter
            sboTerm: the SBO term of the uncert parameter
            metaId: the meta id of the uncert parameter, which its annotations
                are referenced by
            annotations: the annotations of the uncert parameter
            notes: the notes of the uncert parameter
            keyValuePairs: the fbc key value pairs of the uncert parameter
        """
        # before `super().__init__`, which checks and reports what the
        # element states, through the `_states_a_value` of this class
        self.value: float | None = value
        self.var: str | None = var
        super().__init__(
            type=type,
            unit=unit,
            definitionURL=definitionURL,
            math=math,
            uncertParameters=uncertParameters,
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )

    def __repr__(self) -> str:
        """Get string representation."""
        value = self.value if self.value is not None else self.var
        return f"UncertParameter({self.type}, {value} [{self.unit}])"

    def _states_a_value(self) -> bool:
        """Test whether the uncert parameter states anything about the value."""
        return (
            self.value is not None or self.var is not None or super()._states_a_value()
        )

    def create_sbml(
        self,
        parent: libsbml.Uncertainty | libsbml.UncertParameter,
        model: libsbml.Model,
    ) -> libsbml.UncertParameter | None:
        """Create the libsbml.UncertParameter in the given parent.

        Args:
            parent: the libsbml.Uncertainty or libsbml.UncertParameter the
                parameter is created in
            model: the libsbml.Model the uncertainty is created in, which the
                math is parsed against, see `_UncertChild._set_fields`

        Returns:
            the created libsbml.UncertParameter, `None` for a parameter whose
            type SBML does not allow on one, see `_supports_type`
        """
        if not self._supports_type():
            return None
        up: libsbml.UncertParameter = parent.createUncertParameter()
        self._set_fields(up, model)
        return up

    def _set_fields(self, sbase: libsbml.UncertParameter, model: libsbml.Model) -> None:
        """Set the fields on the libsbml.UncertParameter.

        Args:
            sbase: the libsbml.UncertParameter created by `create_sbml`
            model: the model the math is parsed against, see
                `_UncertChild._set_fields`
        """
        super()._set_fields(sbase, model)
        if self.value is not None:
            check(sbase.setValue(self.value), f"Set value '{self.value}' on {sbase}")
        if self.var is not None:
            check(sbase.setVar(self.var), f"Set var '{self.var}' on {sbase}")


class UncertSpan(_UncertChild):
    """An interval of an `Uncertainty`, e.g. a range or a confidence interval.

    Both bounds are either a number (`valueLower`, `valueUpper`) or a
    reference to a parameter of the model (`varLower`, `varUpper`), and the
    `type` states what the interval is, e.g.
    `libsbml.DISTRIB_UNCERTTYPE_RANGE`.

    An uncert span carries the same fields as an `UncertParameter`, which it
    is a subclass of in libsbml: it is written with `createUncertSpan` and
    read back from the `listOfUncertParameters`. The shared fields, and the
    fields neither class offers, are documented in `_UncertChild`.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    _types: ClassVar[frozenset[int]] = frozenset(
        {
            libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
            libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL,
            libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE,
            libsbml.DISTRIB_UNCERTTYPE_RANGE,
        }
    )

    def __init__(
        self,
        type: int | None,
        valueLower: float | None = None,
        varLower: str | None = None,
        valueUpper: float | None = None,
        varUpper: str | None = None,
        unit: UnitType = None,
        definitionURL: str | None = None,
        math: str | None = None,
        uncertParameters: list[UncertParameter | UncertSpan] | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Construct UncertSpan.

        Args:
            type: the kind of the interval, a `libsbml.DISTRIB_UNCERTTYPE_*`,
                `None` for an element without one, see `_UncertChild`
            valueLower: the numerical value of the lower bound
            varLower: the id of the element which holds the lower bound, an
                alternative to `valueLower`
            valueUpper: the numerical value of the upper bound
            varUpper: the id of the element which holds the upper bound, an
                alternative to `valueUpper`
            unit: the unit of the bounds
            definitionURL: see `_UncertChild`
            math: see `_UncertChild`
            uncertParameters: see `_UncertChild`
            sid: the id of the uncert span, which is optional in SBML
            name: the name of the uncert span
            sboTerm: the SBO term of the uncert span
            metaId: the meta id of the uncert span, which its annotations are
                referenced by
            annotations: the annotations of the uncert span
            notes: the notes of the uncert span
            keyValuePairs: the fbc key value pairs of the uncert span
        """
        # before `super().__init__`, which checks and reports the bounds
        # through the `_check_states_a_value` of this class
        self.valueLower: float | None = valueLower
        self.varLower: str | None = varLower
        self.valueUpper: float | None = valueUpper
        self.varUpper: str | None = varUpper
        super().__init__(
            type=type,
            unit=unit,
            definitionURL=definitionURL,
            math=math,
            uncertParameters=uncertParameters,
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )

    def __repr__(self) -> str:
        """Get string representation."""
        lower = self.valueLower if self.valueLower is not None else self.varLower
        upper = self.valueUpper if self.valueUpper is not None else self.varUpper
        return f"UncertSpan({self.type}, {lower} - {upper} [{self.unit}])"

    def _states_a_value(self) -> bool:
        """Test whether the uncert span states anything about its bounds."""
        return (
            self.valueLower is not None
            or self.varLower is not None
            or self.valueUpper is not None
            or self.varUpper is not None
            or super()._states_a_value()
        )

    def _check_states_a_value(self) -> None:
        """Report every bound of the span which is not stated.

        A span states an interval, so each of its two bounds needs either a
        value or the variable it is read from. The check of `_UncertChild`
        only sees whether the element states anything at all, which a span
        with one bound does; both are named here instead, which is what the
        constructor refused before an element of every document libsbml reads
        had to be expressible.

        A span which states its interval as math, as the definitionURL of an
        external distribution or as uncert parameters of its own needs neither
        bound, and nothing is reported for it.
        """
        if not Sbase._authoring_hints.get() or super()._states_a_value():
            return
        for bound, value, var in (
            ("lower", self.valueLower, self.varLower),
            ("upper", self.valueUpper, self.varUpper),
        ):
            if value is None and var is None:
                logger.error(
                    "The %s bound of '%s' is not stated: neither 'value%s' nor "
                    "'var%s' is set.",
                    bound,
                    self,
                    bound.capitalize(),
                    bound.capitalize(),
                )

    def create_sbml(
        self,
        parent: libsbml.Uncertainty | libsbml.UncertParameter,
        model: libsbml.Model,
    ) -> libsbml.UncertSpan | None:
        """Create the libsbml.UncertSpan in the given parent.

        Args:
            parent: the libsbml.Uncertainty or libsbml.UncertParameter the
                span is created in
            model: the libsbml.Model the uncertainty is created in, which the
                math is parsed against, see `_UncertChild._set_fields`

        Returns:
            the created libsbml.UncertSpan, `None` for a span whose type SBML
            does not allow on one, see `_supports_type`
        """
        if not self._supports_type():
            return None
        span: libsbml.UncertSpan = parent.createUncertSpan()
        self._set_fields(span, model)
        return span

    def _set_fields(self, sbase: libsbml.UncertSpan, model: libsbml.Model) -> None:
        """Set the fields on the libsbml.UncertSpan.

        Args:
            sbase: the libsbml.UncertSpan created by `create_sbml`
            model: the model the math is parsed against, see
                `_UncertChild._set_fields`
        """
        super()._set_fields(sbase, model)
        if self.valueLower is not None:
            check(
                sbase.setValueLower(self.valueLower),
                f"Set valueLower '{self.valueLower}' on {sbase}",
            )
        if self.valueUpper is not None:
            check(
                sbase.setValueUpper(self.valueUpper),
                f"Set valueUpper '{self.valueUpper}' on {sbase}",
            )
        if self.varLower is not None:
            check(
                sbase.setVarLower(self.varLower),
                f"Set varLower '{self.varLower}' on {sbase}",
            )
        if self.varUpper is not None:
            check(
                sbase.setVarUpper(self.varUpper),
                f"Set varUpper '{self.varUpper}' on {sbase}",
            )


#: the start of the `definitionURL` of every distribution of distrib
_DISTRIBUTION_URL: str = "http://www.sbml.org/sbml/symbols/distrib/"

#: the distributions of distrib, which `Uncertainty.formula` names one of
_DISTRIBUTIONS: tuple[str, ...] = (
    "normal",
    "uniform",
    "bernoulli",
    "binomial",
    "cauchy",
    "chisquare",
    "exponential",
    "gamma",
    "laplace",
    "lognormal",
    "poisson",
    "rayleigh",
)


def _distribution_parameter(formula: str) -> UncertParameter:
    """Build the uncert parameter the `formula` of an uncertainty is written as.

    Which distribution the formula draws from is decided on the parsed
    formula, the name of the function it calls at the top level: libsbml
    parses every distribution of distrib into an AST node of its own, whose
    name is the name of the distribution. The name cannot be searched for in
    the text of the formula, which is what this did: `lognormal(0, 1)`
    contains `normal`, and so does an identifier like `normalization`.

    A formula which is not a call of a distribution is written as the uncert
    parameter of the type `distribution` it has always been written as,
    without a `definitionURL` and without math, and is reported: the shortcut
    has no way to express it, and the generic check of `_UncertChild` would
    only say that the parameter states nothing, which this says precisely.
    The math itself is parsed again when it is written, by `_set_math` with
    the model of the document, which resolves the ids of the formula.

    Args:
        formula: the distribution of the value as an SBML L3 formula, e.g.
            `normal(2.0, 2.0)`

    Returns:
        an uncert parameter of the type `distribution`: with the
        `definitionURL` of the distribution the formula calls and the formula
        as its math, or, for a formula which calls none, with neither
    """
    distribution: str | None = None
    ast: libsbml.ASTNode | None = libsbml.parseL3Formula(formula)
    if ast is None:
        reason: str = libsbml.getLastParseL3Error().strip() or "empty formula"
        logger.error(
            "The formula '%s' of an uncertainty could not be parsed: %s",
            formula,
            reason,
        )
    elif ast.isFunction() and ast.getName() in _DISTRIBUTIONS:
        distribution = str(ast.getName())

    if distribution is None:
        if ast is not None:
            logger.error(
                "The formula '%s' of an uncertainty is not a call of a "
                "distribution of distrib (%s), so the uncert parameter of the "
                "uncertainty is written without a definitionURL and without "
                "math.",
                formula,
                ", ".join(_DISTRIBUTIONS),
            )
        # the parameter states nothing about the value, which the message
        # above says more precisely than `_UncertChild._check_states_a_value`
        with Sbase.no_authoring_hints():
            return UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION)

    return UncertParameter(
        type=libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION,
        definitionURL=f"{_DISTRIBUTION_URL}{distribution}",
        math=formula,
    )


class Uncertainty(Sbase):
    """The uncertainty of the value of an element, a `distrib:uncertainty`.

    An uncertainty states what is known about a value beyond the value
    itself: a mean with a standard deviation, a range, a confidence interval,
    or the distribution the value is drawn from. Every `Sbase` can carry a
    list of them.

    SBML holds the values of an uncertainty in one list, the
    `distrib:listOfUncertParameters`, whose elements are
    `distrib:uncertParameter` and `distrib:uncertSpan`, and
    `uncertParameters` is that list: it takes `UncertParameter` and
    `UncertSpan` objects and is written in its own order, which is how the
    order of a parsed document is preserved.

    `uncertSpans` is the authoring style of two lists, one per kind, and is
    kept. It has no place for an order between the two, so its spans are put
    in front of `uncertParameters`, which is the order such an uncertainty has
    always been written in.

    `formula` is the shortcut for a distribution: it is normalized into one
    `UncertParameter` of the type `distribution` when the uncertainty is
    constructed, see `_distribution_parameter`, and appended after the
    children given explicitly. An uncertainty is written from
    `uncertParameters` and from nothing else, so a parsed uncertainty, which
    carries the distribution as an ordinary child, is written exactly once.

    libsbml attaches no `CompSBasePlugin` to a `<distrib:uncertainty>`, so a
    `replacedBy` is not offered, see `Sbase.create_replaced_by`.
    """

    def __init__(
        self,
        sid: str | None = None,
        formula: str | None = None,
        uncertParameters: list[UncertParameter | UncertSpan] | None = None,
        uncertSpans: list[UncertSpan] | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
    ):
        """Construct Uncertainty.

        Args:
            sid: the id of the uncertainty, which is optional in SBML
            formula: the distribution of the value as an SBML L3 formula,
                e.g. `normal(2.0, 2.0)`; the shortcut for the uncert parameter
                of the type `distribution` it is normalized into
            uncertParameters: the uncert parameters and spans of the
                uncertainty, in the order they are written in
            uncertSpans: the spans of the uncertainty, which are written
                before `uncertParameters`
            name: the name of the uncertainty
            sboTerm: the SBO term of the uncertainty
            metaId: the meta id of the uncertainty, which its annotations are
                referenced by
            annotations: the annotations of the uncertainty
            notes: the notes of the uncertainty
            keyValuePairs: the fbc key value pairs of the uncertainty
            port: the comp port of the uncertainty
        """
        super().__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
        )

        self.uncertParameters: list[UncertParameter | UncertSpan] = [
            *(uncertSpans if uncertSpans else []),
            *(uncertParameters if uncertParameters else []),
        ]
        #: the parameter the current `formula` was normalized into, which an
        #: assignment to `formula` replaces; `None` for an uncertainty
        #: without a formula
        self._formula_parameter: UncertParameter | None = None
        self._formula: str | None = None
        self.formula = formula

    @property
    def formula(self) -> str | None:
        """Get the distribution of the value as an SBML L3 formula.

        Returns:
            the formula, `None` for an uncertainty which states none
        """
        return self._formula

    @formula.setter
    def formula(self, formula: str | None) -> None:
        """Normalize a formula into the uncert parameter it stands for.

        An uncertainty is written from `uncertParameters` and from nothing
        else, so the shortcut is normalized into one parameter of the type
        `distribution`, see `_distribution_parameter`. It is a property so
        that a formula assigned after the uncertainty was constructed is
        written: the assignment replaces the parameter of the formula it
        replaces, in its place, and leaves every other child alone. Without
        it the value assigned was kept and never written, and the
        distribution given first was written instead, in silence.

        Args:
            formula: the distribution of the value as an SBML L3 formula,
                e.g. `normal(2.0, 2.0)`; `None` or the empty string removes
                the parameter of the formula which was set before
        """
        self._formula = formula
        previous = self._formula_parameter
        parameter = _distribution_parameter(formula) if formula else None
        self._formula_parameter = parameter

        if previous is None:
            if parameter is not None:
                self.uncertParameters.append(parameter)
            return
        position = self.uncertParameters.index(previous)
        if parameter is None:
            del self.uncertParameters[position]
        else:
            self.uncertParameters[position] = parameter

    def __repr__(self) -> str:
        """Get the string representation of the uncertainty.

        `Sbase.__str__` of the element which carries the uncertainties prints
        the list of them, and a list prints its items with `repr`, so without
        this a message which names that element puts the address of the
        uncertainty in front of a user.

        Returns:
            the id of the uncertainty, if it has one, and its children
        """
        sid = f"{self.sid}, " if self.sid else ""
        children = ", ".join(repr(child) for child in self.uncertParameters)
        return f"Uncertainty({sid}{children})"

    def create_sbml(
        self, sbase: libsbml.SBase, model: libsbml.Model
    ) -> libsbml.Uncertainty:
        """Create the libsbml.Uncertainty on the given element.

        Args:
            sbase: the libsbml object the uncertainty is created on
            model: the libsbml.Model the element belongs to

        Returns:
            the created libsbml.Uncertainty
        """
        sbase_distrib: libsbml.DistribSBasePlugin = sbase.getPlugin("distrib")
        uncertainty: libsbml.Uncertainty = sbase_distrib.createUncertainty()

        self._set_fields(uncertainty, model)
        self.create_port(model)

        child: UncertParameter | UncertSpan
        for child in self.uncertParameters:
            child.create_sbml(uncertainty, model)

        return uncertainty
