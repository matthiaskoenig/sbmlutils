"""Distrib example demonstrating distributions."""
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.validation import ValidationOptions


class U(Units):
    """UnitsDefinitions."""

    hr = UnitDefinition("hr")
    m2 = UnitDefinition("m2", "meter^2")


model = Model(
    "distrib_distributions",
    name="model with distrib distributions",
    packages=[Package.DISTRIB_V1],
    creators=templates.creators,
    notes="""
    # Distrib example

    Example creating distrib model with distribution elements.
    """
    + templates.terms_of_use,
    units=U,
    model_units=ModelUnits(
        time=U.hr,
        extent=U.mole,
        substance=U.mole,
        length=U.meter,
        area=U.m2,
        volume=U.liter,
    ),
)

model.assignments = [
    InitialAssignment("p_normal_1", "normal(0, 1)"),
    InitialAssignment("p_normal_2", "normal(0, 1, 0, 10)"),
    InitialAssignment("p_uniform", "uniform(5, 10)"),
    InitialAssignment("p_bernoulli", "bernoulli(10)"),
    InitialAssignment("p_binomial_1", "binomial(100, 0.3)"),
    InitialAssignment("p_binomial_2", "binomial(100, 0.3, 0, 2)"),
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
]


if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )
