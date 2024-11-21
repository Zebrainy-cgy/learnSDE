import numpy as np
import matplotlib.pyplot as plt
from math import *
import scipy
from scipy import sparse
from numba import vectorize, float64
fft=np.fft.fft
fft2=np.fft.fft2
ifft=np.fft.ifft
ifft2=np.fft.ifft2


##############################################################################################
# special functions
@vectorize([float64(float64)])
def fNagumo(u):
    return u * (1 - u) * (u + 0.5)

@vectorize([float64(float64)])
def fAC(u):
    return u - u**3

def sep_exp(x1, x2, ell_1, ell_2):
    '''
    2D speratable exponential covariance function
    Input:
        x1, x2: coordinates
        ell_1, ell_2: corelated length
    Output:
        c: the covariance
    '''
    c = exp(- abs(x1) / ell_1 - abs(x2) / ell_2)
    return c

def gaussA_exp(x1, x2, a11, a22, a12):
    '''
    2D speratable exponential covariance function
    Input:
        x1, x2: coordinates
        A: 2*2 symmetric matrix
    Output:
        c: covariance
    '''
    c = exp(- ((x1 ** 2 * a11 + x2 ** 2 * a22) - 2 * x1 * x2 * a12))
    return c

def Whittle_Matern_Cov(t, q=0.5):
    '''
    Whittle Matern covariance, it is a stationary covariance function
    Input:
        t: time grid
        q: parameter to control the regularity
    Output:
        result: covariance value on t
    '''
    from scipy.special import kv
    factor = (2 ** (1 - q)) / gamma(q)
    # t = np.asarray(t)
    result = np.ones_like(t)
    non_zero_mask = t != 0
    result[non_zero_mask] = factor * (t[non_zero_mask] ** q) * kv(q, t[non_zero_mask])
    return result

##############################################################################################
# plot methods
def Plot_wireframe(x, y, z, rstride = 5, cstride = 5, colors = 'k', name:str='Figure'):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_wireframe(x, y, z, rstride=rstride, cstride=cstride, colors=colors)
    ax.set_xlabel(rf'$t$')
    ax.set_ylabel(rf'$x$')
    ax.set_zlabel(rf'$W$')
    ax.set_title(rf'{name}') 
    plt.show()
    return fig, ax

def Plot_contourf(x, y, z, levels:int=20, cmap:str='jet', name:str='Figure'):
    fig, ax = plt.subplots(figsize=(6, 4))
    pic = ax.contourf(x, y, z, levels=levels, cmap=cmap)
    plt.colorbar(pic, ax=ax)
    ax.set_xlabel(rf'$x$')
    ax.set_ylabel(rf'$y$')
    ax.set_title(rf'{name}') 
    plt.show()
    return fig, ax

def Plot(x, y, xlabel: str='x', ylabel: str='y', name:str='Figure', figsize: tuple = (6, 4)):
    plt.figure(figsize=figsize)
    plt.plot(x, y, 'k-')
    plt.xlabel(rf'{xlabel}')
    plt.ylabel(rf'{ylabel}')
    plt.title(rf'{name}')
    plt.show()

def Generate_GIF(x, y, ut):
    from matplotlib.animation import FuncAnimation, PillowWriter
    fig, ax = plt.subplots(figsize=(8, 6))
    N = ut.shape[2]
    cmap = 'jet' 
    contour = ax.contourf(x, y, ut[:, :, 0], levels=50, cmap=cmap)
    cbar = plt.colorbar(contour, ax=ax)
    cbar.set_label(r'$u$', fontsize=12)
    ax.set_xlabel(r'$x$', fontsize=12)
    ax.set_ylabel(r'$y$', fontsize=12)
    ax.set_title('Time Evolution of $u$ at t = 0', fontsize=14)

    def update(frame):
        ax.clear() 
        contour = ax.contourf(x, y, ut[:, :, frame], levels=50, cmap=cmap)
        ax.set_xlabel(r'$x$', fontsize=12)
        ax.set_ylabel(r'$y$', fontsize=12)
        ax.set_title(f'Time Evolution of $u$ at t = {frame}', fontsize=14)
        return contour

    ani = FuncAnimation(fig, update, frames=N + 1, blit=False)
    ani.save('evolution.gif', writer=PillowWriter(fps=100))
    plt.show()

##############################################################################################
# stochastic process
def BrownianMotion(T, N, seed=None):
    '''
    Input:
        T: time doamin [0, T]
        N: partition number of time
        sedd: random seed = None as default
    Output:
        t, X
    '''
    X = np.zeros(N + 1)
    t = np.linspace(0, T, N + 1)
    X[0] = np.array(0)
    np.random.seed(seed)
    xi = np.random.randn(N)
    for i in range(1, N+1):
        dt = t[i] - t[i-1]
        X[i] = X[i-1] + sqrt(dt)*xi[i-1]
    return t, X

def BrownianBridge(T, N, seed=None):
    '''
    Brownian Bridge
    Input:
        T: time domain [0, T]
        N: partition into N intervals
    Output:
        t, B
    '''
    t, W = BrownianMotion(T, N, seed=seed)
    B = W - W[-1] * (t - t[0]) / (t[-1] - t[0])
    return t, B

##############################################################################################
# some processes sampled by discrete KL expansion(spectral decomposition of covariance matrix)

def GP_Exponential_KL(T, N, l, seed=None):
    '''
    Gaussian process with exponential covariance
    Input:
        T: time domain [0, T]
        N: partition into N intervals
        l: param of exponential covariance function
        seed: random seed
    Output:
        t, X
    '''
    t = np.linspace(0, T, N + 1)
    C = np.zeros((N + 1, N + 1))
    for i in range(N + 1):
        for j in range(N + 1):
            ti = t[i]; tj = t[j]
            C[i, j] = exp(-abs(ti-tj)/l)
    S, U = np.linalg.eig(C)
    np.random.seed(seed)
    xi = np.random.randn(N + 1)
    X = np.dot(U, S**0.5 * xi)
    return t, X

