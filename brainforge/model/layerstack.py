from brainforge import backend as xp


class LayerStack:

    def __init__(self, input_shape, layers=()):
        self.layers = []
        self.architecture = []
        self.learning = False
        self._iterme = None

        self._add_input_layer(input_shape)
        for layer in layers:
            self.add(layer)

    def _add_input_layer(self, input_shape):
        from ..layers import InputLayer
        inl = InputLayer(input_shape)
        inl.connect(self)
        self.layers.append(inl)
        self.architecture.append(str(inl))

    def add(self, layer):
        layer.connect(self, inshape=self.layers[-1].outshape)
        self.layers.append(layer)
        self.architecture.append(str(layer))

    def pop(self):
        self.layers.pop()
        self.architecture.pop()

    def feedforward(self, X):
        for layer in self.layers:
            X = layer.forward(X)
        return X

    def get_weights(self, unfold=True):
        ws = [layer.get_weights(unfold=unfold) for
              layer in self.layers if layer.trainable]
        return xp.concatenate(ws) if unfold else ws

    def set_weights(self, ws, fold=True):
        trl = (l for l in self.layers if l.trainable)
        if fold:
            start = 0
            for layer in trl:
                end = start + layer.nparams
                layer.set_weights(ws[start:end])
                start = end
        else:
            for w, layer in zip(ws, trl):
                layer.set_weights(w)

    def describe(self):
        return "Architecture: " + "->".join(self.architecture),

    def reset(self):
        for layer in (l for l in self.layers if l.trainable):
            layer.reset()

    @property
    def nparams(self):
        return sum(layer.nparams for layer in self.layers if layer.trainable)

    def __iter__(self):
        return self

    def __next__(self):
        if self._iterme is None:
            self._iterme = iter(self.layers)
        try:
            # noinspection PyTypeChecker
            return next(self._iterme)
        except StopIteration:
            self._iterme = None
            raise

    def __getitem__(self, item):
        return self.layers.__getitem__(item)
