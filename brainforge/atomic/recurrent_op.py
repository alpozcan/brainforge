import numpy as np

from .activation_op import activations
from ..util.typing import zX, zX_like, scalX

sigmoid = activations["sigmoid"]()
s0 = scalX(0.)


class RecurrentOp:

    def __init__(self, activation):
        self.actfn = activations[activation]()

    def forward(self, X, W, b):
        outdim = W.shape[-1]
        time, batch, indim = X.shape

        Z = zX(time, batch, indim+outdim)
        O = zX(time, batch, outdim)

        for t in range(time):
            Z[t] = np.concatenate((X[t], O[t-1]), axis=-1)
            O[t] = self.actfn.forward(np.dot(Z[t], W) + b)

        return O, Z

    def backward(self, Z, O, E, W):
        outdim = W.shape[-1]
        time, batch, zdim = Z.shape
        indim = zdim - outdim

        bwO = self.actfn.backward(O)

        for t in range(time-1, -1, -1):
            E[t] *= bwO[t]
            deltaZ = np.dot(E[t], W.T)
            E[t-1] += deltaZ[:, indim:] if t else 0.

        dX = E[:, :, :indim]
        nablaW = np.matmul(Z.transpose(0, 2, 1), E).sum(axis=0)
        nablab = E.sum(axis=(0, 1))
        return dX, nablaW, nablab


class LSTMOp:

    def __init__(self, activation):
        self.actfn = activations[activation]()

    def forward(self, X, W, b):
        outdim = W.shape[-1] // 4
        time, batch, indim = X.shape

        Z = zX(time, batch, indim+outdim)
        O = zX(time, batch, outdim)
        C, f, i, o, cand, Ca = zX(6, time, batch, outdim)

        for t in range(time):
            Z[t] = np.concatenate((X[t], O[t-1]), axis=-1)

            p = np.dot(Z[t], W) + b
            p[:, :outdim] = self.actfn.forward(p[:, :outdim])
            p[:, outdim:] = sigmoid.forward(p[:, outdim:])

            cand[t] = p[:, :outdim]
            f[t] = p[:, outdim:2*outdim]
            i[t] = p[:, 2*outdim:3*outdim]
            o[t] = p[:, 3*outdim:]
            # cand[t], f[t], i[t], o[t] = np.split(p, 4, axis=1)

            C[t] = C[t-1] * f[t] + cand[t] * i[t]

            Ca[t] = self.actfn.forward(C[t])
            O[t] = Ca[t] * o[t]

        return O, Z, np.stack((C, Ca, cand, f, i, o))

    def backward(self, Z, O, E, W, cache):
        outdim = W.shape[-1] // 4
        time, batch, zdim = Z.shape
        indim = zdim - outdim

        C, Ca, cand, f, i, o = cache
        bwgates = np.concatenate(cache[2:], axis=-1)
        bwgates[..., outdim:] = sigmoid.backward(bwgates[..., outdim:])
        bwgates[..., :outdim] = self.actfn.backward(bwgates[..., :outdim])
        bwCa = np.atleast_2d(self.actfn.backward(Ca))

        deltaC = zX_like(O[-1])
        deltaZ = zX_like(Z)
        dgates = zX(time, batch, outdim*4)

        for t in range(time-1, -1, -1):
            deltaC += E[t] * o[t] * bwCa[t]

            dcand = deltaC * i[t]
            df = deltaC * (C[t-1] if t else s0)
            di = deltaC * cand[t]
            do = Ca[t] * E[t]

            dgates[t] = np.concatenate((dcand, df, di, do), axis=-1) * bwgates[t]

            deltaC *= f[t]

            deltaZ[t] = np.dot(dgates[t], W.T)
            E[t-1] += deltaZ[t, :, indim:] if t else s0

        nablaW = np.matmul(Z.transpose(0, 2, 1), dgates).sum(axis=0)
        nablab = np.sum(dgates, axis=(0, 1))
        deltaX = deltaZ[:, :, :indim]
        return deltaX, nablaW, nablab

    def backward_o(self, Z, O, E, W, cache):
        C, f, i, o, cand, Ca = cache
        outdim = W.shape[-1] // 4
        time, batch, zdim = Z.shape
        indim = zdim - outdim

        bwgates = np.concatenate((f, i, o, cand), axis=-1)
        bwgates[:, :, :-outdim] = sigmoid.backward(bwgates[:, :, :-outdim])
        bwgates[:, :, -outdim:] = self.actfn.backward(bwgates[:, :, -outdim:])
        bwCa = self.actfn.backward(Ca)

        nablaW = zX_like(W)
        nablab = zX(outdim*4)

        delta = zX_like(O[-1])
        deltaC = zX_like(O[-1])
        deltaX = zX(time, batch, indim)
        dgates = zX(time, batch, outdim*4)

        for t in range(time-1, -1, -1):
            E[t] += delta
            deltaC += E[t] * o[t] * bwCa[t]
            state_yesterday = 0. if not t else C[t-1]
            df = state_yesterday * deltaC
            di = cand[t] * deltaC
            do = Ca[t] * E[t]
            dcand = i[t] * deltaC

            dgates[t] = np.concatenate((df, di, do, dcand), axis=-1) * bwgates[t]

            deltaC *= f[t]

            nablaW += np.dot(Z[t].T, dgates[t])
            nablab += np.sum(dgates[t], axis=0)

            deltaZ = np.dot(dgates[t], W.T)
            deltaX[t] = deltaZ[:, :-outdim]

        return deltaX, nablaW, nablab
