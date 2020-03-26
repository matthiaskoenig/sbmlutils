SBML distrib
------------

The following examples demonstrate the creation of SBML models with SBML
distrib information.

.. code:: ipython3

    %load_ext autoreload
    %autoreload 2

.. code:: ipython3

    from notebook_utils import print_xml
    from sbmlutils.units import *
    from sbmlutils.factory import *
    from sbmlutils.modelcreator.creator import CoreModel
    from sbmlutils.validation import check_doc

Assigning a distribution to a parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here we create a parameter

.. math:: p_1 = 0.0

and assign the initial value from a normal distribution with ``mean=0``
and ``standard deviation=1``

.. math:: p_1 = \sigma(0,1)

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_distrib_assignment&quot;</span> <span class="na">id=</span><span class="s">&quot;distrib_assignment&quot;</span> <span class="na">name=</span><span class="s">&quot;distrib_assignment&quot;</span> <span class="na">substanceUnits=</span><span class="s">&quot;mole&quot;</span> <span class="na">timeUnits=</span><span class="s">&quot;hr&quot;</span> <span class="na">volumeUnits=</span><span class="s">&quot;litre&quot;</span> <span class="na">areaUnits=</span><span class="s">&quot;m2&quot;</span> <span class="na">lengthUnits=</span><span class="s">&quot;m&quot;</span> <span class="na">extentUnits=</span><span class="s">&quot;mole&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfUnitDefinitions&gt;</span>
          <span class="nt">&lt;unitDefinition</span> <span class="na">id=</span><span class="s">&quot;hr&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;listOfUnits&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;second&quot;</span> <span class="na">exponent=</span><span class="s">&quot;1&quot;</span> <span class="na">scale=</span><span class="s">&quot;0&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;3600&quot;</span><span class="nt">/&gt;</span>
            <span class="nt">&lt;/listOfUnits&gt;</span>
          <span class="nt">&lt;/unitDefinition&gt;</span>
          <span class="nt">&lt;unitDefinition</span> <span class="na">id=</span><span class="s">&quot;m&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;listOfUnits&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;metre&quot;</span> <span class="na">exponent=</span><span class="s">&quot;1&quot;</span> <span class="na">scale=</span><span class="s">&quot;0&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;1&quot;</span><span class="nt">/&gt;</span>
            <span class="nt">&lt;/listOfUnits&gt;</span>
          <span class="nt">&lt;/unitDefinition&gt;</span>
          <span class="nt">&lt;unitDefinition</span> <span class="na">id=</span><span class="s">&quot;m2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;listOfUnits&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;metre&quot;</span> <span class="na">exponent=</span><span class="s">&quot;2&quot;</span> <span class="na">scale=</span><span class="s">&quot;0&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;1&quot;</span><span class="nt">/&gt;</span>
            <span class="nt">&lt;/listOfUnits&gt;</span>
          <span class="nt">&lt;/unitDefinition&gt;</span>
          <span class="nt">&lt;unitDefinition</span> <span class="na">id=</span><span class="s">&quot;mM&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;listOfUnits&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;mole&quot;</span> <span class="na">exponent=</span><span class="s">&quot;1&quot;</span> <span class="na">scale=</span><span class="s">&quot;-3&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;1&quot;</span><span class="nt">/&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;litre&quot;</span> <span class="na">exponent=</span><span class="s">&quot;-1&quot;</span> <span class="na">scale=</span><span class="s">&quot;0&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;1&quot;</span><span class="nt">/&gt;</span>
            <span class="nt">&lt;/listOfUnits&gt;</span>
          <span class="nt">&lt;/unitDefinition&gt;</span>
        <span class="nt">&lt;/listOfUnitDefinitions&gt;</span>
        <span class="nt">&lt;listOfParameters&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p1&quot;</span> <span class="na">value=</span><span class="s">&quot;0&quot;</span> <span class="na">units=</span><span class="s">&quot;mM&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/listOfParameters&gt;</span>
        <span class="nt">&lt;listOfInitialAssignments&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span> <span class="na">xmlns:sbml=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/normal&quot;</span><span class="nt">&gt;</span> normal <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">sbml:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">sbml:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
        <span class="nt">&lt;/listOfInitialAssignments&gt;</span>
        <span class="nt">&lt;comp:listOfPorts&gt;</span>
          <span class="nt">&lt;comp:port</span> <span class="na">metaid=</span><span class="s">&quot;hr_port&quot;</span> <span class="na">sboTerm=</span><span class="s">&quot;SBO:0000599&quot;</span> <span class="na">comp:unitRef=</span><span class="s">&quot;hr&quot;</span> <span class="na">comp:id=</span><span class="s">&quot;hr_port&quot;</span> <span class="na">comp:name=</span><span class="s">&quot;hr_port&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;comp:port</span> <span class="na">metaid=</span><span class="s">&quot;m_port&quot;</span> <span class="na">sboTerm=</span><span class="s">&quot;SBO:0000599&quot;</span> <span class="na">comp:unitRef=</span><span class="s">&quot;m&quot;</span> <span class="na">comp:id=</span><span class="s">&quot;m_port&quot;</span> <span class="na">comp:name=</span><span class="s">&quot;m_port&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;comp:port</span> <span class="na">metaid=</span><span class="s">&quot;m2_port&quot;</span> <span class="na">sboTerm=</span><span class="s">&quot;SBO:0000599&quot;</span> <span class="na">comp:unitRef=</span><span class="s">&quot;m2&quot;</span> <span class="na">comp:id=</span><span class="s">&quot;m2_port&quot;</span> <span class="na">comp:name=</span><span class="s">&quot;m2_port&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;comp:port</span> <span class="na">metaid=</span><span class="s">&quot;mM_port&quot;</span> <span class="na">sboTerm=</span><span class="s">&quot;SBO:0000599&quot;</span> <span class="na">comp:unitRef=</span><span class="s">&quot;mM&quot;</span> <span class="na">comp:id=</span><span class="s">&quot;mM_port&quot;</span> <span class="na">comp:name=</span><span class="s">&quot;mM_port&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/comp:listOfPorts&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.002
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


