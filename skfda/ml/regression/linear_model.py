from skfda.misc._lfd import LinearDifferentialOperator as Lfd

from sklearn.base import BaseEstimator, RegressorMixin
from skfda.representation.basis import FDataBasis, Constant, Basis, FData

import numpy as np

from sklearn.utils.validation import check_is_fitted


class LinearFunctionalRegression(BaseEstimator, RegressorMixin):

    def __init__(self, beta_basis):
        self.beta_basis = beta_basis

    def fit(self, X, y=None, sample_weight=None):

        y, X, weights = self._argcheck(y, X, sample_weight)

        rangeval = y.domain_range[0]
        onesfd = FDataBasis(Constant(rangeval), [1])

        ncoef = sum(self.beta_basis[i].nbasis for i in
                    range(len(self.beta_basis)))

        Cmat = np.zeros((ncoef, ncoef))
        Dmat = np.zeros((ncoef, 1))

        mj2 = 0
        for j in range(len(X)):
            mj1 = mj2
            mj2 = mj2 + self.beta_basis[j].nbasis
            xyfdj = X[j].times(weights).times(y)
            wtfdj = sum(xyfdj)
            Dmat[mj1:mj2] = self.beta_basis[j].to_basis().inner_product(onesfd,
                                   Lfd(0), Lfd(0), wtfdj)

            mk2 = 0
            for k in range(0, j + 1):
                mk1 = mk2
                mk2 = mk2 + self.beta_basis[k].nbasis
                xxfdjk = X[j].times(weights).times(X[k])
                wtfdjk = sum(xxfdjk)
                Cmatjk = self.beta_basis[j].to_basis().inner_product(
                    self.beta_basis[k].to_basis(), Lfd(0), Lfd(0), wtfdjk)

                Cmat[mj1: mj2, mk1: mk2] = Cmatjk
                Cmat[mk1: mk2, mj1: mj2] = np.transpose(Cmatjk)

        Cmat = (Cmat + np.transpose(Cmat)) / 2
        Cmatinv = np.linalg.inv(Cmat)
        betacoefs = np.transpose(np.transpose(Cmatinv) @ Dmat)[0]

        idx = 0
        for j in range(0, len(self.beta_basis)):
            self.beta_basis[j] = FDataBasis(
                self.beta_basis[j],
                betacoefs[idx:idx+self.beta_basis[j].nbasis].T
            )
            idx = idx + self.beta_basis[j].nbasis

        self.beta_ = self.beta_basis
        return self


    def _argcheck(self, y, x, weights = None):
        """Do some checks to types and shapes"""
        if not isinstance(y, FData):
            raise ValueError("The explanined variable is not an FData objetc")

        # TODO check for same domain_range

        xlen = len(x)
        blen = len(self.beta_basis)

        if blen != xlen:
            raise ValueError("Independent variables number should be equal "
                             "to the number of beta basis")

        for j in range(0, xlen):
            if isinstance(x[j], list):
                xjcoefs = np.asarray(x[j]).reshape((-1, 1))
                x[j] = FDataBasis(Constant(y.domain_range), xjcoefs)

        if any(y.nsamples != xfd.nsamples for xfd in x):
            raise ValueError("Dependent and independent variables should "
                             "have the same number of samples")

        if any(not isinstance(b, Basis) for b in self.beta_basis):
            raise ValueError("Betas should be a list of Basis.")

        if weights is None:
            weights = [1 for _ in range(y.nsamples)]

        if len(weights) != y.nsamples:
            raise ValueError("The number of weights should be equal to the "
                             "independent samples.")

        if np.any(np.array(weights) < 0):
            raise ValueError("The weights should be non negative values")

        return y, x, weights
