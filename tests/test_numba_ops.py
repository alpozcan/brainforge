import unittest

import numpy as np
from matplotlib import pyplot as plt

from brainforge.atomic import (
    ConvolutionOp as NpConv,
    MaxPoolOp as NpPool,
    DenseOp as NpDense,
    RecurrentOp as NpRec,
    LSTMOp as NpLSTM
)
from brainforge.llatomic import (
    ConvolutionOp as NbConv,
    MaxPoolOp as NbPool,
    DenseOp as NbDense,
    RecurrentOp as NbRec,
    LSTMOp as NbLSTM
)


VISUAL = False


class TestNumbaTensorOps(unittest.TestCase):

    def test_convolution_op(self):
        npop = NpConv()
        nbop = NbConv()

        A = np.random.uniform(size=(1, 1, 12, 12))
        F = np.random.uniform(size=(1, 1, 3, 3))

        npO = npop.forward(A, F, mode="full")
        nbO = nbop.forward(A, F, mode="full")

        self.assertTrue(np.allclose(npO, nbO))

        if VISUAL:
            visualize(A, npO, nbO, supt="Testing Convolutions")

    def test_pooling_op(self):
        npop = NpPool()
        nbop = NbPool()

        A = np.random.uniform(0., 1., (1, 1, 12, 12))

        npO, npF = npop.forward(A, 2)
        nbO, nbF = nbop.forward(A, 2)

        npbF = npop.backward(npO, npF)
        nbbF = nbop.backward(nbO, nbF)

        self.assertTrue(np.allclose(npF, nbF))
        self.assertTrue(np.allclose(npbF, nbbF))
        self.assertTrue(np.allclose(npO, nbO))

        if VISUAL:
            visualize(A, npO, nbO, supt="Testing Pooling")

    def test_dense_op(self):
        npop = NpDense()
        nbop = NbDense()

        A = np.random.uniform(size=(12, 12))
        W = np.random.uniform(size=(12, 12))
        b = np.random.uniform(size=(12,))

        npO = npop.forward(A, W, b)
        nbO = nbop.forward(A, W, b)

        self.assertTrue(np.allclose(npO, nbO))
        if VISUAL:
            visualize(A[None, None, ...], npO[None, None, ...], nbO[None, None, ...], "Testing Dense")

    def test_recurrent_op(self):

        npop = NpRec("tanh")
        nbop = NbRec("tanh")

        A = np.random.uniform(size=(5, 20, 10))
        W = np.random.uniform(size=(20, 10))
        b = np.random.uniform(size=(10,))

        npO, npZ = npop.forward(A, W, b)
        nbO, nbZ = nbop.forward(A, W, b)

        self.assertTrue(np.allclose(npO, nbO))
        self.assertTrue(np.allclose(npZ, nbZ))

    def test_lstm_op(self):
        npop = NpLSTM("tanh")
        nbop = NbLSTM("tanh")

        BSZE = 20
        TIME = 2
        DDIM = 10
        NEUR = 15

        X = np.random.randn(TIME, BSZE, DDIM)
        W = np.random.randn(NEUR + DDIM, NEUR * 4)
        b = np.random.randn(NEUR * 4)
        # E = np.random.randn(BSZE, TIME, NEUR)

        npO, npZ, npcache = npop.forward(X, W, b)
        nbO, nbZ, nbcache = nbop.forward(X, W, b)

        # visualize(X, npZ, nbZ)
        for i, array_type in enumerate(["C", "Ca", "cand", "f", "i", "o"]):
            for t in range(TIME):
                d = np.sum(np.abs(npcache[i, t] - nbcache[i, t]))
                print("{} diff @ t {}: {}".format(array_type, t, d))
        self.assertTrue(np.allclose(npcache, nbcache))
        self.assertTrue(np.allclose(npZ, nbZ))
        self.assertTrue(np.allclose(npO, nbO))


def visualize(A, O1, O2, supt=None):
    TAKE = 0
    d = O1 - O2
    vmax, vmin = max(O1.max(), O2.max()), min(O1.min(), O2.min())
    fig, axarr = plt.subplots(2, 2)
    print("Total deviance:", d.sum())
    axarr[0][1].imshow(d[TAKE], cmap="seismic")
    axarr[0][1].set_title("d")
    axarr[1][0].imshow(O1[TAKE], vmin=vmin, vmax=vmax, cmap="hot")
    axarr[1][0].set_title("npO")
    axarr[1][1].imshow(O2[TAKE], vmin=vmin, vmax=vmax, cmap="hot")
    axarr[1][1].set_title("nbO")
    plt.suptitle(supt)
    plt.tight_layout()
    plt.show()