Using a normal distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, the initial value of y is set as a draw from the normal
distribution ``normal(z,10)``:

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);


.. parsed-literal::

    ERROR:root:Model units should be provided for a model, i.e., set the 'model_units' field on model.



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_normal&quot;</span> <span class="na">id=</span><span class="s">&quot;normal&quot;</span> <span class="na">name=</span><span class="s">&quot;normal&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfParameters&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;y&quot;</span> <span class="na">value=</span><span class="s">&quot;1&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;z&quot;</span> <span class="na">value=</span><span class="s">&quot;1&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/listOfParameters&gt;</span>
        <span class="nt">&lt;listOfInitialAssignments&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;y&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/normal&quot;</span><span class="nt">&gt;</span> normal <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;ci&gt;</span> z <span class="nt">&lt;/ci&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
        <span class="nt">&lt;/listOfInitialAssignments&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.001
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


Defining a truncated normal distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When used with four arguments instead of two, the normal distribution is
truncated to ``normal(z, 10, z-2, z+2)``. This use would apply a draw
from a normal distribution with ``mean z``, ``standard deviation 10``,
``lower bound z-2`` (inclusive) and ``upper bound z+2`` (not inclusive)
to the SBML symbol ``y``.

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);


.. parsed-literal::

    ERROR:root:Model units should be provided for a model, i.e., set the 'model_units' field on model.



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_truncated_normal&quot;</span> <span class="na">id=</span><span class="s">&quot;truncated_normal&quot;</span> <span class="na">name=</span><span class="s">&quot;truncated_normal&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfParameters&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;y&quot;</span> <span class="na">value=</span><span class="s">&quot;1&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;z&quot;</span> <span class="na">value=</span><span class="s">&quot;1&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/listOfParameters&gt;</span>
        <span class="nt">&lt;listOfInitialAssignments&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;y&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/normal&quot;</span><span class="nt">&gt;</span> normal <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;ci&gt;</span> z <span class="nt">&lt;/ci&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;apply&gt;</span>
                  <span class="nt">&lt;minus/&gt;</span>
                  <span class="nt">&lt;ci&gt;</span> z <span class="nt">&lt;/ci&gt;</span>
                  <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 2 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;/apply&gt;</span>
                <span class="nt">&lt;apply&gt;</span>
                  <span class="nt">&lt;plus/&gt;</span>
                  <span class="nt">&lt;ci&gt;</span> z <span class="nt">&lt;/ci&gt;</span>
                  <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 2 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;/apply&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
        <span class="nt">&lt;/listOfInitialAssignments&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.001
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


Defining conditional events
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simultaneous events in SBML are ordered based on their Priority values,
with higher values being executed first, and potentially cancelling
events that fire after them. In this example, two simultaneous events
have priorities set with csymbols defined in distrib. The event ``E0``
has a priority of ``uniform(0,1)``, while the event ``E1`` has a
priority of ``uniform(0,2)``. This means that 75% of the time, event
``E1`` will have a higher priority than ``E0``, and will fire first,
assigning a value of ``5`` to parameter ``x``. Because this negates the
trigger condition for ``E0``, which is set ``persistent="false"``, this
means that ``E0`` never fires, and the value of ``x`` remains at ``5``.
The remaining 25% of the time, the reverse happens, with ``E0`` setting
the value of ``x`` to ``3`` instead.

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);


