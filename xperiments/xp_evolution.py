from brainforge import backend as xp
from matplotlib import pyplot as plt

from brainforge.evolution import Population


def upscale(ind: xp.ndarray):
    x = ind * 10.
    return x


def fitness(ind):
    return xp.linalg.norm(TARGET - upscale(ind)),


def matefn1(ind1, ind2):
    return xp.where(xp.random.uniform() < 0.5, ind1, ind2)


def matefn2(ind1, ind2):
    return xp.add(ind1, ind2) / 2.


TARGET = xp.array([3., 3.])


pop = Population(
    loci=2,
    fitness_function=fitness,
    mate_function=matefn2,
    limit=100)

plt.ion()
obj = plt.plot(*upscale(pop.individuals.T), "bo", markersize=2)[0]
plt.xlim([-2, 11])
plt.ylim([-2, 11])

X, Y = xp.linspace(-2, 11, 50), xp.linspace(-2, 11, 50)
X, Y = xp.meshgrid(X, Y)
Z = xp.array([fitness(xp.array([x, y])/10.) for x, y in zip(X.ravel(), Y.ravel())]).reshape(X.shape)
CS = plt.contour(X, Y, Z, cmap="hot")
plt.clabel(CS, inline=1, fontsize=10)
plt.show()
means, stds, bests = [], [], []
for i in range(100):
    m, s, b = pop.run(1, verbosity=0, mutation_rate=0.01)
    means += m
    stds += s
    bests += b
    obj.set_data(*upscale(pop.individuals.T))
    plt.pause(0.1)

means, stds, bests = tuple(map(xp.array, (means, stds, bests)))
plt.close()
plt.ioff()
Xs = xp.arange(1, len(means) + 1)
plt.plot(Xs, means, "b-")
plt.plot(Xs, means+stds, "g--")
plt.plot(Xs, means-stds, "g--")
plt.plot(Xs, bests, "r-")
plt.xlim([Xs.min(), Xs.max()])
plt.ylim([bests.min(), (means+stds).max()])
plt.show()
