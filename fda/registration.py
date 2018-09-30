"""Registration of functional data module.

This module contains the methods to perform the registration of
functional data and related routines, in basis form as well in discretized form.

"""

import numpy
import scipy.integrate

def _check_extrapolation(fd, ext):
    # Check how to extrapolate
    # By default uses the value of the fd object
    if ext == "default" or ext == 0:
        ext = fd.default_extrapolation

    if ext == "basis" or ext == 1:
        periodic = True
        periodic_ext = False

    elif ext == "periodic" or  ext == 2:
        periodic_ext = True
        periodic = True

    elif ext == "slice" or ext == 3:
        periodic = False
        periodic_ext = False

    else:
        raise ValueError("Incorrect value of ext, should be 'default', 'basis'"\
                         ", 'periodic' or 'slice'.")

    return periodic, periodic_ext

def shift_registration(fd, maxiter=5, tol=1e-2, ext="default",
                       alpha=1, initial=[], tfine=[],
                       shifts_array=False, **kwargs):
    r"""Perform a shift registration of the curves.

        Realizes a registration of the curves, using shift aligment, as is
        defined in [RS05-7-2]_. Calculates :math:`\delta_{i}` for each sample
        such that :math:`x_i(t + \delta_{i})` minimizes the least squares
        criterion:

        .. math::
            \text{REGSSE} = \sum_{i=1}^{N} \int_{\mathcal{T}}
            [x_i(t + \delta_i) - \hat\mu(t)]^2 ds

        Estimates the shift parameter :math:`\delta_i` iteratively by
        using a modified Newton-Raphson algorithm, updating the mean
        in each iteration, as is described in detail in [RS05-7-9-1]_.

    Args:
        maxiter (int, optional): Maximun number of iterations.
            Defaults to 5.
        tol (float, optional): Tolerance allowable. The process will stop if
            :math:`\max_{i}|\delta_{i}^{(\nu)}-\delta_{i}^{(\nu-1)}|<tol`.
            Default sets to 1e-2.
        periodic (bool, optional): If is True the functions are considered
            periodical, if the basis of the functions is periodic it is used
            its own period, as in the case of :meth:`Fourier` basis, else
            are considerated periodic in the domain range, as in the
            periodic :meth:`BSplines` case. In general, it is not
            recommended this option for non periodic basis.
            If it is False the domain range of the functions are restricted
            to allow evaluated all the functions with their shifts.
            If 'default' are passed it is choosen according to the basis,
            being True for periodic basis and False in other cases.
        alpha (int or float, optional): Parameter to adjust the rate of
            convergence in the Newton-Raphson algorithm, see [RS05-7-9-1]_.
            Defaults to 1.
        initial (array_like, optional): Initial estimation of shifts.
            Default uses a list of zeros for the initial shifts.
        tfine (array_like, optional): Set of points where the
            functions are evaluated to obtain the discrete
            representation of the object to integrate. If none are passed
            it calls numpy.linspace with bounds equal to the ones defined in
            fd.domain_range and the number of points the maximum
            between 201 and 10 times the number of basis plus 1.
        shifts_array (bool, optional): If True returns an array with the
            shifts instead of a :obj:`FDataBasis` with the registered
            curves. Default sets to False.
        **kwargs: Keyword arguments to be passed to the :meth:`from_data`
            function.

    Returns:
        :obj:`FDataBasis` or :obj:`ndarray`: A :obj:`FDataBasis` object with
        the curves registered or if shifts_array is True a :obj:`ndarray`
        with the shifts.

    Raises:
        ValueError: If the initial array has different length than the
            number of samples.

    References:
        ..  [RS05-7-2] Ramsay, J., Silverman, B. W. (2005). Shift
            registration. In *Functional Data Analysis* (pp. 129-132).
            Springer.
        ..  [RS05-7-9-1] Ramsay, J., Silverman, B. W. (2005). Shift
            registration by the Newton-Raphson algorithm. In *Functional
            Data Analysis* (pp. 142-144). Springer.
    """

    # Initial estimation of the shifts
    if not len(initial):
        delta = numpy.zeros(fd.nsamples)

    elif len(initial) != fd.nsamples:
        raise ValueError("the initial shift ({}) must have the same length "
                         "than the number of samples ({})"
                         .format(len(initial), fd.nsamples))
    else:
        delta = numpy.asarray(initial)

    # Fine equispaced mesh to evaluate the samples
    if not len(tfine):
        nfine = max(fd.nbasis*10+1, 201)
        tfine = numpy.linspace(fd.basis.domain_range[0],
                               fd.basis.domain_range[1],
                               nfine)
    else:
        nfine = len(tfine)
        tfine = numpy.asarray(tfine)


    # Check how to extrapolate based on the argument ext
    periodic, periodic_ext = _check_extrapolation(fd, ext)

    # Auxiliar arrays to avoid multiple memory allocations
    delta_aux = numpy.empty(fd.nsamples)
    tfine_aux = numpy.empty(nfine)

    # Computes the derivate of originals curves in the mesh points
    D1x = fd.evaluate(tfine, 1)

    # Second term of the second derivate estimation of REGSSE. The
    # first term has been dropped to improve convergence (see references)
    d2_regsse = scipy.integrate.trapz(numpy.square(D1x), tfine, axis=1)

    max_diff = tol + 1
    iter = 0

    # Saves the array in all the interval if it will be adjusted to slice
    if not periodic:
        D1x_tmp = D1x
        tfine_tmp = tfine
        tfine_aux_tmp = tfine_aux
        domain = numpy.empty(nfine, dtype=numpy.dtype(bool))

    # Newton-Rhapson iteration
    while max_diff > tol and iter < maxiter:

        # Updates the limits for non periodic functions ignoring the ends
        if not periodic:
            # Calculates the new limits
            a = min(numpy.min(delta), 0)
            b = max(numpy.max(delta), 0)


            # The new interval is (domain[0] - a, domain[1] - b)
            numpy.logical_and(tfine_tmp >= fd.basis.domain_range[0] - a,
                              tfine_tmp <= fd.basis.domain_range[1] - b,
                              out=domain)
            tfine = tfine_tmp[domain]
            tfine_aux = tfine_aux_tmp[domain]
            D1x = D1x_tmp[:, domain]
            # Reescale the second derivate could be other approach
            # d2_regsse =
            # d2_regsse_original * ( 1 + (a - b) / (domain[1] - domain[0]))
            d2_regsse = scipy.integrate.trapz(numpy.square(D1x), tfine,
                                              axis=1)

        # Computes the new values shifted
        x = fd.evaluate_shifted(tfine, delta,
                                   ext=periodic_ext)
        x.mean(axis=0, out=tfine_aux)

        # Calculates x - mean
        numpy.subtract(x, tfine_aux, out=x)

        # REGSSE derivates are multiplied by 2
        d1_regsse = scipy.integrate.trapz(numpy.multiply(x, D1x, out=x),
                                          tfine, axis=1)
        # Updates the shifts by the Newton-Rhapson iteration
        # delta = delta - alpha * d1_regsse / d2_regsse
        numpy.divide(d1_regsse, d2_regsse, out=delta_aux)
        numpy.multiply(delta_aux, alpha, out=delta_aux)
        numpy.subtract(delta, delta_aux, out=delta)

        # Updates convergence criterions
        max_diff = numpy.abs(delta_aux, out=delta_aux).max()
        iter += 1

    # If shifts_array is True returns the delta array
    if shifts_array:
        return delta

    # Computes the values with the final shift to construct the FDataBasis
    return fd.shift(delta, ext = ext, tfine=tfine, **kwargs)


def landmark_shift(fd, landmarks, location='minimize', ext='default',
                   tfine=[], shifts_array=False, **kwargs ):
    r"""

    """

    if len(landmarks) != fd.nsamples:
        raise ValueError("landmark list ({}) must have the same length "
                         "than the number of samples ({})"
                         .format(len(landmarks), fd.nsamples))

    landmarks = numpy.asarray(landmarks)

    # Parses location
    if location == 'minimize':
        p = (numpy.max(landmarks) + numpy.min(landmarks)) / 2.
    elif location == 'mean':
        p = numpy.mean(landmarks)
    elif location == 'median':
        p = numpy.median(landmarks)
    elif location == 'middle':
        p = (fd.domain_range[1] + fd.domain_range[0]) / 2.
    else:
        try:
            p = float(location)
        except:
            raise ValueError("Invalid location, must be 'minimize', 'mean',"
                             " 'median','middle' or a number in the domain")

    shifts = landmarks - p

    if shifts_array:
        return shifts

    return fd.shift(shifts, ext = ext, tfine=tfine, **kwargs)