def GP_Gaussian_KL(T, N, l, seed=None):
    '''
    Gaussian process with gaussian covariance
    Input:
        T: time domain [0, T]
        N: partition into N intervals
        l: param of gaussian covariance function
        seed: random seed
    Output:
        t, X
    '''
    t = np.linspace(0, T, N + 1)
    C = np.zeros((N + 1, N + 1))
    for i in range(N + 1):
        for j in range(N + 1):
            ti = t[i]; tj = t[j]
            C[i, j] = exp(-(ti-tj)**2/l**2)
    S, U = np.linalg.eig(C)
    np.random.seed(seed)
    xi = np.random.randn(N + 1)
    X = np.dot(U, S**0.5 * xi)
    return t, X

def Gaussian_Whittle_Matern_KL(t, q, seed=None):
    N = t.size
    C = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            ti = t[i]; tj = t[j]
            h = abs(ti - tj)
            C[i, j] = Utils.Whittle_Matern_Cov(h, q)
    S, U = np.linalg.eig(C)
    np.random.seed(seed)
    xi = np.random.randn(N) 
    X = np.dot(U, S**0.5 * xi)
    return X  


##############################################################################################
# Circulant Embedding method for stochastic process, stationary process
def Circulant_Sample(c):
    '''
    C is circculant matrix, smaple by circualnt sampling method
    Input:
        c: the first column of C(A circulant matrix)
    Output:
        X, Y: two uncorrelated processes
    '''
    N = c.size
    d = np.fft.ifft(c) * N
    xi = np.dot(np.random.randn(N, 2), [1, 1j])
    Z = np.fft.fft(d**0.5 * xi) / sqrt(N)
    X = np.real(Z)
    Y = np.imag(Z)
    return X, Y

def Circulant_Embed_Sample(c):
    '''
    C is a symmetric Toeplitz matrix, sample by circulant embedding
    Input:
        c: first column of C
    Output:
        X, Y: two uncorrelated processes
    '''
    N = c.size
    c_tilde = np.hstack([c, c[-2:0:-1]])
    X, Y = Circulant_Sample(c_tilde)
    X = X[0:N]
    Y = Y[0:N]
    return X, Y

def Circulant_Embed_Approx(c):
    '''
    circulant embedding method with padding
    Input:
        c: the first column of Toeplitz matrix after padding
    Output:
        X, Y: two uncorrelated processes
    '''
    c_tilde = np.hstack([c, c[-2:0:-1]])
    N_tilde = c_tilde.size
    d = np.real(np.fft.ifft(c_tilde)) * N_tilde
    d_minus = np.maximum(-d, 0)
    d_pos = np.maximum(d, 0)
    if (np.max(d_minus) > 0):
        print(f'rho(D_minus) = {np.max(d_minus):.4e}')
    xi=np.dot(np.random.randn(N_tilde, 2), [1, 1j])
    Z = np.fft.fft(d_pos**0.5 * xi) / sqrt(N_tilde)
    N = c.size
    X=np.real(Z[0:N]);    Y=np.imag(Z[0:N])
    return X, Y


def Circlulant_Exponential(t, l):
    ''' 
    t must be positioned uniformly
    '''
    c = np.exp(- np.abs(t) / l)
    X, Y = Circulant_Embed_Sample(c)
    return X, Y

def rho_D_minus(c):
    c_tilde = np.hstack([c, c[-2:0:-1]])
    N_tilde = c_tilde.size
    d = np.real(np.fft.ifft(c_tilde)) * N_tilde
    d_minus = np.maximum(-d, 0)
    return np.max(d_minus)

def rho_WM(N, dt, q):
    M = np.linspace(100, 10000, 100)
    rho = np.zeros(M.size)
    for i, m in enumerate(M):
        m = int(m)
        Ndash = N + m - 1
        T=(Ndash+1)*dt
        t=np.linspace(0,T,Ndash+1)
        c = rho_D_minus(Whittle_Matern_Cov(t, q))
        rho[i] = c
    return  N+M, rho

def Circulant_Approx_WM(N, M, dt, q):
    Ndash = N + M - 1
    T = (Ndash + 1) * dt
    t = np.linspace(0, T, Ndash+1)
    c = Whittle_Matern_Cov(t, q)
    X, Y = Circulant_Embed_Approx(c)
    X = X[0:N];    Y = Y[0:N];    t = t[0:N]
    return t, X, Y, c

##############################################################################################
# Circulant Embedding method for stationary process

def Reduced_Cov(n1, n2, dx1, dx2, c):
    '''
    given a covariance function c, get the reduced vector of covariance matrix.
    Input:
        n1, n2: resolution of x, y axis respectively
        dx1:
        dx2:
        c: the covariance function, take two params as input
    Output:
        C_red: reduced vector of covariance matrix
    '''
    C_red = np.zeros((2*n1 - 1, 2*n2 - 1))
    for i in range(2*n1 - 1):
        for j in range(2*n2 - 1):
            C_red[i, j] = c((i+1-n1)*dx1, (j+1-n2)*dx2)
    return C_red

def Circulant_Sample_2d(C_red, n1, n2, seed = 24):
    '''
    If the covariance matrix is BCCB matrix with reduced vector C_red, use cirrculant embedding method to sample 2D random field.
    Input:
        C_red: the reduced vector of covariance matrix
        n1: resolution of x axis
        n2: resolution of y axis
    Output:
        X, Y: two unrealted realizations
    '''
    N = n1 * n2
    Lam = N * np.fft.ifft2(C_red)
    d = np.ravel(np.real(Lam))
    d_minus = np.maximum(- d, 0)
    if np.max(d_minus > 0):
        print(f'rho(D_minus)={np.max(d_minus)}')
    np.random.seed(seed)
    xi = np.random.randn(n1, n2) + 1j*np.random.randn(n1, n2)
    V = (Lam ** 0.5)*xi
    Z = np.fft.fft2(V) / sqrt(N)
    X = np.real(Z);    Y = np.imag(Z)
    return X, Y

