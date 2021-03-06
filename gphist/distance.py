"""Cosmological distance model.
"""

import numpy as np

import gphist.cosmology

def convert_DC_to_DA(DH,DC,omega_k):
    """Applies curvature to convert DC(z) into DA(z).

    Args:
        DH(ndarray): input array with shape (nh,nz) of nh comoving distance
            functions DC(z) each tabulated at nz redshifts. Only the slice
            DH[:,0] corresponding to z=0 is actually used.
        DC(ndarray): input array with shape (nh,nz) of nh comoving distance
            functions DC(z) each tabulated at nz redshifts starting with z=0.
            The input values are overwritten with DA values.
        omega_k(float): curvature parameter Omega_k.

    Returns:
        ndarray: a reference to the input array DC which now contains
            values of DA.
    """
    n_sample,n_z = DH.shape
    if omega_k < 0:
        w = DH[:,0]/np.sqrt(-omega_k)
        w = np.tile(w[:,np.newaxis],(1,n_z))
        DC[:] = w*np.sin(DC/w)
    elif omega_k > 0:
        w = DH[:,0]/np.sqrt(+omega_k)
        w = np.tile(w[:,np.newaxis],(1,n_z))
        DC[:] = w*np.sinh(DC/w)
    return DC

class HubbleDistanceModel(object):
    """Models expansion history as multiplicative correction to the fiducial DH(z).

    Args:
        evol: evolution parameter to use, which must have a zvalues attribute
            and implement a get_DC method.
    """
    def __init__(self,evol):
        # Tabulate values of DH(z) for the fiducial model.
        self.DH0 = gphist.cosmology.get_DH(evol.zvalues)
        # Calculate the corresponding DC values.
        self.DC0 = evol.get_DC(self.DH0[np.newaxis,:])[0]

    def get_DH(self,samples):
        """Build expansion histories from Gaussian process samples.

        Each sample gamma(z) generates a Hubble distance function
        DH(z) = DH0(z)*exp(gamma(z)).

        Args:
            samples(ndarray): 2D array with shape (num_samples,num_steps)
                of num_samples samples gamma(z) tabulated at the num_steps
                redshifts z given in zvalues.

        Returns:
            ndarray: 1D array with shape (num_steps,) of tabulated DH(z) values.
        """
        return self.DH0*np.exp(samples)
