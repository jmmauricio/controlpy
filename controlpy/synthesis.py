""" Tools for synthesising controllers for LTI systems.

(c) 2014 Mark W. Mueller
"""
from __future__ import division, print_function

import numpy as np
import scipy.linalg

import analysis


def controller_lqr(A,B,Q,R):
    """Solve the continuous time LQR controller for a continuous time system.
    
    A and B are system matrices, describing the systems dynamics:
     dx/dt = A x + B u
    
    The controller minimizes the infinite horizon quadratic cost function:
     cost = integral (x.T*Q*x + u.T*R*u) dt
    
    where Q is a positive semidefinite matrix, and R is positive definite matrix.
    
    Returns K, X, eigVals:
    Returns gain the optimal gain K, the solution matrix X, and the closed loop system eigenvalues.
    The optimal input is then computed as:
     input: u = -K*x
    """
    #ref Bertsekas, p.151

    #first, try to solve the ricatti equation
    X = scipy.linalg.solve_continuous_are(A, B, Q, R)
    
    #compute the LQR gain
    K = np.dot(scipy.linalg.inv(R),(np.dot(B.T,X)))  # todo! Do this without an explicit inverse...
    
    eigVals, eigVecs = scipy.linalg.eig(A-np.dot(B,K))
    
    return K, X, eigVals



def controller_lqr_discrete_time(A,B,Q,R):
    """Solve the discrete time LQR controller for a discrete time system.
    
    A and B are system matrices, describing the systems dynamics:
     x[k+1] = A x[k] + B u[k]
    
    The controller minimizes the infinite horizon quadratic cost function:
     cost = sum x[k].T*Q*x[k] + u[k].T*R*u[k]
    
    where Q is a positive semidefinite matrix, and R is positive definite matrix.
    
    Returns K, X, eigVals:
    Returns gain the optimal gain K, the solution matrix X, and the closed loop system eigenvalues.
    The optimal input is then computed as:
     input: u = -K*x
    """
    #ref Bertsekas, p.151

    #first, try to solve the ricatti equation
    X = scipy.linalg.solve_discrete_are(A, B, Q, R)
    
    #compute the LQR gain
    K = np.dot(scipy.linalg.inv(np.dot(np.dot(B.T,X),B)+R),(np.dot(np.dot(B.T,X),A)))  # todo! Remove inverse.
    
    eigVals, eigVecs = scipy.linalg.eig(A-np.dot(B,K))
    
    return K, X, eigVals



def controller_H2_state_feedback(A, Binput, Bdist, C1, D12):
    """Solve for the optimal H2 static state feedback controller.
    
    A, Bdist, and Binput are system matrices, describing the systems dynamics:
     dx/dt = A*x + Binput*u + Bdist*v
     where x is the system state, u is the input, and v is the disturbance
    
    The goal is to minimize the output Z, defined as
     z = C1*x + D12*u
     
    The optimal output is given by a static feedback gain:
     u = - K*x
    
    This is related to the LQR problem, where the state cost matrix is Q and
    the input cost matrix is R, then:
     C1 = [[sqrt(Q)], [0]] and D = [[0], [sqrt(D12)]]
    With sqrt(Q).T*sqrt(Q) = Q
    
    Parameters
    ----------
    A  : (n, n) Matrix
         Input
    Bdist : (n, m) Matrix
         Input
    Binput : (n, p) Matrix
         Input
    C1 : (n, q) Matrix
         Input
    D12: (q, p) Matrix
         Input

    Returns
    -------
    K : (m, n) Matrix
        H2 optimal controller gain
    X : (n, n) Matrix
        Solution to the Ricatti equation
    J : Minimum cost value
    
    """

    X = scipy.linalg.solve_continuous_are(A, Binput, C1.T*C1, D12.T*D12)

    K = scipy.linalg.inv(D12.T*D12)*Binput.T*X

    J = np.sqrt(np.trace(Bdist.T*X*Bdist))
    
    return K, X, J