def Circulant_Embed_Sample_2d(C_red, n1, n2, seed = None):
    '''
    If the covariance matrix is BTTB matrix, embed the matrix into BCCB to sample.
    Input:
        C_red: reduced vector of covariance matrix
        n1, n2: resolution of x, y axis
        seed: the random seed, default as None
    Output:
        u1, u2: uncorrelated realizations
    '''
    N = n1 * n2
    tilde_C_red = np.zeros((2 * n1, 2 * n2))
    tilde_C_red[1:2*n1, 1:2*n2] = C_red
    tilde_C_red = np.fft.fftshift(tilde_C_red)
    u1, u2 = Circulant_Sample_2d(tilde_C_red, 2*n1, 2*n2, seed)
    u1 = np.ravel(u1);  u2=np.ravel(u2)
    u1 = u1[0:2*N]; u1 = u1.reshape((n1,2 * n2)); u1 = u1[:,::2]
    u2 = u2[0:2*N]; u2 = u2.reshape((n1,2 * n2)); u2 = u2[:,::2]
    return u1, u2

def Circulant_Embed_Approx_2d(C_red, n1, n2, m1, m2, seed = None):
    '''
    Circulant embedding with padding.
    Input:
        C_red: the reduced vvector of covariance matrix
        n1, n2: resolution of x, y axis
        m1, m2: padding size of x, y axis
        seed: random seed, default as None
    Output:
        u1, u2: uncorrelated realizations
    '''
    nn1 = n1 + m1;    nn2 = n2 + m2
    N = nn1 * nn2
    tilde_C_red = np.zeros((2 * nn1, 2 * nn2))
    tilde_C_red[1:2 * nn1, 1:2 * nn2] = C_red
    tilde_C_red = np.fft.fftshift(tilde_C_red)
    u1, u2 = Circulant_Sample_2d(tilde_C_red, 2 * nn1, 2 * nn2, seed)
    # print(u1.shape, u2.shape)
    u1 = np.ravel(u1);    u2 = np.ravel(u2)
    u1 = u1[0:2 * N];    u1 = u1.reshape((nn1, 2 * nn2));    u1 = u1[0:n1, 0:2*n2:2]
    u2 = u2[0:2 * N];    u2 = u2.reshape((nn1, 2 * nn2));    u2 = u2[0:n1, 0:2*n2:2]
    return u1, u2

##############################################################################################
# 1D stationary FEM
def Get_Ele_Info(h, p, q, f, ne):
    '''
    Get local FEM information of 1D problem
    Input: 
        h: the uniform length of interval
        p: diffusion coefficient p(x)
        q: mass coefficients q(x)
        ne: number of elements
    Output:
        Kks: element diffusion matrices
        Mks: element mass matrices
        bks: element vectors
    '''
    Kks = np.zeros((ne, 2, 2));    
    Kks[:, 0, 0] = p/h; Kks[:, 0, 1] = -p/h; Kks[:, 1, 0] = -p/h; Kks[:, 1, 1] = p/h
    Mks = np.zeros_like(Kks)
    Mks[:, 0, 0] = q*h/3; Mks[:, 0, 1] = q*h/6; Mks[:, 1, 0] = q*h/6; Mks[:, 1, 1] = q*h/3
    bks = np.zeros((ne, 2))
    bks[:, 0] = f*(h / 2); bks[:, 1] = f*(h / 2)
    return Kks, Mks, bks


def FEM_Solver1D_r1(ne, p, q, f):
    '''
    Solve 1D BVP wiith homogenous boundary conditions by FEM using linear basis.
    Input:
        ne: number of elements
        p: diffusion coefficients
        q: mass coefficients
        f: source term
    Output:
        x: gird points
        uh: solution
        A: FEM matrix
        b: rhs
        K: Diffusion matrix
        M: Mass matrix
    '''
    h = 1 / ne
    x = np.linspace(0, 1, ne + 1)
    nvtx = ne + 1
    Kks, Mks, bks = Get_Ele_Info(h, p, q, f, ne)
    elt2vert = np.vstack((np.arange(0, nvtx - 1, dtype = 'int'), np.arange(1, nvtx, dtype = 'int')))
    b = np.zeros(nvtx)
    K = sum(sparse.csc_matrix((Kks[:, row_no, col_no], (elt2vert[row_no, :], elt2vert[col_no, :])), (nvtx, nvtx)) for row_no in range(2)  for col_no in range(2))
    M = sum(sparse.csc_matrix((Mks[:, row_no, col_no], (elt2vert[row_no, :], elt2vert[col_no, :])), (nvtx, nvtx)) for row_no in range(2)  for col_no in range(2))
    for row_no in range(2):
        nrow = elt2vert[row_no, :]
        b[nrow] = b[nrow] + bks[:, row_no]
    A = K + M
    # impose homogeneous boundary condition
    A = A[1:-1, 1:-1]; K = K[1:-1, 1:-1]; M = M[1:-1, 1:-1]
    b = b[1:-1]
    # solve linear system for interior degrees of freedom
    u_int = sparse.linalg.spsolve(A, b)
    # add in boundary data 
    uh = np.hstack([0, u_int, 0])
    # plotting commands removed 
    return x, uh, A, b, K, M

