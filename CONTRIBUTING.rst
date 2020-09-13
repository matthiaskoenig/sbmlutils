============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs using the `issue tracker <https://github.com/matthiaskoenig/sbmlutils/issues>`__

If you are reporting a bug, please include:

* Your operating system name and version.
* Your python and sbmlutils version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub `issues <https://github.com/matthiaskoenig/sbmlutils/issues>`__
for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants
to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub `issues <https://github.com/matthiaskoenig/sbmlutils/issues>`__
for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to
implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

sbmlutils could always use more documentation, whether as part of the official
sbmlutils docs, in docstrings, or even on the web in blog posts, articles, and
such - all contributions are welcome!

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an
`issue <https://github.com/matthiaskoenig/sbmlutils/issues>`__.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

If you like sbmlutils please remember to 'star' our github page (click on the star
at top right corner), that way we also have an idea of who is using sbmlutils!

Get Started!
------------

Want to contribute a new feature or improvement? Consider starting by raising an
issue and assign it to yourself to describe what you want to achieve. This way,
we reduce the risk of duplicated efforts and you may also get suggestions on how
to best proceed, e.g. there may be half-finished work in some branch that you
could start with.

Here's how to set up `sbmlutils` for local development to contribute smaller
features or changes that you can implement yourself.

1. Fork the `sbmlutils` repository on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:<your Github name>/sbmlutils.git

3. If virtualenvwrapper is not installed,
   `follow the directions <https://virtualenvwrapper.readthedocs.io/en/latest/>`__
   to install virtualenvwrapper.

4. Install your local copy of sbmlutils into a virtualenv with virtualenvwrapper::

    $ cd sbmlutils
    $ mkvirtualenv sbmlutils --python3.7

   Use the ``--python`` option to select a specific version of Python for the
   virtualenv.

5. Install the required packages for development in the virtualenv using pip install::

    (sbmlutils)$ pip install --upgrade pip setuptools wheel
    (sbmlutils)$ pip install -r requirements.txt

6. Check out the branch that you want to contribute to. Most likely that will be
   ``develop``::

    (sbmlutils)$ git checkout develop

7. Create a branch for local development based on the previously checked out
   branch (see below for details on the branching model)::

    (sbmlutils)$ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

8. Setup sbmlutils for development::

    (sbmlutils)$ pip install -e .

9. When you are done making changes, check that your changes pass pep8
   and the tests with tox for your local Python version::

     (sbmlutils)$ tox -e pep8

    and likely one of::

     (sbmlutils)$ tox -e py36
     (sbmlutils)$ tox -e py37
     (sbmlutils)$ tox -e py38

10. Commit your changes and push your branch to GitHub::

    (sbmlutils)$ git add .
    (sbmlutils)$ git commit -m "Your detailed description of your changes."
    (sbmlutils)$ git push origin name-of-your-bugfix-or-feature

11. Submit a pull request through the GitHub website. Once you submit a pull
    request your changes will be tested automatically against multiple python
    versions and operating systems. Further errors might appear during those
    tests.

For larger features that you want to work on collaboratively with other sbmlutils team members,
you may consider to first request to join the sbmlutils developers team to get write access to the
repository so that you can create a branch in the main repository
(or simply ask the maintainer to create a branch for you).
Once you have a new branch you can push your changes directly to the main
repository and when finished, submit a pull request from that branch to ``develop``.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests in the ``sbmlutils/test``
   directory. Except in rare circumstances, code coverage must
   not decrease (as reported by codecov which runs automatically when
   you submit your pull request)
2. If the pull request adds functionality, the docs should be
   updated. Put your new functionality into a function with a
   docstring and consider creating a notebook that demonstrates the
   usage in ``documentation_builder`` (documentation is written as
   jupyter notebooks in the ``documentation_builder`` directory, which
   are then converted to rst by the ``autodoc.sh`` script.)
3. The pull request should work for Python 2.7, 3.5 and 3.6.
4. Assign a reviewer to your pull request. If in doubt, assign matthiaskoenig.
   Your pull request must be approved by at least one
   reviewer before it can be merged.

Unit tests and benchmarks
-------------------------

sbmlutils uses `pytest <http://docs.pytest.org/en/latest/>`_ for its
unit-tests and new features should in general always come with new
tests that make sure that the code runs as intended::

    (sbmlutils)$ pytest

Branching model
---------------

``develop``
    Is the branch all pull-requests should be based on.
``master``
    Is only touched by maintainers and is the branch with only tested, reviewed
    code that is released or ready for the next release.
``{fix, bugfix, doc, feature}/descriptive-name``
    Is the recommended naming scheme for smaller improvements, bugfixes,
    documentation improvement and new features respectively.

Please use concise descriptive commit messages and consider using
``git pull --rebase`` when you update your own fork to avoid merge commits.

1. Tests are in the ``sbmlutils/tests`` directory. They are automatically run
   through continuous integration services on supported python 3 versions
   when pull requests are made.
2. Please write tests for new functions. Writing documentation as well
   would also be very helpful.

Thank you very much for contributing to sbmlutils!