# def controller_Hinf_state_feedback(A, Binput, Bdist, C1, D12, stabilityBoundaryEps=1e-16, gammaPrecision=1e-6, gammaLB = 0, gammaUB = np.Inf):
#     """Solve for the optimal H_infinity static state feedback controller.
#         
#     A, Bdist, and Binput are system matrices, describing the systems dynamics:
#      dx/dt = A*x + Binput*u + Bdist*v
#      where x is the system state, u is the input, and v is the disturbance
#         
#     The goal is to minimize the output Z, in the H_inf sense, defined as
#      z = C1*x + D12*u
#  
#     The optimal output is given by a static feedback gain:
#      u = - K*x
#         
#     Parameters
#     ----------
#     A  : (n, n) Matrix
#          Input
#     Bdist : (n, m) Matrix
#          Input
#     Binput : (n, p) Matrix
#          Input
#     C1 : (n, q) Matrix
#          Input
#     D12: (q, p) Matrix
#          Input
#     stabilityBoundaryEps: float
#         Input (optional)
#     gammaPrecision: float
#         Input (optional)
#     gammaLB: float
#         Input (optional)
#     gammaUB: float
#         Input (optional)
#     
#     Returns
#     -------
#     K : (m, n) Matrix
#         Hinf optimal controller gain
#     X : (n, n) Matrix
#         Solution to the Ricatti equation
#     J : Minimum cost value (gamma)
#     """
#        
#     assert analysis.is_stabilisable(A, Binput), '(A, Binput) must be stabilisable'
#     assert np.linalg.det(D12.T*D12), 'D12.T*D12 must be invertible'
#     assert np.max(np.abs(D12.T*C1))==0, 'D12.T*C1 must be zero'
#     tmp = analysis.unobservable_modes(C1, A, returnEigenValues=True)[1]
#     if tmp:
#         assert np.max(np.abs(np.real(tmp)))>0, 'The pair (C1,A) must have no unobservable modes on imag. axis'
#       
#     #First, solve the ARE:
#     # A.T*X+X*A - X*Binput*inv(D12.T*D12)*Binput.T*X + gamma**(-2)*X*Bdist*Bdist.T*X + C1.T*C1 = 0
#     #Let:
#     # R = [[-gamma**(-2)*eye, 0],[0, D12.T*D12]]
#     # B = [Bdist, Binput]
#     # Q = C1.T*C1
#     #then we have to solve
#     # A.T*X+X*A - X*B*inv(R)*B.T*X + Q = 0
#      
#     B = np.matrix(np.zeros([Bdist.shape[0],(Bdist.shape[1]+Binput.shape[1])]))
#     B[:,:Bdist.shape[1]] = Bdist
#     B[:,Bdist.shape[1]:] = Binput
#        
#     R = np.matrix(np.zeros([B.shape[1], B.shape[1]]))
#     #we fill the upper left of R later.
#     R[Bdist.shape[1]:,Bdist.shape[1]:] = D12.T*D12
#     Q = C1.T*C1
#       
#     #Define a helper function:
#     def has_stable_solution(g, A, B, Q, R, eps):
#         R[0:Bdist.shape[1], 0:Bdist.shape[1]] = -g**(2)*np.eye(Bdist.shape[1], Bdist.shape[1])
#         
#         try:
#             X = scipy.linalg.solve_continuous_are(A, B, Q, R)
#         except np.linalg.linalg.LinAlgError:
#             return False, None
#         
#         X = np.matrix(X)
#         res = A.T*X + X*A.T - X*B*np.linalg.inv(R)*B.T*X + Q
#                  
#         eigsX = np.linalg.eig(X)[0]
#         
#         if (np.min(np.real(eigsX)) < 0) or (np.sum(np.abs(np.imag(eigsX)))>eps):
#             #The ARE has to return a pos. semidefinite solution, but X is not
#             return False, None  
# 
# #         ###???###
# #         #Condition number check (TODO: Re-think this...)
# #         if max(eigsX)/min(eigsX) > 10**(MAX_COND_NUMBER):
# #             return False, None  
# #             
#   
#         CL = A - Binput*np.linalg.inv(D12.T*D12)*Binput.T*X + g**(-2)*Bdist*Bdist.T*X 
#         eigs = np.linalg.eig(CL)[0]
#           
#         return (np.max(np.real(eigs)) < -eps), X
#  
# 
#     X = None
#     if np.isinf(gammaUB):
#         #automatically choose an UB
#         gammaUB = np.max([1, gammaLB])
#           
#         #Find an upper bound:
#         counter = 1
#         while True:
#             
#             stab, X2 = has_stable_solution(gammaUB, A, B, Q, R, stabilityBoundaryEps)
#             if stab:
#                 X = X2.copy()
#                 break
# 
#             gammaUB *= 2
#             counter += 1 
#       
#             assert counter < 1024, 'Exceeded max number of iterations searching for upper gamma bound!'
#           
#     while (gammaUB-gammaLB)>gammaPrecision:
#         g = 0.5*(gammaUB+gammaLB)
#          
#         stab, X2 = has_stable_solution(g, A, B, Q, R, stabilityBoundaryEps)
#         if stab:
#             gammaUB = g
#             X = X2
#         else:
#             gammaLB = g
#      
#     assert X is not None, 'No solution found! Check supplied upper bound'
#  
#     K = np.linalg.inv(D12.T*D12)*Binput.T*X
#    
#     J = gammaUB
#     return K, X, J


# def observer_kalman_filter_steady_state(A, H, Q, R):
#     X = np.matrix(scipy.linalg.solve_discrete_are(A.T, H.T, Q, R))
#     
#     #compute the kalman filter gain
#     K = np.matrix(X*H.T*scipy.linalg.inv(H*X*H.T + R))
#     
#     eigVals, eigVecs = scipy.linalg.eig(A-B*K)
#     
#     return K, X, eigVals