"""Distrib example demonstrating distributions."""
from pathlib import Path

from rich import print

from sbmlutils.examples import templates
from sbmlutils.factory import *


_m0 = Model(
    "model_no_distrib",
    name="Model sampling from distrib distributions",
    packages=["distrib"],
    creators=templates.creators,
    notes=(
        """
    # Distrib example
    Example creating distrib model with distribution elements.
    """
        + templates.terms_of_use
    ),
    parameters=[
        Parameter("p_1", 0),
    ],
)

_m1 = Model(
    "model_normal",
    name="Model sampling from distrib distributions",
    packages=["distrib"],
    creators=templates.creators,
    notes=(
        """
    # Distrib example
    Example creating distrib model with normal distribution.
    """
        + templates.terms_of_use
    ),
    assignments=[
        InitialAssignment("p_normal_1", "normal(0, 1)"),
    ],
)

_m2 = Model(
    "model_distrib",
    name="Model sampling from distrib distributions",
    packages=["distrib"],
    creators=templates.creators,
    notes=(
        """
    # Distrib example
    Example creating distrib model with distribution elements.
    """
        + templates.terms_of_use
    ),
    assignments=[
        InitialAssignment("p_normal_1", "normal(0, 1)"),
        InitialAssignment("p_normal_2", "normal(0, 1, 0, 10)"),
        InitialAssignment("p_uniform", "uniform(5, 10)"),
        InitialAssignment("p_bernoulli", "bernoulli(10)"),
        # InitialAssignment("p_binomial_1", "binomial(100, 0.3)"),
        # InitialAssignment("p_binomial_2", "binomial(100, 0.3, 0, 2)"),
        InitialAssignment("p_cauchy_1", "cauchy(0, 1)"),
        InitialAssignment("p_cauchy_2", "cauchy(0, 1, 0, 5)"),
        InitialAssignment("p_chisquare_1", "chisquare(10)"),
        InitialAssignment("p_chisquare_2", "chisquare(10, 0, 10)"),
        InitialAssignment("p_exponential_1", "exponential(1.0)"),
        InitialAssignment("p_exponential_2", "exponential(1.0, 0, 10)"),
        InitialAssignment("p_gamma_1", "gamma(0, 1)"),
        InitialAssignment("p_gamma_2", "gamma(0, 1, 0, 10)"),
        InitialAssignment("p_laplace_1", "laplace(0, 1)"),
        InitialAssignment("p_laplace_2", "laplace(0, 1, 0, 10)"),
        InitialAssignment("p_lognormal_1", "lognormal(0, 1)"),
        InitialAssignment("p_lognormal_2", "lognormal(0, 1, 0, 10)"),
        InitialAssignment("p_poisson_1", "poisson(0.5)"),
        InitialAssignment("p_poisson_2", "poisson(0.5, 0, 10)"),
        InitialAssignment("p_raleigh_1", "rayleigh(0.5)"),
        InitialAssignment("p_raleigh_2", "rayleigh(0.5, 0, 10)"),
    ],
)

_m3 = Model(
    "model_binomial",
    name="Model sampling from distrib distributions",
    packages=["distrib"],
    creators=templates.creators,
    notes=(
        """
    # Distrib example
    Example creating distrib model with distribution elements.
    """
        + templates.terms_of_use
    ),
    assignments=[
        InitialAssignment("p_binomial_1", "binomial(100, 0.3)"),
        InitialAssignment("p_binomial_2", "binomial(100, 0.3, 0, 2)"),
    ],
)


if __name__ == "__main__":
    for m in [_m0, _m1, _m2, _m3]:
        fac_result = create_model(
            models=m,
            output_dir=Path(__file__).parent,
            units_consistency=False,
        )
        print(fac_result.sbml_path)
