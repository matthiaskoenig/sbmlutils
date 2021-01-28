============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Report Bugs
===========

Report bugs at https://github.com/matthiaskoenig/sbmlutils/issues.

If you are reporting a bug, please follow the template guide lines. The more
detailed your report, the easier and thus faster we can help you.

Fix Bugs
========

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
==================

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
===================

sbmlutils could always use more documentation, whether as part of the official
documentation, in docstrings, or even on the web in blog posts, articles, and
such.

Submit Feedback
===============

The best way to send feedback is to file an issue at
https://github.com/matthiaskoenig/sbmlutils/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions are
  welcome :)

Get Started!
============

Ready to contribute? Here's how to set up sbmlutils for local development.

1. Fork the https://github.com/matthiaskoenig/sbmlutils repository on GitHub. If you
   have never done this before, `follow the official guide
   <https://guides.github.com/activities/forking/>`_
2. Clone your fork locally as described in the same guide.
3. Install your local copy into a a Python virtual environment.  You can `read
   this guide to learn more
   <https://realpython.com/python-virtual-environments-a-primer/>`_ about them
   and how to create one. Alternatively, particularly if you are a Windows or
   Mac user, you can also use `Anaconda <https://docs.anaconda.com/anaconda/>`_.
   Assuming you have virtualenvwrapper installed, this is how you set up your
   fork for local development

   .. code-block:: console

       mkvirtualenv sbmlutils
       cd sbmlutils/
       pip install -e ".[development]"

4. Create a branch for local development using the ``develop`` branch as a
   starting point. Use ``fix``, ``refactor``, or ``feat`` as a prefix

   .. code-block:: console

       git checkout devel
       git checkout -b fix-name-of-your-bugfix

   Now you can make your changes locally.

5. When making changes locally, it is helpful to ``git commit`` your work
   regularly. On one hand to save your work and on the other hand, the smaller
   the steps, the easier it is to review your work later. Please use `semantic
   commit messages
   <http://karma-runner.github.io/2.0/dev/git-commit-msg.html>`_.

   .. code-block:: console

       git add .
       git commit -m "fix: Your summary of changes"

6. When you're done making changes, check that your changes pass our test suite (with
   exception of flake8).
   This is all included with tox

   .. code-block:: console

       tox

   You can run all tests in parallel using detox. To get detox, just pip install
   it into your virtualenv.

   To fix the isort and black tests use
   
   .. code-block:: console

       isort src/sbmlutils
       black src/sbmlutils --exclude resources

7. Push your branch to GitHub.

   .. code-block:: console

       git push origin fix-name-of-your-bugfix

8. Open the link displayed in the message when pushing your new branch in order
   to submit a pull request. Please follow the template presented to you in the
   web interface to complete your pull request.

For larger features that you want to work on collaboratively with other sbmlutils
team members, you may consider to first request to join the sbmlutils developers
team to get write access to the repository so that you can create a branch in
the main repository (or simply ask the maintainer to create a branch for you).
Once you have a new branch you can push your changes directly to the main
repository and when finished, submit a pull request from that branch to
``develop``.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests in the ``sbmlutils/test``
   directory. Except in rare circumstances, code coverage must
   not decrease (as reported by codecov which runs automatically when
   you submit your pull request)
2. If the pull request adds functionality, the docs should be
   updated. Put your new functionality into a function with a
   docstring.
3. The pull request will be tested for several different Python versions.
4. Someone from the @matthiaskoenig/sbmlutils-core team will review your work and guide
   you to a successful contribution.

Unit tests and benchmarks
-------------------------

sbmlutils uses `pytest <http://docs.pytest.org/en/latest/>`_ for its
unit-tests and new features should in general always come with new
tests that make sure that the code runs as intended. 

To run all tests do::

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

Thank you very much for contributing to sbmlutils!