def oned_linear_FEM_b(ne, h, f):
    nvtx = ne + 1
    elt2vert = np.vstack([np.arange(0, ne, dtype = 'int'), 
                        np.arange(1, (ne + 1), dtype = 'int')])
    bks = np.zeros((ne, 2));    b = np.zeros(nvtx) 
    bks[:, 0] = f[:-1]*(h / 3) + f[1:]*(h / 6)
    bks[:, 1] = f[:-1]*(h / 6) + f[1:]*(h / 3)
    for row_no in range(0, 2):
        nrow = elt2vert[row_no, :]
        b[nrow] = b[nrow]+bks[:, row_no]
    b = b[1:-1]
    return b

##############################################################################################
# 2D stationary FEM
def Uniform_Mesh(ns):
    '''
    Generate uniformly mesh, grid index from left bottom to right top. Vertex of element is by anticlockwise 
    Input:
        ns: number of partition on each edge of square domain
    Output:
        h: length of each interval
        xv, yv:  x, y value of grid points
        elt2vert: vertices index of each triangular element
        nvtx: number of vertices 
        ne: number of elements
    '''
    n = ns + 1
    h = 1/ns
    x = np.linspace(0, 1, ns+1)
    y = np.linspace(0, 1, ns+1)
    xv, yv = np.meshgrid(x, y)
    xv = xv.ravel()
    yv = yv.ravel()
    nvtx = n**2
    nsqr = ns**2
    ne = 2*nsqr
    elt2vert = np.zeros((ne, 3), dtype='int')
    vv=np.reshape(np.arange(0, nvtx),(ns + 1,ns + 1), order='F')
    v1=vv[:-1, :-1]; v2=vv[1:, :-1]; v3=vv[:-1, 1:]; v4=vv[1:, 1:]
    elt2vert[:nsqr, :] = np.vstack((v1.ravel(), v2.ravel(), v3.ravel())).T
    elt2vert[nsqr:, :] = np.vstack((v4.ravel(), v3.ravel(), v2.ravel())).T
    # plot the Mesh
    # plt.figure(figsize=(8, 6)) 
    # plt.axis('equal')
    # plt.triplot(xv.ravel(),yv.ravel(), elt2vert, 'k-')
    # plt.xlabel(r'$x_1$')
    # plt.ylabel(r'$x_2$')
    return h, xv, yv, elt2vert, nvtx, ne

def Get_Jacobian_Info(xv, yv, ne, elt2vert):
    '''
    Get the Jacobi matrix of each elements
    Input:
        xv, yv: the x, y value of each grid point
        ne: number of elements(2*ns^2)
        elt2vert: index of each element
    Output:
        Jks: Jacobi matrix of each element
        invJks: inverse Jacobi matrix
        detJks: determinate of Jacobi matrices
    '''
    Jks = np.zeros((ne, 2, 2))
    invJks = np.zeros((ne, 2, 2))
    x1 = xv[elt2vert[:, 0]]; x2 = xv[elt2vert[:, 1]]; x3 = xv[elt2vert[:, 2]]
    y1 = yv[elt2vert[:, 0]]; y2 = yv[elt2vert[:, 1]]; y3 = yv[elt2vert[:, 2]]
    Jks[:, 0, 0] = x2 - x1; Jks[:, 0, 1] = y2 - y1
    Jks[:, 1, 0] = x3 - x1; Jks[:, 1, 1] = y3 - y1
    detJks = Jks[:, 0, 0]*Jks[:, 1, 1]-Jks[:, 0, 1]*Jks[:, 1, 0]
    invJks[:, 0, 0] = (y3 - y1)/detJks
    invJks[:, 0, 1] = (y1 - y2)/detJks
    invJks[:, 1, 0] = (x1 - x3)/detJks
    invJks[:, 1, 1] = (x2 - x1)/detJks
    return Jks, invJks, detJks

def Get_Integration_Info_r1(ne, invJks, detJks, a, f):
    '''
    Collection of local matrix on each element using linear nodal basis.
    Input:
        ne: bumber of elements
        invJks: inverse of Jacobian
        detJks: determinate of Jacobian
        a: space domain [0, a]
        f: source term f(x)
    Output:
        Ak, bk: local matrix of each element
    '''
    Ak = np.zeros((ne, 3, 3))
    bk = np.zeros((ne, 3))
    dpsi_ds = np.array([-1, 1, 0])
    dpsi_dt = np.array([-1, 0, 1])
    for i in range(3):
        for j in range(3):
            grad=np.array([[dpsi_ds[i],dpsi_ds[j]],
                           [dpsi_dt[i],dpsi_dt[j]]])       
            v1=np.dot(invJks[:,:,:], grad[:, 0])
            v2=np.dot(invJks[:,:,:], grad[:, 1])
            tmp = detJks * np.sum(v1 * v2, axis=1)
            Ak[:,i,j] = Ak[:,i,j] + a*tmp/ 2
        bk[:,i]=bk[:,i] + f*detJks / 6
    return Ak, bk

