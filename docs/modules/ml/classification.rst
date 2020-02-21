.. _classification-module:

Classification
==============

Module with classes to perform classification of functional data.


Nearest Neighbors
-----------------

This module contains `nearest neighbors
<https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm>`_ estimators to
perform classification. In the examples
:ref:`sphx_glr_auto_examples_plot_k_neighbors_classification.py`  and
:ref:`sphx_glr_auto_examples_plot_radius_neighbors_classification.py`
it is explained the basic usage of these estimators.

.. autosummary::
   :toctree: autosummary

   skfda.ml.classification.KNeighborsClassifier
   skfda.ml.classification.RadiusNeighborsClassifier
   skfda.ml.classification.NearestCentroid