.. parsed-literal::

    ERROR:root:Model units should be provided for a model, i.e., set the 'model_units' field on model.



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_conditional_events&quot;</span> <span class="na">id=</span><span class="s">&quot;conditional_events&quot;</span> <span class="na">name=</span><span class="s">&quot;conditional_events&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfParameters&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;x&quot;</span> <span class="na">value=</span><span class="s">&quot;1&quot;</span> <span class="na">constant=</span><span class="s">&quot;false&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/listOfParameters&gt;</span>
        <span class="nt">&lt;listOfEvents&gt;</span>
          <span class="nt">&lt;event</span> <span class="na">id=</span><span class="s">&quot;E0&quot;</span> <span class="na">useValuesFromTriggerTime=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;trigger</span> <span class="na">initialValue=</span><span class="s">&quot;true&quot;</span> <span class="na">persistent=</span><span class="s">&quot;false&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
                <span class="nt">&lt;apply&gt;</span>
                  <span class="nt">&lt;and/&gt;</span>
                  <span class="nt">&lt;apply&gt;</span>
                    <span class="nt">&lt;gt/&gt;</span>
                    <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/time&quot;</span><span class="nt">&gt;</span> time <span class="nt">&lt;/csymbol&gt;</span>
                    <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 2 <span class="nt">&lt;/cn&gt;</span>
                  <span class="nt">&lt;/apply&gt;</span>
                  <span class="nt">&lt;apply&gt;</span>
                    <span class="nt">&lt;lt/&gt;</span>
                    <span class="nt">&lt;ci&gt;</span> x <span class="nt">&lt;/ci&gt;</span>
                    <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                  <span class="nt">&lt;/apply&gt;</span>
                <span class="nt">&lt;/apply&gt;</span>
              <span class="nt">&lt;/math&gt;</span>
            <span class="nt">&lt;/trigger&gt;</span>
            <span class="nt">&lt;priority&gt;</span>
              <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
                <span class="nt">&lt;apply&gt;</span>
                  <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/uniform&quot;</span><span class="nt">&gt;</span> uniform <span class="nt">&lt;/csymbol&gt;</span>
                  <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                  <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;/apply&gt;</span>
              <span class="nt">&lt;/math&gt;</span>
            <span class="nt">&lt;/priority&gt;</span>
            <span class="nt">&lt;listOfEventAssignments&gt;</span>
              <span class="nt">&lt;eventAssignment</span> <span class="na">variable=</span><span class="s">&quot;x&quot;</span><span class="nt">&gt;</span>
                <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
                  <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 3 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;/math&gt;</span>
              <span class="nt">&lt;/eventAssignment&gt;</span>
            <span class="nt">&lt;/listOfEventAssignments&gt;</span>
          <span class="nt">&lt;/event&gt;</span>
          <span class="nt">&lt;event</span> <span class="na">id=</span><span class="s">&quot;E1&quot;</span> <span class="na">useValuesFromTriggerTime=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;trigger</span> <span class="na">initialValue=</span><span class="s">&quot;true&quot;</span> <span class="na">persistent=</span><span class="s">&quot;false&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
                <span class="nt">&lt;apply&gt;</span>
                  <span class="nt">&lt;and/&gt;</span>
                  <span class="nt">&lt;apply&gt;</span>
                    <span class="nt">&lt;gt/&gt;</span>
                    <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/time&quot;</span><span class="nt">&gt;</span> time <span class="nt">&lt;/csymbol&gt;</span>
                    <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 2 <span class="nt">&lt;/cn&gt;</span>
                  <span class="nt">&lt;/apply&gt;</span>
                  <span class="nt">&lt;apply&gt;</span>
                    <span class="nt">&lt;lt/&gt;</span>
                    <span class="nt">&lt;ci&gt;</span> x <span class="nt">&lt;/ci&gt;</span>
                    <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                  <span class="nt">&lt;/apply&gt;</span>
                <span class="nt">&lt;/apply&gt;</span>
              <span class="nt">&lt;/math&gt;</span>
            <span class="nt">&lt;/trigger&gt;</span>
            <span class="nt">&lt;priority&gt;</span>
              <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
                <span class="nt">&lt;apply&gt;</span>
                  <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/uniform&quot;</span><span class="nt">&gt;</span> uniform <span class="nt">&lt;/csymbol&gt;</span>
                  <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                  <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 2 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;/apply&gt;</span>
              <span class="nt">&lt;/math&gt;</span>
            <span class="nt">&lt;/priority&gt;</span>
            <span class="nt">&lt;listOfEventAssignments&gt;</span>
              <span class="nt">&lt;eventAssignment</span> <span class="na">variable=</span><span class="s">&quot;x&quot;</span><span class="nt">&gt;</span>
                <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
                  <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 5 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;/math&gt;</span>
              <span class="nt">&lt;/eventAssignment&gt;</span>
            <span class="nt">&lt;/listOfEventAssignments&gt;</span>
          <span class="nt">&lt;/event&gt;</span>
        <span class="nt">&lt;/listOfEvents&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.002
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


Overview of all distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following gives an example how to use all of the various
distributions

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);