def FEM_Solver2D_r1(ns, xv, yv, elt2vert, nvtx, ne, a, f):
    '''
    2D FEM solver
    Input:
        ns: number of partition on each edge of square domain
        xv, yv: the x, y value of each grid point
        elt2vert: index of each element
        nvtx: number of vertices
        ne: number of elements(2*ns^2)
        a: spatial domain [0, a]
        f: source term f(x)
    Output:
        uh: solution of u
        u_int: solution on inner points
        A_int: inner part of A
        rhs: inner part of b
    '''
    Jks, invJks, detJks = Get_Jacobian_Info(xv, yv, ne, elt2vert)
    Aks, bks = Get_Integration_Info_r1(ne, invJks, detJks, a, f)
    A = sparse.csc_matrix((nvtx, nvtx))
    A = sum(sparse.csc_matrix((Aks[:, row_no, col_no], (elt2vert[:, row_no], elt2vert[:, col_no])), (nvtx, nvtx)) for row_no in range(3)  for col_no in range(3))
    b = np.zeros(nvtx)
    for k in range(3):
        nrow = elt2vert[:, k]
        b[nrow] = b[nrow] + bks[:, k]
    # get discrete Dirichlet boundary data 
    b_nodes = np.where((xv == 0) | (xv == 1) | (yv == 0) | (yv == 1))[0]
    int_nodes = np.ones(nvtx, dtype='bool');    
    int_nodes[b_nodes]=False;    
    b_int = np.squeeze(b[int_nodes])
    # print(b_int)
    wB = g_eval(xv[b_nodes], yv[b_nodes])
    # solve linear system for interior nodes;
    Ab = A[int_nodes, :]; Ab = Ab[:, b_nodes]
    rhs = b_int - Ab.dot(wB)
    A_int = A[int_nodes, :]; A_int=A_int[:, int_nodes]
    u_int = sparse.linalg.spsolve(A_int,rhs)
    # combine with boundary data and plot
    uh = np.zeros(nvtx)
    uh[int_nodes] = u_int
    uh[b_nodes] = wB
    return uh, u_int, A_int, rhs

def g_eval(x,y):
    '''
    Input:
        x, y: coordinates
    Ouput:
        g: boundary value
    '''
    g=np.zeros(x.shape)
    return g      

##############################################################################################
# Time-dependent PDE
def Pde_MOL_FDM_1D_Semilinear(u0, T, a, N, J, epsilon, fhandle, bctype):
    '''
    Solve semilinear PDE with method of line for time and FDM for space
    Input:
        u0: initial condition
        T: time domain [0, T]
        a: space domain [0, a]
        N: number of temporal intervals
        J: number of spatial intervals
        epsilon: param of semilinear PDE
        fhandle: nonlinear term f(u)
        bdtype: 'd' for Dirichlet; 'p' for Period; 'n' for Nuemann
    Ouput:
        t, x: time grids and space grids
        ut: [J + 1, N + 1] space-time solution
    '''
    Dt = T / N;     
    t = np.linspace(0, T, N + 1)
    h = a / J
    x = np.linspace(0, a, J + 1)
    # set matrix A according to boundary conditions
    A = scipy.sparse.diags([-1, 2, -1], [-1, 0, 1],  shape = (J+1, J+1), format = 'csc')
    if 'd' == bctype.lower():
        ind = np.arange(1, J)
        A = A[:, ind]
        A = A[ind, :]
    else:
        if 'p' == bctype.lower():
            ind = np.arange(0, J)
            A = A[:, ind]; A = A[ind, :]
            A[1, -1] = -1; A[-1, 1] = -1
        elif 'n' == bctype.lower():
            ind = np.arange(0, J + 1)
            A[0, 1] = -2; A[-1, -2] = -2 
    EE = scipy.sparse.identity(ind.size, format = 'csc') + (Dt * epsilon/h**2) * A 
    ut = np.zeros((J + 1, t.size)) # initialize vectors
    ut[:, 0] = u0; u_n = u0[ind] # set initial condition
    #
    EEinv = sparse.linalg.factorized(EE)
    #
    for k in range(N): # time loop
        fu = fhandle(u_n) # evaluate f(u_n)
        u_n = EEinv(u_n + Dt * fu) # linear solve for EE
        ut[ind, k + 1] = u_n
    if bctype.lower() == 'p':
        ut[-1, :] = ut[0, :] # correct for periodic case  
    return t, x, ut

def Pde_MOL_Galerkin_1D_Semilinear(u0, T, a, N, J, epsilon, fhandle):
    """
    Use semi-implicit Euler method plus Galerkin method to solve 1d semilinear equation with periodic boundary
    Input:
        u0: initial condition
        T: time domain [0, T]
        a: space domain [0, a]
        N: number of time intervals
        J: number of space intervals
        epsilon: param of semilinear equation
        fhandle: nonlinear term f(u)
    Output:
        t, x: time grids and space grids
        ut: [J + 1, N + 1] space-time solution
    """
    Dt = T/N
    t = np.linspace(0, T, N+1)
    x = np.linspace(0, a, J+1)
    ut = np.zeros((J + 1, N + 1))
    # set linear operator 
    lam = (2 * pi/ a) * np.hstack([np.arange(0, J / 2+1), np.arange(- J / 2 + 1, 0)]) 
    M = epsilon * lam ** 2
    EE = 1.0 / (1 + Dt * M) # diagonal of (1+ Dt M)^{-1}
    ut[:, 0] = u0;    u = u0[0:J];     uh = fft(u) # set initial condition
    #
    for n in range(0, N): # time loop
        fhu = fft(fhandle(u)) # evaluate fhat(u)
        uh = EE*(uh + Dt * fhu) # semi-implicit Euler step
        u = np.real(ifft(uh))
        ut[0:J, n + 1] = u
    ut[J, :] = ut[0, :] # make periodic
    return t, x, ut

