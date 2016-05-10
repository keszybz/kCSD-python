"""
This script is used to generate Current Source Density Estimates, 
using the kCSD method described in Ness et.al (2015) for 2D case.

This was written by :
Chaitanya Chintaluri, 
Laboratory of Neuroinformatics,
Nencki Institute of Exprimental Biology, Warsaw.
"""
import numpy as np
from scipy import integrate

from KCSD2D import KCSD2D

class MoIKCSD(KCSD2D):
    """MoIKCSD - CSD while including the forward modeling effects of saline.
    
    This estimates the Current Source Density, for a given configuration of 
    electrod positions and recorded potentials, in the case of 2D recording
    electrodes from an MEA electrode plane using the Method of Images. 
    The method implented here is based on kCSD method by Jan Potworowski 
    et.al. 2012, which was extended in Ness, Chintaluri 2015 for MEA.
    """
    def __init__(self, ele_pos, pots, **kwargs):
        """Initialize MoIKCSD Class. 

        Parameters
        ----------
        ele_pos : numpy array
            positions of electrodes
        pots : numpy array
            potentials measured by electrodes
        **kwargs
            configuration parameters, that may contain the following keys:
            src_type : str
                basis function type ('gauss', 'step', 'gauss_lim')
                Defaults to 'gauss'
            sigma : float
                space conductance of the medium
                Defaults to 1.
            sigma_S : float
                conductance of the saline (medium)
                Default is 5 S/m (5 times more conductive)
            n_src_init : int
                requested number of sources
                Defaults to 1000
            R_init : float
                demanded thickness of the basis element
                Defaults to 0.23
            h : float
                thickness of analyzed tissue slice
                Defaults to 1.
            xmin, xmax, ymin, ymax : floats
                boundaries for CSD estimation space
                Defaults to min(ele_pos(x)), and max(ele_pos(x))
                Defaults to min(ele_pos(y)), and max(ele_pos(y))
            ext_x, ext_y : float
                length of space extension: x_min-ext_x ... x_max+ext_x
                length of space extension: y_min-ext_y ... y_max+ext_y 
                Defaults to 0.
            gdx, gdy : float
                space increments in the estimation space
                Defaults to 0.01(xmax-xmin)
                Defaults to 0.01(ymax-ymin)
            lambd : float
                regularization parameter for ridge regression
                Defaults to 0.
            MoI_iters : int
                Number of interations in method of images.
                Default is 20
        Returns
        -------
        None
        """
        self.MoI_iters = kwargs.get('MoI_iters', 20)
        self.sigma_S = kwargs.get('sigma_S', 5.0)
        self.sigma = kwargs.get('sigma', 1.0)
        #Eq 6, Ness (2015)
        W_TS = (self.sigma - self.sigma_S) / (self.sigma + self.sigma_S) 
        self.iters = np.arange(self.MoI_iters) + 1
        self.iter_factor = W_TS**self.iters
        super(MoIKCSD, self).__init__(ele_pos, pots, **kwargs)
        return

    def forward_model(self, x, R, h, sigma, src_type):
        """FWD model functions
        Evaluates potential at point (x,0) by a basis source located at (0,0)
        Eq 22 kCSD by Jan,2012

        Parameters
        ----------
        x : float
        R : float
        h : float
        sigma : float
        src_type : basis_2D.key

        Returns
        -------
        pot : float
            value of potential at specified distance from the source
        """
        pot, err = integrate.dblquad(self.int_pot_2D_moi, -R, R, 
                                     lambda x: -R, 
                                     lambda x: R, 
                                     args=(x, R, h, src_type))
        pot *= 1./(2.0*np.pi*sigma)
        return pot

    def int_pot_2D_moi(self, xp, yp, x, R, h, basis_func):
        """FWD model function. Incorporates the Method of Images.
        Returns contribution of a point xp,yp, belonging to a basis source
        support centered at (0,0) to the potential measured at (x,0),
        integrated over xp,yp gives the potential generated by a
        basis source element centered at (0,0) at point (x,0)
        #Eq 20, Ness(2015)

        Parameters
        ----------
        xp, yp : floats or np.arrays
            point or set of points where function should be calculated
        x :  float
            position at which potential is being measured
        R : float
            The size of the basis function
        h : float
            thickness of slice
        basis_func : method
            Fuction of the basis source

        Returns
        -------
        pot : float
        """
        L = ((x-xp)**2 + yp**2)**(0.5)
        if L < 0.00001:
            L = 0.00001
        correction = np.arcsinh((h-(2*h*self.iters))/L) + np.arcsinh((h+(2*h*self.iters))/L)
        pot = np.arcsinh(h/L) + np.sum(self.iter_factor*correction)
        dist = np.sqrt(xp**2 + yp**2)
        pot *= basis_func(dist, R) #Eq 20, Ness et.al.
        return pot

if __name__ == '__main__':
    ele_pos = np.array([[-0.2, -0.2],[0, 0], [0, 1], [1, 0], [1,1], [0.5, 0.5],
                        [1.2, 1.2]])
    pots = np.array([[-1], [-1], [-1], [0], [0], [1], [-1.5]])
    k = MoIKCSD(ele_pos, pots,
                gdx=0.05, gdy=0.05,
                xmin=-2.0, xmax=2.0,
                ymin=-2.0, ymax= 2.0)
    k.cross_validate()
    #print k.values()