.. parsed-literal::

    ERROR:root:Model units should be provided for a model, i.e., set the 'model_units' field on model.



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_all_distributions&quot;</span> <span class="na">id=</span><span class="s">&quot;all_distributions&quot;</span> <span class="na">name=</span><span class="s">&quot;all_distributions&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfParameters&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_normal_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_normal_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_uniform&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_bernoulli&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_binomial_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_binomial_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_cauchy_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_cauchy_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_chisquare_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_chisquare_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_exponential_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_exponential_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_gamma_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_gamma_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_laplace_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_laplace_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_lognormal_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_lognormal_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_poisson_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_poisson_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_raleigh_1&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p_raleigh_2&quot;</span> <span class="na">units=</span><span class="s">&quot;dimensionless&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/listOfParameters&gt;</span>
        <span class="nt">&lt;listOfInitialAssignments&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_normal_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/normal&quot;</span><span class="nt">&gt;</span> normal <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_normal_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/normal&quot;</span><span class="nt">&gt;</span> normal <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_uniform&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/uniform&quot;</span><span class="nt">&gt;</span> uniform <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 5 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_bernoulli&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/bernoulli&quot;</span><span class="nt">&gt;</span> bernoulli <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 0.4 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_binomial_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/binomial&quot;</span><span class="nt">&gt;</span> binomial <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 100 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 0.3 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_binomial_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/binomial&quot;</span><span class="nt">&gt;</span> binomial <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 100 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 0.3 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 2 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_cauchy_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/cauchy&quot;</span><span class="nt">&gt;</span> cauchy <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_cauchy_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/cauchy&quot;</span><span class="nt">&gt;</span> cauchy <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 5 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_chisquare_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/chisquare&quot;</span><span class="nt">&gt;</span> chisquare <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_chisquare_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/chisquare&quot;</span><span class="nt">&gt;</span> chisquare <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_exponential_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/exponential&quot;</span><span class="nt">&gt;</span> exponential <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_exponential_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/exponential&quot;</span><span class="nt">&gt;</span> exponential <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_gamma_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/gamma&quot;</span><span class="nt">&gt;</span> gamma <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_gamma_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/gamma&quot;</span><span class="nt">&gt;</span> gamma <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_laplace_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/laplace&quot;</span><span class="nt">&gt;</span> laplace <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_laplace_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/laplace&quot;</span><span class="nt">&gt;</span> laplace <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_lognormal_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/lognormal&quot;</span><span class="nt">&gt;</span> lognormal <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_lognormal_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/lognormal&quot;</span><span class="nt">&gt;</span> lognormal <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_poisson_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/poisson&quot;</span><span class="nt">&gt;</span> poisson <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 0.5 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_poisson_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/poisson&quot;</span><span class="nt">&gt;</span> poisson <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 0.5 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_raleigh_1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/rayleigh&quot;</span><span class="nt">&gt;</span> rayleigh <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 0.5 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p_raleigh_2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/rayleigh&quot;</span><span class="nt">&gt;</span> rayleigh <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn&gt;</span> 0.5 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 10 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
        <span class="nt">&lt;/listOfInitialAssignments&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.004
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


Basic uncertainty example
~~~~~~~~~~~~~~~~~~~~~~~~~

Here, the species with an initial amount of ``3.22`` is described as
having a ``standard deviation`` of ``0.3``, a value that might be
written as ``3.22 +- 0.3``.

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);


.. parsed-literal::

    ERROR:root:Model units should be provided for a model, i.e., set the 'model_units' field on model.



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_basic_example_1&quot;</span> <span class="na">id=</span><span class="s">&quot;basic_example_1&quot;</span> <span class="na">name=</span><span class="s">&quot;basic_example_1&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfCompartments&gt;</span>
          <span class="nt">&lt;compartment</span> <span class="na">id=</span><span class="s">&quot;C&quot;</span> <span class="na">spatialDimensions=</span><span class="s">&quot;3&quot;</span> <span class="na">size=</span><span class="s">&quot;1&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/listOfCompartments&gt;</span>
        <span class="nt">&lt;listOfSpecies&gt;</span>
          <span class="nt">&lt;species</span> <span class="na">id=</span><span class="s">&quot;s1&quot;</span> <span class="na">compartment=</span><span class="s">&quot;C&quot;</span> <span class="na">initialAmount=</span><span class="s">&quot;3.22&quot;</span> <span class="na">hasOnlySubstanceUnits=</span><span class="s">&quot;false&quot;</span> <span class="na">boundaryCondition=</span><span class="s">&quot;false&quot;</span> <span class="na">constant=</span><span class="s">&quot;false&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;distrib:listOfUncertainties&gt;</span>
              <span class="nt">&lt;distrib:uncertainty&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;0.3&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;standardDeviation&quot;</span><span class="nt">/&gt;</span>
              <span class="nt">&lt;/distrib:uncertainty&gt;</span>
            <span class="nt">&lt;/distrib:listOfUncertainties&gt;</span>
          <span class="nt">&lt;/species&gt;</span>
        <span class="nt">&lt;/listOfSpecies&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.001
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


It is also possible to include additional information about the species,
should more be known. In this example, the initial amount of ``3.22`` is
noted as having a mean of ``3.2``, a standard deviation of ``0.3``, and
a variance of ``0.09``.

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);


.. parsed-literal::

    ERROR:root:Model units should be provided for a model, i.e., set the 'model_units' field on model.



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_basic_example_2&quot;</span> <span class="na">id=</span><span class="s">&quot;basic_example_2&quot;</span> <span class="na">name=</span><span class="s">&quot;basic_example_2&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfCompartments&gt;</span>
          <span class="nt">&lt;compartment</span> <span class="na">id=</span><span class="s">&quot;C&quot;</span> <span class="na">spatialDimensions=</span><span class="s">&quot;3&quot;</span> <span class="na">size=</span><span class="s">&quot;1&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/listOfCompartments&gt;</span>
        <span class="nt">&lt;listOfSpecies&gt;</span>
          <span class="nt">&lt;species</span> <span class="na">id=</span><span class="s">&quot;s1&quot;</span> <span class="na">compartment=</span><span class="s">&quot;C&quot;</span> <span class="na">initialAmount=</span><span class="s">&quot;3.22&quot;</span> <span class="na">hasOnlySubstanceUnits=</span><span class="s">&quot;false&quot;</span> <span class="na">boundaryCondition=</span><span class="s">&quot;false&quot;</span> <span class="na">constant=</span><span class="s">&quot;false&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;distrib:listOfUncertainties&gt;</span>
              <span class="nt">&lt;distrib:uncertainty&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;3.2&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;mean&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;0.3&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;standardDeviation&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;0.09&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;variance&quot;</span><span class="nt">/&gt;</span>
              <span class="nt">&lt;/distrib:uncertainty&gt;</span>
            <span class="nt">&lt;/distrib:listOfUncertainties&gt;</span>
          <span class="nt">&lt;/species&gt;</span>
        <span class="nt">&lt;/listOfSpecies&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.001
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


