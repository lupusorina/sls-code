import cvxpy as cp
import numpy as np

class SLSConstraint:
    '''
    The base class for SLS constriant
    '''
    def addConstraints(self, sls, objective_value, constraints):
        return objective_value, constraints

class SLSCons_dLocalized (SLSConstraint):
    def __init__(self,
        base=None,
        actDelay=0, cSpeed=1, d=1
    ):
        if isinstance(base,SLSCons_dLocalized):
            self._actDelay = base._actDelay
            self._cSpeed = base._cSpeed
            self._d = base._d
        else:
            self._actDelay = actDelay
            self._cSpeed = cSpeed
            self._d = d
    
    def addConstraints(self, sls, objective_value, constraints):
        # localized constraints
        # get localized supports
        Phi_x = sls._Phi_x
        Phi_u = sls._Phi_u

        XSupport = []
        USupport = []

        commsAdj = np.absolute(sls._system_model._A) > 0
        localityR = np.linalg.matrix_power(commsAdj, self._d - 1) > 0

        # adjacency matrix for available information 
        infoAdj = np.eye(sls._system_model._Nx) > 0
        transmission_time = -self._cSpeed*self._actDelay
        for t in range(sls._FIR_horizon):
            transmission_time += self._cSpeed
            while transmission_time >= 1:
                transmission_time -= 1
                infoAdj = np.dot(infoAdj,commsAdj)

            support_x = np.logical_and(infoAdj, localityR)
            XSupport.append(support_x)

            support_u = np.dot(np.absolute(sls._system_model._B2).T,support_x.astype(int)) > 0
            USupport.append(support_u)

        # shutdown those not in the support
        for t in range(1,sls._FIR_horizon-1):
            for ix,iy in np.ndindex(XSupport[t].shape):
                if XSupport[t][ix,iy] == False:
                    constraints += [ Phi_x[t][ix,iy] == 0 ]
        for t in range(sls._FIR_horizon):
            for ix,iy in np.ndindex(USupport[t].shape):
                if USupport[t][ix,iy] == False:
                    constraints += [ Phi_u[t][ix,iy] == 0 ]

        return objective_value, constraints

class SLSCons_ApproxdLocalized (SLSCons_dLocalized):
    def __init__(self,
        robCoeff=0,
        **kwargs
    ):
        SLSCons_dLocalized.__init__(self,**kwargs)

        base = kwargs.get('base')
        if isinstance(base,SLSCons_ApproxdLocalized):
            self._robCoeff = base._robCoeff
        else:
            self._robCoeff = robCoeff

        self._stability_margin = -1

    def getStabilityMargin (self):
        return self._stability_margin

    def addConstraints(self, sls, objective_value, constraints):
        # reset constraints
        Phi_x = sls._Phi_x
        Phi_u = sls._Phi_u

        Nx = sls._system_model._Nx
        constraints =  [ Phi_x[0] == np.eye(Nx) ]
        constraints += [ Phi_x[sls._FIR_horizon-1] == np.zeros([Nx, Nx]) ]

        SLSCons_dLocalized.addConstraints(self,
            sls=sls,
            objective_value=objective_value,
            constraints=constraints
        )

        Delta = cp.Variable(shape=(Nx,Nx*sls._FIR_horizon))

        pos = 0
        for t in range(sls._FIR_horizon-1):
            constraints += [
                Delta[:,pos:pos+Nx] == (
                    Phi_x[t+1]
                    - sls._system_model._A  * Phi_x[t]
                    - sls._system_model._B2 * Phi_u[t]
                )
            ]
            pos += Nx

        self._stability_margin = cp.norm(Delta, 'inf')  # < 1 means we can guarantee stability
        objective_value += self._robCoeff * self._stability_margin

        return objective_value, constraints