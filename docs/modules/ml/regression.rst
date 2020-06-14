.. _regression-module:

Regression
==========

Module with classes to perform regression of functional data.

Linear regression
-----------------

A linear regression model is one in which the response variable can be
expressed as a linear combination of the covariates (which could be
multivariate or functional).

.. autosummary::
   :toctree: autosummary

   skfda.ml.regression.LinearRegression

Nearest Neighbors
-----------------

This module contains `nearest neighbors
<https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm>`_ estimators to
perform regression. In the examples
:ref:`sphx_glr_auto_examples_plot_neighbors_scalar_regression.py` and
:ref:`sphx_glr_auto_examples_plot_neighbors_functional_regression.py`
it is explained the basic usage of these estimators.

.. autosummary::
   :toctree: autosummary

   skfda.ml.regression.KNeighborsRegressor
   skfda.ml.regression.RadiusNeighborsRegressor