Multiple uncertainties
~~~~~~~~~~~~~~~~~~~~~~

The following gives an example how to encode multiple uncertainties for
a parameter. Here the two uncertainties
``5.0 (mean) +- 0.3 (std) [2.0 - 8.0]`` and
``4.5 (mean) +- 1.1 (std) [1.0 - 10.0]`` are set.

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_multiple_uncertainties&quot;</span> <span class="na">id=</span><span class="s">&quot;multiple_uncertainties&quot;</span> <span class="na">name=</span><span class="s">&quot;multiple_uncertainties&quot;</span> <span class="na">substanceUnits=</span><span class="s">&quot;mole&quot;</span> <span class="na">timeUnits=</span><span class="s">&quot;hr&quot;</span> <span class="na">volumeUnits=</span><span class="s">&quot;litre&quot;</span> <span class="na">areaUnits=</span><span class="s">&quot;m2&quot;</span> <span class="na">lengthUnits=</span><span class="s">&quot;m&quot;</span> <span class="na">extentUnits=</span><span class="s">&quot;mole&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfUnitDefinitions&gt;</span>
          <span class="nt">&lt;unitDefinition</span> <span class="na">id=</span><span class="s">&quot;hr&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;listOfUnits&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;second&quot;</span> <span class="na">exponent=</span><span class="s">&quot;1&quot;</span> <span class="na">scale=</span><span class="s">&quot;0&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;3600&quot;</span><span class="nt">/&gt;</span>
            <span class="nt">&lt;/listOfUnits&gt;</span>
          <span class="nt">&lt;/unitDefinition&gt;</span>
          <span class="nt">&lt;unitDefinition</span> <span class="na">id=</span><span class="s">&quot;m&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;listOfUnits&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;metre&quot;</span> <span class="na">exponent=</span><span class="s">&quot;1&quot;</span> <span class="na">scale=</span><span class="s">&quot;0&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;1&quot;</span><span class="nt">/&gt;</span>
            <span class="nt">&lt;/listOfUnits&gt;</span>
          <span class="nt">&lt;/unitDefinition&gt;</span>
          <span class="nt">&lt;unitDefinition</span> <span class="na">id=</span><span class="s">&quot;m2&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;listOfUnits&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;metre&quot;</span> <span class="na">exponent=</span><span class="s">&quot;2&quot;</span> <span class="na">scale=</span><span class="s">&quot;0&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;1&quot;</span><span class="nt">/&gt;</span>
            <span class="nt">&lt;/listOfUnits&gt;</span>
          <span class="nt">&lt;/unitDefinition&gt;</span>
          <span class="nt">&lt;unitDefinition</span> <span class="na">id=</span><span class="s">&quot;mM&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;listOfUnits&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;mole&quot;</span> <span class="na">exponent=</span><span class="s">&quot;1&quot;</span> <span class="na">scale=</span><span class="s">&quot;-3&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;1&quot;</span><span class="nt">/&gt;</span>
              <span class="nt">&lt;unit</span> <span class="na">kind=</span><span class="s">&quot;litre&quot;</span> <span class="na">exponent=</span><span class="s">&quot;-1&quot;</span> <span class="na">scale=</span><span class="s">&quot;0&quot;</span> <span class="na">multiplier=</span><span class="s">&quot;1&quot;</span><span class="nt">/&gt;</span>
            <span class="nt">&lt;/listOfUnits&gt;</span>
          <span class="nt">&lt;/unitDefinition&gt;</span>
        <span class="nt">&lt;/listOfUnitDefinitions&gt;</span>
        <span class="nt">&lt;listOfParameters&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p1&quot;</span> <span class="na">value=</span><span class="s">&quot;5&quot;</span> <span class="na">units=</span><span class="s">&quot;mM&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;distrib:listOfUncertainties&gt;</span>
              <span class="nt">&lt;distrib:uncertainty&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;5&quot;</span> <span class="na">distrib:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;mean&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;0.3&quot;</span> <span class="na">distrib:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;standardDeviation&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertSpan</span> <span class="na">distrib:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;range&quot;</span> <span class="na">distrib:valueLower=</span><span class="s">&quot;2&quot;</span> <span class="na">distrib:valueUpper=</span><span class="s">&quot;8&quot;</span><span class="nt">/&gt;</span>
              <span class="nt">&lt;/distrib:uncertainty&gt;</span>
              <span class="nt">&lt;distrib:uncertainty&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;4.5&quot;</span> <span class="na">distrib:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;mean&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;1.1&quot;</span> <span class="na">distrib:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;standardDeviation&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertSpan</span> <span class="na">distrib:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;range&quot;</span> <span class="na">distrib:valueLower=</span><span class="s">&quot;1&quot;</span> <span class="na">distrib:valueUpper=</span><span class="s">&quot;10&quot;</span><span class="nt">/&gt;</span>
              <span class="nt">&lt;/distrib:uncertainty&gt;</span>
            <span class="nt">&lt;/distrib:listOfUncertainties&gt;</span>
          <span class="nt">&lt;/parameter&gt;</span>
        <span class="nt">&lt;/listOfParameters&gt;</span>
        <span class="nt">&lt;listOfInitialAssignments&gt;</span>
          <span class="nt">&lt;initialAssignment</span> <span class="na">symbol=</span><span class="s">&quot;p1&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span> <span class="na">xmlns:sbml=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span><span class="nt">&gt;</span>
              <span class="nt">&lt;apply&gt;</span>
                <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/normal&quot;</span><span class="nt">&gt;</span> normal <span class="nt">&lt;/csymbol&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">sbml:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                <span class="nt">&lt;cn</span> <span class="na">sbml:units=</span><span class="s">&quot;mM&quot;</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
              <span class="nt">&lt;/apply&gt;</span>
            <span class="nt">&lt;/math&gt;</span>
          <span class="nt">&lt;/initialAssignment&gt;</span>
        <span class="nt">&lt;/listOfInitialAssignments&gt;</span>
        <span class="nt">&lt;comp:listOfPorts&gt;</span>
          <span class="nt">&lt;comp:port</span> <span class="na">metaid=</span><span class="s">&quot;hr_port&quot;</span> <span class="na">sboTerm=</span><span class="s">&quot;SBO:0000599&quot;</span> <span class="na">comp:unitRef=</span><span class="s">&quot;hr&quot;</span> <span class="na">comp:id=</span><span class="s">&quot;hr_port&quot;</span> <span class="na">comp:name=</span><span class="s">&quot;hr_port&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;comp:port</span> <span class="na">metaid=</span><span class="s">&quot;m_port&quot;</span> <span class="na">sboTerm=</span><span class="s">&quot;SBO:0000599&quot;</span> <span class="na">comp:unitRef=</span><span class="s">&quot;m&quot;</span> <span class="na">comp:id=</span><span class="s">&quot;m_port&quot;</span> <span class="na">comp:name=</span><span class="s">&quot;m_port&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;comp:port</span> <span class="na">metaid=</span><span class="s">&quot;m2_port&quot;</span> <span class="na">sboTerm=</span><span class="s">&quot;SBO:0000599&quot;</span> <span class="na">comp:unitRef=</span><span class="s">&quot;m2&quot;</span> <span class="na">comp:id=</span><span class="s">&quot;m2_port&quot;</span> <span class="na">comp:name=</span><span class="s">&quot;m2_port&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;comp:port</span> <span class="na">metaid=</span><span class="s">&quot;mM_port&quot;</span> <span class="na">sboTerm=</span><span class="s">&quot;SBO:0000599&quot;</span> <span class="na">comp:unitRef=</span><span class="s">&quot;mM&quot;</span> <span class="na">comp:id=</span><span class="s">&quot;mM_port&quot;</span> <span class="na">comp:name=</span><span class="s">&quot;mM_port&quot;</span><span class="nt">/&gt;</span>
        <span class="nt">&lt;/comp:listOfPorts&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.002
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


