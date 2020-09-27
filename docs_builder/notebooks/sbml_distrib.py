#!/usr/bin/env python
# coding: utf-8

# ## SBML distrib
# The following examples demonstrate the creation of SBML models with SBML distrib information.

# In[1]:


get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# In[2]:


from notebook_utils import print_xml
from sbmlutils.units import *
from sbmlutils.factory import *

from sbmlutils.modelcreator.creator import CoreModel
from sbmlutils.validation import validate_doc


# ### Assigning a distribution to a parameter
# Here we create a parameter $$p_1 = 0.0$$ and assign the initial value from a normal distribution with `mean=0` and `standard deviation=1` 
# 
# $$p_1 = \sigma(0,1)$$

# In[3]:


model_dict = {
    'mid': 'distrib_assignment',
    'packages': ['distrib'],
    'model_units': ModelUnits(time=UNIT_hr, extent=UNIT_KIND_MOLE, substance=UNIT_KIND_MOLE,
                              length=UNIT_m, area=UNIT_m2, volume=UNIT_KIND_LITRE),
    'units': [UNIT_hr, UNIT_m, UNIT_m2, UNIT_mM],
    'parameters': [
        Parameter(sid="p1", value=0.0, unit=UNIT_mM)
    ],
    'assignments': [
        InitialAssignment('p1', 'normal(0 mM, 1 mM)'),
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Using a normal distribution
# In this example, the initial value of y is set as a draw from the normal distribution `normal(z,10)`:

# In[4]:


model_dict = {
    'mid': 'normal',
    'packages': ['distrib'],
    'parameters': [
        Parameter('y', value=1.0),
        Parameter('z', value=1.0),
    ],
    'assignments': [
        InitialAssignment('y', 'normal(z, 10)'),
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Defining a truncated normal distribution
# When used with four arguments instead of two, the normal distribution is truncated to `normal(z, 10, z-2, z+2)`. This use would apply a draw from a normal distribution with `mean z`, `standard deviation 10`, `lower bound z-2` (inclusive) and `upper bound z+2` (not inclusive) to the SBML symbol `y`.

# In[5]:


model_dict = {
    'mid': 'truncated_normal',
    'packages': ['distrib'],
    'parameters': [
        Parameter('y', value=1.0),
        Parameter('z', value=1.0),
    ],
    'assignments': [
        InitialAssignment('y', 'normal(z, 10, z-2, z+2)'),
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Defining conditional events 
# Simultaneous events in SBML are ordered based on their Priority values, with higher values being executed first, and potentially cancelling events that fire after them. In this example, two simultaneous events have priorities set with csymbols defined in distrib. The event `E0` has a priority of `uniform(0,1)`, while the event `E1` has a priority of `uniform(0,2)`. This means that 75% of the time, event `E1` will have a higher priority than `E0`, and will fire first, assigning a value of `5` to parameter `x`. Because this negates the trigger condition for `E0`, which is set `persistent="false"`, this means that `E0` never fires, and the value of `x` remains at `5`. The remaining 25% of the time, the reverse happens, with `E0` setting the value of `x` to `3` instead.

# In[6]:


model_dict = {
    'mid': 'conditional_events',
    'packages': ['distrib'],
    'parameters': [
        Parameter('x', value=1.0, constant=False)
    ],
    'events': [
        Event(
            "E0", 
            trigger="time>2 && x<1", 
            priority="uniform(0, 1)",
            trigger_initialValue=True, trigger_persistent=False,
            assignments={"x": "3"}
        ),
        Event(
            "E1", 
            trigger="time>2 && x<1", 
            priority="uniform(0, 2)",
            trigger_initialValue=True, trigger_persistent=False,
            assignments={"x": "5"}
        )
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Overview of all distributions
# The following gives an example how to use all of the various distributions

# In[7]:


model_dict = {
    'mid': 'all_distributions',
    'packages': ['distrib'],
    'assignments': [
        InitialAssignment('p_normal_1', 'normal(0, 1)'),
        InitialAssignment('p_normal_2', 'normal(0, 1, 0, 10)'),
        InitialAssignment('p_uniform', 'uniform(5, 10)'),
        InitialAssignment('p_bernoulli', 'bernoulli(0.4)'),
        InitialAssignment('p_binomial_1', 'binomial(100, 0.3)'),
        InitialAssignment('p_binomial_2', 'binomial(100, 0.3, 0, 2)'),
        InitialAssignment('p_cauchy_1', 'cauchy(0, 1)'),
        InitialAssignment('p_cauchy_2', 'cauchy(0, 1, 0, 5)'),
        InitialAssignment('p_chisquare_1', 'chisquare(10)'),
        InitialAssignment('p_chisquare_2', 'chisquare(10, 0, 10)'),
        InitialAssignment('p_exponential_1', 'exponential(1.0)'),
        InitialAssignment('p_exponential_2', 'exponential(1.0, 0, 10)'),
        InitialAssignment('p_gamma_1', 'gamma(0, 1)'),
        InitialAssignment('p_gamma_2', 'gamma(0, 1, 0, 10)'),
        InitialAssignment('p_laplace_1', 'laplace(0, 1)'),
        InitialAssignment('p_laplace_2', 'laplace(0, 1, 0, 10)'),
        InitialAssignment('p_lognormal_1', 'lognormal(0, 1)'),
        InitialAssignment('p_lognormal_2', 'lognormal(0, 1, 0, 10)'),
        InitialAssignment('p_poisson_1', 'poisson(0.5)'),
        InitialAssignment('p_poisson_2', 'poisson(0.5, 0, 10)'),
        InitialAssignment('p_raleigh_1', 'rayleigh(0.5)'),
        InitialAssignment('p_raleigh_2', 'rayleigh(0.5, 0, 10)'),
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Basic uncertainty example
# Here, the species with an initial amount of `3.22` is described as having a `standard deviation` of `0.3`, a value that might
# be written as `3.22 +- 0.3`.

# In[8]:


import libsbml
model_dict = {
    'mid': 'basic_example_1',
    'packages': ['distrib'],
    'compartments': [
        Compartment("C", value=1.0)
    ],
    'species': [
        Species(sid="s1", compartment="C", initialAmount=3.22, 
                uncertainties=[
                  Uncertainty(uncertParameters=[
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=0.3)
                  ])
                ])
    ],
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# It is also possible to include additional information about the species, should more be known. In this example, the initial amount of `3.22` is noted as having a mean of `3.2`, a standard deviation of `0.3`, and a variance
# of `0.09`.

# In[9]:


import libsbml
model_dict = {
    'mid': 'basic_example_2',
    'packages': ['distrib'],
    'compartments': [
        Compartment("C", value=1.0)
    ],
    'species': [
        Species(sid="s1", compartment="C", initialAmount=3.22, 
                uncertainties=[
                  Uncertainty(uncertParameters=[
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=3.2),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=0.3),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_VARIANCE, value=0.09),
                  ])
                ])
    ],
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Multiple uncertainties
# The following gives an example how to encode multiple uncertainties for a parameter.
# Here the two uncertainties 
# `5.0 (mean) +- 0.3 (std) [2.0 - 8.0]` 
# and 
# `4.5 (mean) +- 1.1 (std) [1.0 - 10.0]` 
# are set.

# In[10]:


import libsbml
model_dict = {
    'mid': 'multiple_uncertainties',
    'packages': ['distrib'],
    'model_units': ModelUnits(time=UNIT_hr, extent=UNIT_KIND_MOLE, substance=UNIT_KIND_MOLE,
                              length=UNIT_m, area=UNIT_m2, volume=UNIT_KIND_LITRE),
    'units': [UNIT_hr, UNIT_m, UNIT_m2, UNIT_mM],
    'parameters': [
        Parameter(sid="p1", value=5.0, unit=UNIT_mM, 
                  uncertainties=[
                      Uncertainty('p1_uncertainty_1', uncertParameters=[
                          UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=5.0, unit=UNIT_mM),
                          UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=0.3, unit=UNIT_mM),
                          UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_RANGE, valueLower=2.0, valueUpper=8.0, unit=UNIT_mM),
                      ]),
                      Uncertainty('p1_uncertainty_2', uncertParameters=[
                          UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=4.5, unit=UNIT_mM),
                          UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=1.1, unit=UNIT_mM),
                          UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_RANGE, valueLower=1.0, valueUpper=10.0, unit=UNIT_mM),
                      ])
                  ])
    ],
    'assignments': [
        InitialAssignment('p1', 'normal(0 mM, 1 mM)'),
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Defining a random variable
# In addition to describing the uncertainty about an experimental observation one can also use this mechanism
# to describe a parameter as a random variable.

# In[11]:


import libsbml
model_dict = {
    'mid': 'random_variable',
    'packages': ['distrib'],
    'parameters': [
        Parameter("shape_Z", value=10.0),
        Parameter("scale_Z", value=0.1),
        Parameter("Z", value=0.1,
                  uncertainties=[
                      Uncertainty(formula="gamma(shape_Z, scale_Z)",
                                  uncertParameters=[
                                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=1.03),
                                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_VARIANCE, value=0.97),
                                  ])
                  ])
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Overview over UncertParameters and UncertSpans
# The following example provides an overview over the available fields.

# In[12]:


import libsbml
model_dict = {
    'mid': 'parameters_spans',
    'packages': ['distrib'],
    'parameters': [
        Parameter("p",
          uncertainties=[
              Uncertainty(
                  formula="normal(0, 1)",  # distribution
                  uncertParameters=[
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_COEFFIENTOFVARIATION, value=1.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_KURTOSIS, value=2.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=3.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEDIAN, value=4.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MODE, value=5.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE, value=6.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_SKEWNESS, value=7.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=8.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR, value=9.0),
                      UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_VARIANCE, value=10.0),
                      UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL, valueLower=1.0, valueUpper=2.0),
                      UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL, valueLower=2.0, valueUpper=3.0),
                      UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE, valueLower=3.0, valueUpper=4.0),
                      UncertSpan(type=libsbml.DISTRIB_UNCERTTYPE_RANGE, valueLower=4.0, valueUpper=5.0),
                  ])
          ])
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
validate_doc(core_model.doc, units_consistency=False);


# ### Information on experimental parameters (SABIO-RK)
# In the following example we store the experimental information which was used for setting the parameter in the model.

# In[13]:


import libsbml
from sbmlutils.annotation import *
model_dict = {
    'mid': 'sabiork_parameter',
    'packages': ['distrib'],
    'model_units': ModelUnits(time=UNIT_hr, extent=UNIT_KIND_MOLE,
                              substance=UNIT_KIND_MOLE,
                              length=UNIT_m, area=UNIT_m2,
                              volume=UNIT_KIND_LITRE),
    'units': [UNIT_hr, UNIT_m, UNIT_m2, UNIT_mM],
    'parameters': [
        Parameter(
            sid="Km_glc", name="Michelis-Menten constant glucose",
            value=5.0, unit=UNIT_mM, sboTerm=SBO_MICHAELIS_CONSTANT,
            uncertainties=[
                Uncertainty(
                  sid="uncertainty1",
                  uncertParameters=[
                      UncertParameter(
                          type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                          value=5.07),
                      UncertParameter(
                          type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                          value=0.97),
                  ], annotations=[
                        (BQB.IS, "sabiork.kineticrecord/793"),  # entry in SABIO-RK
                        (BQB.HAS_TAXON, "taxonomy/9606"),  # homo sapiens
                        (BQB.IS, "ec-code/2.7.1.2"),  # glucokinase
                        (BQB.IS, "uniprot/P35557"),  # Glucokinase homo sapiens
                        (BQB.IS, "bto/BTO:0000075"),  # liver
                    ]),
                Uncertainty(
                    sid="uncertainty2",
                    uncertParameters=[
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                            value=2.7),
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                            value=0.11),
                    ], annotations=[
                        (BQB.IS, "sabiork.kineticrecord/2581"),
                        # entry in SABIO-RK
                        (BQB.HAS_TAXON, "taxonomy/9606"),  # homo sapiens
                        (BQB.IS, "ec-code/2.7.1.2"),  # glucokinase
                        (BQB.IS, "uniprot/P35557"),  # Glucokinase homo sapiens
                        (BQB.IS, "bto/BTO:0000075"),  # liver
                    ]),
            ])
    ]
}

# create model and print SBML
core_model = CoreModel.from_dict(model_dict=model_dict)
print_xml(core_model.get_sbml())

# validate model
from notebook import BASE_DIR
from sbmlutils.io import write_sbml
validate_doc(core_model.doc, units_consistency=False);
sbml_path = BASE_DIR / "distrib"/ "sabiork_parameter.xml"
write_sbml(core_model.doc, sbml_path)

from sbmlutils.report import sbmlreport
sbmlreport.create_report(sbml_path, output_dir=BASE_DIR / "distrib", validate=False)


# In[ ]:




