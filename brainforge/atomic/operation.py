from brainforge import backend as xp


class ReshapeOp:

    @staticmethod
    def forward(X, outshape):
        return X.reshape(X.shape[0], *outshape)

    @staticmethod
    def backward(E, inshape):
        return ReshapeOp.forward(E, inshape)


class ConvolutionOp:

    @staticmethod
    def valid(A, F):
        im, ic, iy, ix = A.shape
        nf, fc, fy, fx = F.shape
        # fx, fy, fc, nf = F.shape
        recfield_size = fx * fy * fc
        oy, ox = iy - fy + 1, ix - fx + 1
        rfields = xp.zeros((im, oy*ox, recfield_size))
        Frsh = F.reshape(nf, recfield_size)

        if fc != ic:
            err = "Supplied filter (F) is incompatible with supplied input! (X)\n"
            err += "input depth: {} != {} :filter depth".format(ic, fc)
            raise ValueError(err)

        for i, pic in enumerate(A):
            for sy in range(oy):
                for sx in range(ox):
                    rfields[i][sy*ox + sx] = pic[:, sy:sy+fy, sx:sx+fx].ravel()

        output = xp.zeros((im, oy*ox, nf))
        for m in range(im):
            output[m] = xp.dot(rfields[m], Frsh.T)

        # output = xp.matmul(rfields, F.reshape(nf, recfield_size).T)
        output = output.transpose((0, 2, 1)).reshape(im, nf, oy, ox)
        return output

    @staticmethod
    def full(A, F):
        nf, fc, fy, fx = F.shape
        py, px = fy - 1, fx - 1
        pA = xp.pad(A, pad_width=((0, 0), (0, 0), (py, py), (px, px)),
                    mode="constant", constant_values=0.)
        return ConvolutionOp.valid(pA, F)

    @staticmethod
    def apply(A, F, mode="valid"):
        if mode == "valid":
            return ConvolutionOp.valid(A, F)
        return ConvolutionOp.full(A, F)

    @staticmethod
    def outshape(inshape, fshape, mode="valid"):
        ic, iy, ix = inshape[-3:]
        fx, fy, fc, nf = fshape
        if mode == "valid":
            return nf, iy - fy + 1, ix - fx + 1
        elif mode == "full":
            return nf, iy + fy - 1, ix + fx - 1
        else:
            raise RuntimeError("Unsupported mode:", mode)


class MaxPoolOp:

    @staticmethod
    def apply(A, fdim):
        im, ic, iy, ix = A.shape
        oy, ox = iy // fdim, ix // fdim
        output = xp.zeros((im, ic, oy, ox))
        filt = xp.zeros_like(A)
        for m in range(im):
            for c in range(ic):
                for y, sy in enumerate(range(0, iy, fdim)):
                    for x, sx in enumerate(range(0, ix, fdim)):
                        recfield = A[m, c, sy:sy+fdim, sx:sx+fdim]
                        value = recfield.max()
                        output[m, c, y, x] = value
                        ffield = xp.equal(recfield, value)
                        filt[m, c, sy:sy+fdim, sx:sx+fdim] += ffield
        return output, filt

    @staticmethod
    def backward(E, filt):
        em, ec, ey, ex = E.shape
        fm, fc, fy, fx = filt.shape
        fdim = fy // ey
        for m in range(em):
            for c in range(ec):
                for i, y in enumerate(range(0, fy, fdim)):
                    for j, x in enumerate(range(0, fx, fdim)):
                        filt[m, c, y:y+fdim, x:x+fdim] *= E[m, c, i, j]
        return filt

    @staticmethod
    def outshape(inshape, fdim):
        if len(inshape) == 3:
            m, iy, ix = inshape
            return m, iy // fdim, ix // fdim
        elif len(inshape) == 2:
            iy, ix = inshape
            return iy // fdim, ix // fdim