Defining a random variable
~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to describing the uncertainty about an experimental
observation one can also use this mechanism to describe a parameter as a
random variable.

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);


.. parsed-literal::

    ERROR:root:Model units should be provided for a model, i.e., set the 'model_units' field on model.



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_random_variable&quot;</span> <span class="na">id=</span><span class="s">&quot;random_variable&quot;</span> <span class="na">name=</span><span class="s">&quot;random_variable&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfParameters&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;shape_Z&quot;</span> <span class="na">value=</span><span class="s">&quot;10&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;scale_Z&quot;</span> <span class="na">value=</span><span class="s">&quot;0.1&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">/&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;Z&quot;</span> <span class="na">value=</span><span class="s">&quot;0.1&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;distrib:listOfUncertainties&gt;</span>
              <span class="nt">&lt;distrib:uncertainty&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;1.03&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;mean&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;0.97&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;variance&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:type=</span><span class="s">&quot;distribution&quot;</span> <span class="na">distrib:definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/gamma&quot;</span><span class="nt">&gt;</span>
                  <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
                    <span class="nt">&lt;apply&gt;</span>
                      <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/gamma&quot;</span><span class="nt">&gt;</span> gamma <span class="nt">&lt;/csymbol&gt;</span>
                      <span class="nt">&lt;ci&gt;</span> shape_Z <span class="nt">&lt;/ci&gt;</span>
                      <span class="nt">&lt;ci&gt;</span> scale_Z <span class="nt">&lt;/ci&gt;</span>
                    <span class="nt">&lt;/apply&gt;</span>
                  <span class="nt">&lt;/math&gt;</span>
                <span class="nt">&lt;/distrib:uncertParameter&gt;</span>
              <span class="nt">&lt;/distrib:uncertainty&gt;</span>
            <span class="nt">&lt;/distrib:listOfUncertainties&gt;</span>
          <span class="nt">&lt;/parameter&gt;</span>
        <span class="nt">&lt;/listOfParameters&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 2
    check time (s)           : 0.001
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


Overview over UncertParameters and UncertSpans
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example provides an overview over the available fields.

.. code:: ipython3

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
    check_doc(core_model.doc, units_consistency=False);


