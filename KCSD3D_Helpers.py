import numpy as np

def int_pot_3D_mc(xyz, x, R, h, basis_func):
    """
    The same as int_pot_3D, just different input: x,y,z <-- xyz (tuple)
    """
    xp, yp, zp = xyz
    return int_pot_3D(xp, yp, zp, x, R, h, basis_func)

def int_pot_3D(xp, yp, zp, x, R, h, basis_func):
    """
    FWD model functions
    Returns contribution of a point xp,yp, belonging to a basis source
    support centered at (0,0) to the potential measured at (x,0),
    integrated over xp,yp gives the potential generated by a
    basis source element centered at (0,0) at point (x,0)
    **Returns**
    pot : float
    """
    y = ((x-xp)**2 + yp**2 + zp**2)**0.5
    if y < 0.00001:
        y = 0.00001
    pot = 1.0/y
    pot *= basis_func(xp, yp, zp, [0, 0, 0], R)
    return pot

def gauss_rescale_3D(x, y, z, mu, three_stdev):
    """
    Returns normalized gaussian 3D scale function
    **Parameters**
    x, y, z : floats or np.arrays
        coordinates of a point/points at which we calculate the density
    
    mu : list
        distribution mean vector
    
    three_stdev : float
        3 * standard deviation of the distribution
    """
    stdev = three_stdev/3.0
    h = 1./(((2*np.pi)**0.5) * stdev)**3
    c = 0.5 * stdev**(-2)
    Z = h * np.exp(-c * ((x - mu[0])**2 + (y - mu[1])**2 + (z - mu[2])**2))
    return Z

def gauss_rescale_lim_3D(x, y, z, mu, three_stdev):
    """
    Returns gausian 3D distribution cut off after 3 standard deviations.
    """
    Z = gauss_rescale_3D(x, y, z, mu, three_stdev)
    Z = Z * ((x - mu[0])**2 + (y - mu[1])**2 + (z - mu[2])**2 < three_stdev**2)
    return Z

def step_rescale_3D(xp, yp, zp, mu, R):
    """
    Returns normalized 3D step function.
    **Parameters**
    xp, yp : floats or np.arrays
        point or set of points where function should be calculated
    
    mu : float
        origin of the function
    
    R : float
        cutoff range
    """
    s = 3/(4*np.pi*R**3)*(xp**2 + yp**2 + zp**2 <= R**2)
    return s

def make_src_3D(X, Y, Z, n_src, ext_x, ext_y, ext_z, R_init):
    """
    **Parameters**
    X, Y, Z : np.arrays
        points at which CSD will be estimated
    n_src : int
        desired number of sources we want to include in the model
    ext_x, ext_y, ext_z : floats
        how should the sources extend over the area X,Y,Z
    R_init : float
        demanded radius of the basis element
    **Returns**
    X_src, Y_src, Z_src : np.arrays
        positions of the sources in 3D space
    nx, ny, nz : ints
        number of sources in directions x,y,z
        new n_src = nx * ny * nz may not be equal to the demanded number of
        sources
        
    R : float
        updated radius of the basis element
    """
    Lx = np.max(X) - np.min(X)
    Ly = np.max(Y) - np.min(Y)
    Lz = np.max(Z) - np.min(Z)

    Lx_n = Lx + 2*ext_x
    Ly_n = Ly + 2*ext_y
    Lz_n = Lz + 2*ext_z

    (nx, ny, nz, Lx_nn, Ly_nn, Lz_nn, ds) = get_src_params_3D(Lx_n, 
                                                              Ly_n, 
                                                              Lz_n,
                                                              n_src)

    ext_x_n = (Lx_nn - Lx)/2
    ext_y_n = (Ly_nn - Ly)/2
    ext_z_n = (Lz_nn - Lz)/2

    lin_x = np.linspace(np.min(X) - ext_x_n, np.max(X) + ext_x_n, nx)
    lin_y = np.linspace(np.min(Y) - ext_y_n, np.max(Y) + ext_y_n, ny)
    lin_z = np.linspace(np.min(Z) - ext_z_n, np.max(Z) + ext_z_n, nz)

    (X_src, Y_src, Z_src) = np.meshgrid(lin_x, lin_y, lin_z)

    d = np.round(R_init/ds)
    R = d * ds

    return (X_src, Y_src, Z_src, R)

def get_src_params_3D(Lx, Ly, Lz, n_src):
    """
    Helps to evenly distribute n_src sources in a cuboid of size Lx * Ly * Lz
    **Parameters**
    Lx, Ly, Lz : floats
        lengths in the directions x, y, z of the area,
        the sources should be placed
    n_src : int
        demanded number of sources to be included in the model
    **Returns**
    nx, ny, nz : ints
        number of sources in directions x, y, z
        new n_src = nx * ny * nz may not be equal to the demanded number of
        sources
    Lx_n, Ly_n, Lz_n : floats
        updated lengths in the directions x, y, z
    ds : float
        spacing between the sources (grid nodes)
    """
    V = Lx*Ly*Lz
    V_unit = V / n_src
    L_unit = V_unit**(1./3.)

    nx = np.ceil(Lx / L_unit)
    ny = np.ceil(Ly / L_unit)
    nz = np.ceil(Lz / L_unit)

    ds = Lx / (nx-1)

    Lx_n = (nx-1) * ds
    Ly_n = (ny-1) * ds
    Lz_n = (nz-1) * ds
    return (nx, ny, nz,  Lx_n, Ly_n, Lz_n, ds)

basis_types = {
    "step": step_rescale_3D,
    "gauss": gauss_rescale_3D,
    "gauss_lim": gauss_rescale_lim_3D,
}

KCSD3D_params = {
    'sigma': 1.0,
    'n_srcs_init': 1000,
    'lambd': 0.0,
    'R_init': 0.23,
    'ext_x': 0.0,
    'ext_y': 0.0,
    'ext_z': 0.0,
    'h': 1.0,
}