def Pde_MOL_Galerkin_2D_Semilinear(u0, T, a, N, J, epsilon, fhandle):
    """
    Use semi-implicit Euler method plus Galerkin method to solve 2d semilinear equation with periodic boundary
    Input:
        u0: initial condition
        T: time domain [0, T]
        a: space domain [0, a]
        N: number of time intervals
        J: number of space intervals
        epsilon: param of semilinear equation
        fhandle: nonlinear term f(u)
    Output:
        t, x: time grids and space grids
        ut: [J + 1, N + 1] space-time solution
    """
    Dt = T / N
    t = np.linspace(0, T, N+1)
    x  =  np.linspace(0,  a,  J + 1)
    ut = np.zeros((J[0] + 1, J[1] + 1, N+1))
    # set linear operators
    lambdax = (2*pi/a[0]) * np.hstack([np.arange(0, J[0] / 2+1), np.arange(- J[0] / 2 + 1, 0)])
    lambday = (2*pi/a[1]) * np.hstack([np.arange(0, J[1] / 2+1), np.arange(- J[1] / 2 + 1, 0)])
    lambdaxx, lambdayy = np.meshgrid(lambdax, lambday, indexing = 'ij')
    M = epsilon * (lambdaxx ** 2 + lambdayy ** 2)
    EE = 1.0 / (1 + Dt * M)
    ut[:, :, 0] = u0;  u = u0[0:-1, 0:-1];  uh = fft2(u)# set initial data 
    for n in range(N): # time loop
        fhu = fft2(fhandle(u)) # compute fhat
        uh_new = EE*(uh + Dt * fhu)
        u = np.real(ifft2(uh_new))
        ut[0:J[0], 0:J[1], n + 1] = u
        uh = uh_new
    ut[J[0], :, :] = ut[0, :, :]
    ut[:, J[1] , :] = ut[:, 0, :] # make periodic
    return t, x, ut

def oned_linear_FEM_b_r1(ne, h, f):
    '''
    Project f(u_J to \hat{u_J})
    Input:
        ne: number of space intervals
        h: length of each interval
        f: f(u)
    Output:
        b: <f(u), \phi_j>_{L^2}
    '''
    nvtx = ne + 1
    elt2vert = np.vstack([np.arange(0, ne, dtype='int'), np.arange(1, (ne + 1), dtype='int')])
    bks = np.zeros((ne, 2));    
    b = np.zeros(nvtx) 
    bks[:, 0] = f[:-1]*(h / 3) + f[1:]*(h / 6)
    bks[:, 1] = f[:-1]*(h / 6) + f[1:]*(h / 3)
    for row_no in range(0,2):
        nrow = elt2vert[row_no, :]
        b[nrow] = b[nrow] + bks[:, row_no]
    b=b[1:-1]
    return b

def Pde_MOL_FEM_1D_Semilinear_r1(u0, T, a, N, ne, epsilon, fhandle):
    """
    Use semi-implicit Euler method plus FEM with linear basis to solve 1d semilinear equation with dirichlet boundary
    Input:
        u0: initial condition
        T: time domain [0, T]
        a: space domain [0, a]
        N: number of time intervals
        ne: number of space intervals
        epsilon: param of semilinear equation
        fhandle: nonlinear term f(u)
    Output:
        t, x: time grids and space grids
        ut: [nvtx, N + 1] space-time solution
    """
    h = a / ne;    nvtx=ne + 1;    Dt=T / N
    t = np.linspace(0, T, N+1)
    p = epsilon
    q = 1
    f = 1
    x, uh, A, b, KK, MM = FEM_Solver1D_r1(ne, p, q, f)
    EE = (MM + Dt * KK)
    # set initial condition
    ut=np.zeros((nvtx,N + 1))
    ut[:, 0] = u0
    u = np.copy(u0)
    EEinv = sparse.linalg.factorized(EE)
    for n in range(N):# time loop
        fu = fhandle(u)
        b = oned_linear_FEM_b(ne, h, fu)
        u_new = EEinv(MM.dot(u[1:-1]) + Dt * b)
        u = np.hstack([0, u_new, 0])
        ut[:, n + 1] = u
    return t, x, ut

##############################################################################################
# SPDE with random data



##############################################################################################
# 1D H^r_0([0, a])-valued Weiner Process
def icspde_dst1(u):
    return scipy.fftpack.dst(u, type=1, axis=0)/2

def get_onedD_bj(dtref, J, a, r):
    '''
    Input:
        dtref: the reference length of time interval
        J: number of sample points x_k
        a: domain [0, a]
        r: H^r_0([0, a])
    Output:
        bj: coefficients
    '''
    eps=0.001
    return np.sqrt(2 * dtref * np.arange(1,J) ** (-(2 * r + 1 + eps)) / a)

def get_onedD_dW(bj, kappa, iFspace, M):
    '''
    Input:
        bj: coefficients
        kappa: dt = kappa * dt_{ref}
        iFspace: a flag
        M: number of independent realizations to compute
    Output:
        dW
    '''
    if (kappa == 1):
        nn = np.random.randn(M, bj.size)
    else:
        nn = np.sum(np.random.randn(kappa, M, bj.size), axis=0)
    X = bj * nn
    if iFspace == 1:
        dW=X
    else:
        dW = icspde_dst1(np.squeeze(X))
        dW = dW.reshape(X.shape)
    return dW

