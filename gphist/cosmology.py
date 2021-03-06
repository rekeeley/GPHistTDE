"""Homegenous cosmology.
"""

import numpy as np
import astropy.constants as const
import astropy.units as unit
import astropy.cosmology

def get_fiducial():
    """Returns the fiducial homogenous cosmology model.

    The fiducial model is derived from the Planck+WP best fit to flat LCDM in Ade 2013,
    given in the 6th column of Table 2 in the paper.
    """
    # Planck includes massive neutrinos in Om0 = Omega_matter(z=0) but astropy.cosmology
    # does not, so we subtract it here from the value Om0 = 0.3183 in Table 2.
    h = 0.6704
    mnu = 0.06
    Onu0 = (mnu/93.04)/h**2
    return astropy.cosmology.FlatLambdaCDM(
        H0=100*h,Om0=0.3183-Onu0,Tcmb0=2.7255,Neff=3.046,m_nu=(0.,0.,mnu)*unit.eV)


def get_DH(z,model=None):
    """Evaluates the distance function DH(z).

    Args:
        z(ndarray): Array of redshifts where DH(z) = c/H(z) should be evaluated.
        model: subclass of astropy.cosmology.FLRW that defines the homogeneous cosmology
            model to use. If None, uses get_fiducial().

    Returns:
        ndarray: Array of values of DH(z) = c/H(z) in Mpc.
    """
    if model is None:
        model = get_fiducial()
    return (const.c/model.H(z)).to('Mpc').value

def get_acceleration(z,DH):
    """Calculates the cosmic acceleration H(z)/(1+z).

    Args:
        z(ndarray): Array of redshifts where DH is tabulated.
        DH(ndarray): Array of Hubble distances DH(z) = c/H(z). Must have
            the same last dimension as z.

    Returns:
        ndarray: Array of calculated H(z)/(1+z) values with the same
            shape as the input DH array.
    """
    clight_km_per_sec = astropy.constants.c.to('km/s').value
    return clight_km_per_sec/DH/(1+z)

def get_omega_radiation(z,model=None):
    """Evaluates the physical radiation density.

    Evaluates the combined photon and neutrino (massless + massive) physical density
    using the WMAP7 treatment of massive neturinos (Komatsu et al. 2011, ApJS, 192, 18,
    section 3.3).

    Args:
        z(ndarray): Array of redshifts where DH(z) = c/H(z) should be evaluated.
        model: subclass of astropy.cosmology.FLRW that defines the homogeneous cosmology
            model to use. If None, uses get_fiducial().

    Returns:
        ndarray: Array of values of omega_r(z) = (Omega_gamma(z) + Omega_nu(z))*h0**2.
    """
    if model is None:
        model = get_fiducial()
    # FLRW densities Ox(z) are relative to the critical density at z, so rescale to
    # give desities relative to critical density at z = 0.
    rescale = (model.critical_density(z)/model.critical_density0).value
    return rescale*(model.Ogamma(z) + model.Onu(z))*model.h**2

def get_dark_energy_evolution(z,DH):
    """Calculates the dark energy density evolution.

    Args:
        z(ndarray): Array of redshifts where DH is tabulated.
        DH(ndarray): Array of Hubble distances DH(z) = c/H(z). Must have
            the same last dimension as z.

    Returns:
        ndarray: Array with shape (2,...) where (...) is the shape of DH. The
            [0] element gives values of omega_phi(z)/h0**2 for each entry in DH.
            The [1] element gives values of omega_phi(z)/h(z)**2 for each entry
            in DH.
    """
    nde = 2
    de_evol = np.empty(shape=(nde,)+DH.shape)
    zp1 = 1+z
    zp1_cubed = zp1**3
    # Calculate h(z) = H(z)/(100 km/s/Mpc).
    clight_km_per_sec = astropy.constants.c.to('km/s').value
    h_of_z = clight_km_per_sec/DH/100.
    # Calculate the physical matter density Omega_mat*h0**2 assuming that only
    # matter and radiation contribute at zmax.
    omega_radiation = get_omega_radiation(z)
    omega_matter = (h_of_z[...,-1]**2 - omega_radiation[-1])/zp1_cubed[-1]
    # Calculate the physical dark energy density Omega_phi(z)*h0**2 defined as
    # whatever is needed to make up h(z) after accounting for matter and radiation.
    # The result might be negative.
    omega_phi = (h_of_z**2 - omega_radiation) - omega_matter[...,np.newaxis]*zp1_cubed
    # Calculate omega_phi(z)/omega_phi(0).
    ##de_evol[?] = omega_phi/omega_phi[...,0,np.newaxis]
    # Calculate omega_phi(z)/h0**2
    de_evol[0] = omega_phi/h_of_z[...,0,np.newaxis]**2
    # Calculate omega_phi(z)/h(z)**2
    de_evol[1] = omega_phi/h_of_z**2
    return de_evol

def get_omega_matter_evolution(z,DH):
    """Calculates the dark energy density evolution.

        Args:
        z(ndarray): Array of redshifts where DH is tabulated.
        DH(ndarray): Array of Hubble distances DH(z) = c/H(z). Must have
        the same last dimension as z.

        Returns:
        ndarray: Array with shape (2,...) where (...) is the shape of DH. The
        [0] element gives values of omega_phi(z)/h0**2 for each entry in DH.
        The [1] element gives values of omega_phi(z)/h(z)**2 for each entry
        in DH.
        """
    zp1 = 1+z
    zp1_cubed = zp1**3
    # Calculate h(z) = H(z)/(100 km/s/Mpc).
    clight_km_per_sec = astropy.constants.c.to('km/s').value
    h_of_z = clight_km_per_sec/DH/100.
    # Calculate the physical matter density Omega_mat*h0**2 assuming that only
    # matter and radiation contribute at zmax.
    omega_radiation = get_omega_radiation(z)
    omega_matter = (h_of_z[...,-1]**2 - omega_radiation[-1])/zp1_cubed[-1]
    return omega_matter[...,np.newaxis]*zp1_cubed/h_of_z**2

def get_w_median(z,DE):
    """Calculates equation of state.

    Args:
        DE(ndarray): array of median dark energy density
        z(ndarray):array of redshifts (nsteps)

    Returns:
        ndarray: array of tabulated w(z) with the same
            shape as the input DE array. The [i,j] value gives w of sample i at
            zvalues[j].
    """
    # 1+w = -(1/3)rho'/rho where ' is deriv wrt lna i.e. dln rho / dlna
    a = 1./(1.+z[::-1])
    lna = np.log(a)
    lnrho = np.log(DE[::-1])
    lnrho_prime = np.gradient(lnrho,lna)
    return -1.-(1./3.)*lnrho_prime[::-1]