.. parsed-literal::

    ERROR:root:Model units should be provided for a model, i.e., set the 'model_units' field on model.



.. raw:: html

    <style type="text/css">.highlight .hll { background-color: #ffffcc }
    .highlight  { background: #f8f8f8; }
    .highlight .c { color: #408080; font-style: italic } /* Comment */
    .highlight .err { border: 1px solid #FF0000 } /* Error */
    .highlight .k { color: #008000; font-weight: bold } /* Keyword */
    .highlight .o { color: #666666 } /* Operator */
    .highlight .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
    .highlight .cm { color: #408080; font-style: italic } /* Comment.Multiline */
    .highlight .cp { color: #BC7A00 } /* Comment.Preproc */
    .highlight .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
    .highlight .c1 { color: #408080; font-style: italic } /* Comment.Single */
    .highlight .cs { color: #408080; font-style: italic } /* Comment.Special */
    .highlight .gd { color: #A00000 } /* Generic.Deleted */
    .highlight .ge { font-style: italic } /* Generic.Emph */
    .highlight .gr { color: #FF0000 } /* Generic.Error */
    .highlight .gh { color: #000080; font-weight: bold } /* Generic.Heading */
    .highlight .gi { color: #00A000 } /* Generic.Inserted */
    .highlight .go { color: #888888 } /* Generic.Output */
    .highlight .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
    .highlight .gs { font-weight: bold } /* Generic.Strong */
    .highlight .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
    .highlight .gt { color: #0044DD } /* Generic.Traceback */
    .highlight .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
    .highlight .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
    .highlight .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
    .highlight .kp { color: #008000 } /* Keyword.Pseudo */
    .highlight .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
    .highlight .kt { color: #B00040 } /* Keyword.Type */
    .highlight .m { color: #666666 } /* Literal.Number */
    .highlight .s { color: #BA2121 } /* Literal.String */
    .highlight .na { color: #7D9029 } /* Name.Attribute */
    .highlight .nb { color: #008000 } /* Name.Builtin */
    .highlight .nc { color: #0000FF; font-weight: bold } /* Name.Class */
    .highlight .no { color: #880000 } /* Name.Constant */
    .highlight .nd { color: #AA22FF } /* Name.Decorator */
    .highlight .ni { color: #999999; font-weight: bold } /* Name.Entity */
    .highlight .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
    .highlight .nf { color: #0000FF } /* Name.Function */
    .highlight .nl { color: #A0A000 } /* Name.Label */
    .highlight .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
    .highlight .nt { color: #008000; font-weight: bold } /* Name.Tag */
    .highlight .nv { color: #19177C } /* Name.Variable */
    .highlight .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
    .highlight .w { color: #bbbbbb } /* Text.Whitespace */
    .highlight .mb { color: #666666 } /* Literal.Number.Bin */
    .highlight .mf { color: #666666 } /* Literal.Number.Float */
    .highlight .mh { color: #666666 } /* Literal.Number.Hex */
    .highlight .mi { color: #666666 } /* Literal.Number.Integer */
    .highlight .mo { color: #666666 } /* Literal.Number.Oct */
    .highlight .sa { color: #BA2121 } /* Literal.String.Affix */
    .highlight .sb { color: #BA2121 } /* Literal.String.Backtick */
    .highlight .sc { color: #BA2121 } /* Literal.String.Char */
    .highlight .dl { color: #BA2121 } /* Literal.String.Delimiter */
    .highlight .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
    .highlight .s2 { color: #BA2121 } /* Literal.String.Double */
    .highlight .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
    .highlight .sh { color: #BA2121 } /* Literal.String.Heredoc */
    .highlight .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
    .highlight .sx { color: #008000 } /* Literal.String.Other */
    .highlight .sr { color: #BB6688 } /* Literal.String.Regex */
    .highlight .s1 { color: #BA2121 } /* Literal.String.Single */
    .highlight .ss { color: #19177C } /* Literal.String.Symbol */
    .highlight .bp { color: #008000 } /* Name.Builtin.Pseudo */
    .highlight .fm { color: #0000FF } /* Name.Function.Magic */
    .highlight .vc { color: #19177C } /* Name.Variable.Class */
    .highlight .vg { color: #19177C } /* Name.Variable.Global */
    .highlight .vi { color: #19177C } /* Name.Variable.Instance */
    .highlight .vm { color: #19177C } /* Name.Variable.Magic */
    .highlight .il { color: #666666 } /* Literal.Number.Integer.Long */</style>    <div class="highlight"><pre><span></span><span class="cp">&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot;?&gt;</span>
    <span class="nt">&lt;sbml</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/core&quot;</span> <span class="na">xmlns:comp=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/comp/version1&quot;</span> <span class="na">xmlns:distrib=</span><span class="s">&quot;http://www.sbml.org/sbml/level3/version1/distrib/version1&quot;</span> <span class="na">level=</span><span class="s">&quot;3&quot;</span> <span class="na">version=</span><span class="s">&quot;1&quot;</span> <span class="na">comp:required=</span><span class="s">&quot;true&quot;</span> <span class="na">distrib:required=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
      <span class="nt">&lt;model</span> <span class="na">metaid=</span><span class="s">&quot;meta_parameters_spans&quot;</span> <span class="na">id=</span><span class="s">&quot;parameters_spans&quot;</span> <span class="na">name=</span><span class="s">&quot;parameters_spans&quot;</span><span class="nt">&gt;</span>
        <span class="nt">&lt;listOfParameters&gt;</span>
          <span class="nt">&lt;parameter</span> <span class="na">id=</span><span class="s">&quot;p&quot;</span> <span class="na">constant=</span><span class="s">&quot;true&quot;</span><span class="nt">&gt;</span>
            <span class="nt">&lt;distrib:listOfUncertainties&gt;</span>
              <span class="nt">&lt;distrib:uncertainty&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;1&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;coeffientOfVariation&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;2&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;kurtosis&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;3&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;mean&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;4&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;median&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;5&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;mode&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;6&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;sampleSize&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;7&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;skewness&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;8&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;standardDeviation&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;9&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;standardError&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:value=</span><span class="s">&quot;10&quot;</span> <span class="na">distrib:type=</span><span class="s">&quot;variance&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertSpan</span> <span class="na">distrib:type=</span><span class="s">&quot;confidenceInterval&quot;</span> <span class="na">distrib:valueLower=</span><span class="s">&quot;1&quot;</span> <span class="na">distrib:valueUpper=</span><span class="s">&quot;2&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertSpan</span> <span class="na">distrib:type=</span><span class="s">&quot;credibleInterval&quot;</span> <span class="na">distrib:valueLower=</span><span class="s">&quot;2&quot;</span> <span class="na">distrib:valueUpper=</span><span class="s">&quot;3&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertSpan</span> <span class="na">distrib:type=</span><span class="s">&quot;interquartileRange&quot;</span> <span class="na">distrib:valueLower=</span><span class="s">&quot;3&quot;</span> <span class="na">distrib:valueUpper=</span><span class="s">&quot;4&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertSpan</span> <span class="na">distrib:type=</span><span class="s">&quot;range&quot;</span> <span class="na">distrib:valueLower=</span><span class="s">&quot;4&quot;</span> <span class="na">distrib:valueUpper=</span><span class="s">&quot;5&quot;</span><span class="nt">/&gt;</span>
                <span class="nt">&lt;distrib:uncertParameter</span> <span class="na">distrib:type=</span><span class="s">&quot;distribution&quot;</span> <span class="na">distrib:definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/normal&quot;</span><span class="nt">&gt;</span>
                  <span class="nt">&lt;math</span> <span class="na">xmlns=</span><span class="s">&quot;http://www.w3.org/1998/Math/MathML&quot;</span><span class="nt">&gt;</span>
                    <span class="nt">&lt;apply&gt;</span>
                      <span class="nt">&lt;csymbol</span> <span class="na">encoding=</span><span class="s">&quot;text&quot;</span> <span class="na">definitionURL=</span><span class="s">&quot;http://www.sbml.org/sbml/symbols/distrib/normal&quot;</span><span class="nt">&gt;</span> normal <span class="nt">&lt;/csymbol&gt;</span>
                      <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 0 <span class="nt">&lt;/cn&gt;</span>
                      <span class="nt">&lt;cn</span> <span class="na">type=</span><span class="s">&quot;integer&quot;</span><span class="nt">&gt;</span> 1 <span class="nt">&lt;/cn&gt;</span>
                    <span class="nt">&lt;/apply&gt;</span>
                  <span class="nt">&lt;/math&gt;</span>
                <span class="nt">&lt;/distrib:uncertParameter&gt;</span>
              <span class="nt">&lt;/distrib:uncertainty&gt;</span>
            <span class="nt">&lt;/distrib:listOfUncertainties&gt;</span>
          <span class="nt">&lt;/parameter&gt;</span>
        <span class="nt">&lt;/listOfParameters&gt;</span>
      <span class="nt">&lt;/model&gt;</span>
    <span class="nt">&lt;/sbml&gt;</span>
    </pre></div>



.. parsed-literal::

    WARNING:root:[1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    validation error(s)      : 0
    validation warnings(s)   : 3
    check time (s)           : 0.002
    --------------------------------------------------------------------------------
    [0m[0m
    WARNING:root:[47m[30mE0: Modeling practice (core, L1, code)[0m[0m
    [91m[Warning] It's best to declare values for every parameter in a model[0m
    [94mAs a principle of best modeling practice, the <parameter> should set an initial value rather than be left undefined. Doing so improves the portability of models between different simulation and analysis systems, and helps make it easier to detect potential errors in models.
     The <parameter> with the id 'p' does not have 'value' attribute, nor is its initial value set by an <initialAssignment> or <assignmentRule>.
    [0m
    WARNING:root:[47m[30mE1: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Line numbers unreliable.[0m
    [94mDue to the need to instantiate models, modelDefinitions, submodels etc. for the purposes of validation it is problematic to reliably report line numbers when performing validation on models using the Hierarchical Model Composition package.
    [0m
    WARNING:root:[47m[30mE2: SBML component consistency (comp, L1, code)[0m[0m
    [91m[Warning] Flattening not implemented for required package.[0m
    [94mThe CompFlatteningConverter has encountered a required package for which the necessary routines to allow flattening have not yet been implemented. 
     The CompFlatteningConverter has the 'abortIfUnflattenable' option set to 'requiredOnly'  and thus flattening will not be attempted.
    [0m