##############################################################################################
# 1D H^r_{per}([0, a])-valued Weiner Process
def Get_oned_bj(dtref, J, a, r):
    j = np.hstack([np.arange(1, J//2 + 1), np.arange(-J//2+1, 0)])
    eps = 0.001
    qj = np.hstack([[0], np.abs(j)**(-(2*r + 1 + eps)/2)])
    bj = np.sqrt(qj * dtref / a) * J
    return bj

def Get_oned_dW(bj, kappa, iFspace, M):
    J = bj.size
    if kappa == 1:
        nn = np.random.randn(M, J)
    else:
        nn = np.sum(np.random.randn(kappa, M, J), 0)
    nn = np.vstack([nn[0:1, :], (nn[1:J//2, :] + 1j * nn[J//2 + 1:J, :]) / sqrt(2),
                   nn[J//2:J//2+1, :], (nn[J//2-1:0:-1, :] - 1j * nn[J-1:J // 2 :-1, :])/ sqrt(2)])
    X = bj * nn
    if iFspace == 1:
        dW = X
    else:
        dW = np.real(ifft(X))
    return dW

##############################################################################################
# 2D Q-Weiner Process L^2(D)
def Get_twod_bj(dtref, J, a, alpha):
    '''
    Input:
        dtref: the reference time interval
        J: number of sample points [J1, J2]
        a: 2D domain [0, a1] * [0, a2]
        alpha: parameter of Q
    Output:
        bj: coefficients
    '''
    lambdax = 2 * pi * np.hstack([np.arange(0,J[0]//2 +1), np.arange(- J[0]//2 + 1,0)]) / a[0]
    lambday = 2 * pi * np.hstack([np.arange(0,J[1]//2 +1), np.arange(- J[1]//2 + 1,0)]) / a[1]
    lambdaxx, lambdayy = np.meshgrid(lambdax, lambday, indexing='ij')
    sqrt_qj = np.exp(- alpha * (lambdaxx ** 2 + lambdayy ** 2))
    bj = sqrt_qj * sqrt(dtref) * J[0] * J[1] / sqrt(a[0] * a[1])
    return bj

def Get_twod_dW(bj, kappa, M):
    '''
    Input:
        bj: coefficient
        kappa: dt = kappa * dt_{ref}
        M: generate M independent realization
    Output:
        return dW1, dW2
    '''
    J = bj.shape
    if (kappa == 1):
        nn = np.random.randn(M,J[0],J[1],2)
    else:
        nn = np.sum(np.random.randn(kappa,M,J[0],J[1],2),0)
    nn2 = np.dot(nn,np.array([1,1j]))
    tmp = ifft2(bj*nn2)
    dW1 = np.real(tmp)
    dW2 = np.imag(tmp)
    return dW1, dW2



##############################################################################################
# solve spde with Euler-Maruyama Method and FDM
def Spde_EM_FDM_Nagumo_Exponential(u0, T, a, N, J, epsilon, sigma, ell, fhandle):
    '''
    Nagumo SPDE with Exponential Covariance and homogeneous Neumann boundary condition with initial condition u0
    Input:
        u0: the initial value of u(t, x)
        T: time boundary [0, T]
        a: x intervel [0, a]
        N: number of time intervals
        J: number of space intervals
        epsilon: parameter of Nagumo equation
        sigma: addictive noise parameter
        ell: parameter of exponential covariance
        fhandle: nonlinear term f(u)
    Output:
        t, x, ut
    '''
    dt = T / N
    t = np.linspace(0, T, N + 1)
    x = np.linspace(0, a, J + 1)
    h = a / J
    A = scipy.sparse.diags([-1, 2, -1], [-1, 0, 1], shape=(J + 1, J + 1), format='csc')
    ind = np.arange(0, J + 1)
    A[0, 1] = 2
    A[-1, -2] = 2
    EE = scipy.sparse.identity(ind.size, format='csc') + (dt * epsilon/h**2) * A
    ut = np.zeros((J + 1, t.size))
    ut[:, 0] = u0
    un = u0
    EEinv = scipy.sparse.linalg.factorized(EE)
    flag = False
    for n in range(N):
        fu = fhandle(un)
        if flag == False:
            dW1, dW2 = Circlulant_Exponential(x, ell)
            flag = True
        else:
            dW1 = dW2
            flag=False
        un = EEinv(un + dt * fu + sigma * sqrt(dt) * dW1)
        ut[:, n + 1] = un
    return t, x, ut

def Spde_EM_FDM_Nagumo_White(u0, T, a, N, J, epsilon, sigma, fhandle):
    '''
    Nagumo SPDE with White noise and homogeneous Dirichlet boundary condition with initial condition u0
    Input:
        u0: the initial value of u(t, x)
        T: time boundary [0, T]
        a: x intervel [0, a]
        N: number of time intervals
        J: number of space intervals
        epsilon: parameter of Nagumo equation
        sigma: addictive noise parameter
        fhandle: nonlinear term f(u)
    Output:
        t, x, ut
    '''
    dt = T / N
    h = a / J
    t = np.linspace(0, T, N + 1)
    x = np.linspace(0, a, J + 1)
    ind = np.arange(1, J)
    A = scipy.sparse.diags([-1, 2, -1], [-1, 0, 1], shape=(J + 1, J + 1), format='csc')
    A = A[:, ind]; A = A[ind, :]
    EE = scipy.sparse.identity(ind.size, format='csc') + (dt * epsilon / h**2) * A
    ut = np.zeros((J + 1, t.size))
    ut[:, 0] = u0
    un = u0[ind]
    EEinv = scipy.sparse.linalg.factorized(EE)
    for n in range(N):
        fu = fhandle(un)
        Wn = sqrt(dt/h) * np.random.randn(J - 1)
        un = EEinv(un + dt * fu + sigma * Wn)
        ut[ind, n + 1] = un
    return t, x, ut


##############################################################################################
# solve spde with Euler-Maruyama Method and Galerkin
def Spde_oned_AC_EM_Galerkin(u0, T, a, N, kappa, Jref, J, epsilon, fhandle, ghandle, r, M):
    '''
    Input:
        u0: the initial value of u(t, x)
        T: time boundary [0, T]
        a: x intervel [0, a]
        N: number of time intervals
        Jref: 
        J: number of space intervals
        epsilon: parameter of Nagumo equation
        sigma: addictive noise parameter
        fhandle: nonlinear term f(u)
        ghandle: noise term G(u)
    Output:
        t, x, ut
    '''
    dtref = T / N
    dt = kappa * dtref
    t = np.linspace(0, T, N + 1)
    x = np.linspace(0, a, J+1)
    IJJ = np.arange(J // 2 + 1, Jref - J // 2, dtype='int' )
    kk = (2 * pi/ a) * np.hstack([np.arange(0, Jref // 2 + 1), np.arange(- Jref // 2 + 1, 0)]) 
    Dx=1j * kk
    MM=np.real(- epsilon * Dx ** 2)
    EE=1 / (1 + dt * MM);    EE[IJJ]=0;    #EE=EE.reshape((1,EE.size));
    # initiliase noise
    iFspace=1
    bj=Get_oned_bj(dtref,Jref,a,r);    bj[IJJ]=0
    # set initial conditon
    ut=np.zeros((Jref+1,N//kappa+1))
    ut[:,0]=u0;     u=u0[0:Jref];    uh0=np.copy(fft(u))
    uh=np.matlib.repmat(uh0,M,1);    u=(ifft(uh))
    #
    for n in range(N // kappa):
        uh[:,IJJ]=0
        fhu=fft(fhandle(np.real(u)));                fhu[:,IJJ]=0
        dW=Get_oned_dW(bj,kappa,iFspace,M);        dW[:,IJJ]=0
        gdWh=fft(ghandle(u)*np.real(ifft(dW)));     gdWh[:,IJJ]=0
        uh_new=EE*(uh + dt * fhu + gdWh);   uh=uh_new
        u=np.real(np.copy((ifft(uh))))
        ut[0:Jref,n + 1]=u[-1,:]
    ut[Jref,:]=ut[0,:]
    u=np.vstack([u,u[:]])
    return t, x, u, ut

def Spde_twod_AC_EM_Galerkin(u0, T, a, N, kappa, J, epsilon, fhandle, ghandle, alpha, M):
    """
    Input:
        u0: the initial value of u(t, x)
        T: time boundary [0, T]
        a: x intervel [0, a]
        N: number of time intervals
        kappa: dt = kappa * dtref 
        J: number of space intervals
        epsilon: parameter of Nagumo equation
        sigma: addictive noise parameter
        fhandle: nonlinear term f(u)
        ghandle: noise term G(u)
        alpha: parameterr of Q
        M: number of independent realizations
    Output:
        t, u, ut
    """
    dtref = T / N
    Dt = kappa * dtref;    t = np.linspace(0,T,N+1)
    #
    lambdax = (2*pi/a[0]) * np.hstack([np.arange(0, J[0]//2+1), np.arange(-J[0]//2+1, 0)])
    lambday = (2*pi/a[1]) * np.hstack([np.arange(0, J[1]//2+1), np.arange(-J[1]//2+1, 0)])
    lambdaxx, lambdayy = np.meshgrid(lambdax,lambday,indexing='ij')
    Dx = (1j * lambdaxx);    Dy = (1j * lambdayy)
    A = -(Dx ** 2 + Dy ** 2);    MM=np.real(epsilon * A)
    EE = 1 / (1 + Dt * MM)
    # initialise noise
    bj=Get_twod_bj(dtref,J,a,alpha)
    # initial conditions
    u = np.matlib.tile(u0[:-1, :-1], (M, 1, 1))
    uh = np.matlib.tile(fft2(u0[:-1, 0:-1]),(M, 1, 1))
    ut = np.zeros((J[0] + 1, J[1] + 1, N//kappa+1))
    ut[:, :, 0]=u0
    for n in range(N // kappa):
        fh = fft2(fhandle(u))
        dW, dW2 = Get_twod_dW(bj, kappa, M)
        gudWh = fft2(ghandle(u)*dW)
        uh_new = EE*(uh + Dt * fh + gudWh)
        u = np.real(ifft2(uh_new))
        ut[:-1, :-1, n + 1] = u[-1,:,:]
        uh = uh_new
    u[:,-1,:] = u[:,0,:];    u[:,:,-1] = u[:,:,0]
    ut[:,-1,:] = ut[:,0,:];   ut[-1,:,:] = ut[0,:,:]
    return t, u, ut

def Spde_EM_FEM(u0, T, a, Nref, kappa, neref, L, epsilon, fhandle, ghandle, r, M):
    '''
    Input:
        u0: the initial value of u(t, x)
        T: time boundary [0, T]
        a: x intervel [0, a]
        Nref: 
        kappa: dt = kappa * dtref 
        neref: 
        L: 
        epsilon: parameter of Nagumo equation
        fhandle: nonlinear term f(u)
        ghandle: noise term G(u)
        r: 
        M: number of independent realizations
    Output:
        t, u, ut
    '''
    ne = neref // L
    h = a / ne
    nvtx = ne + 1
    dtref = T / Nref
    dt = kappa * dtref
    t = np.linspace(0, T, Nref//kappa + 1)
    p = epsilon * np.ones(ne)
    q = np.ones(ne)
    f = np.ones(ne)
    uh, A, b, KK, MM = FEM_Solver1D_r1(ne, p, q, f)
    EE = MM + dt * KK
    ZM = np.zeros((M, 1))
    bj = get_onedD_bj(dtref, neref, a, r)
    bj[ne:-1] = 0
    iFspace = 0
    u = np.matlib.repmat(u0, M, 1)
    ut = np.zeros((nvtx, Nref//kappa + 1))
    ut[:, 0] = u[0, :]
    b = np.zeros(ne - 1)
    gdw = np.copy(b)
    EEinv = scipy.sparse.linalg.factorized(EE)
    for k in range(Nref//kappa):
        dWJ = get_onedD_dW(bj, kappa, iFspace, M)
        dWL = np.hstack([ZM, dWJ, ZM])
        dWL = dWL[:, ::L]
        gdW = ghandle(u) * dWL
        fu = fhandle(u)
        for m in range(M):
            b = oned_linear_FEM_b(ne, h, fu[m,:])
            gdw = oned_linear_FEM_b(ne, h, gdW[m, :])
            u1 = EEinv(MM.dot(u[m, 1:-1]) + dt * b + gdw)
            u[m, :] = np.hstack([0, u1, 0])
        ut[:, k + 1] = u[-1, :]
    return t, u, ut