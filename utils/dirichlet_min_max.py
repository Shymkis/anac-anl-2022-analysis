import numpy as np
import matplotlib.pyplot as plt

def main():
	means = {}
	mxs = {}
	mns = {}
	diffs = {}
	reciprocal_diffs = {}
	n_min_over_diffs = {}
	sums = {}
	distribution = {}
	samples = 8000
	seed = 12345678
	rng = np.random.default_rng(seed)
	for n in range(2,21):
		alpha = np.array([2] * n)
		x = rng.dirichlet(alpha, samples)
		mx = np.max(x, axis=1)
		mn = np.min(x, axis=1)
		y = (x - mn.reshape((samples, 1))) / (mx - mn).reshape((samples, 1))
		mxs[n] = np.mean(mx)
		mns[n] = np.mean(mn)
		diffs[n] = np.mean(mx - mn)
		reciprocal_diffs[n] = np.mean(1 / (mx - mn))
		n_min_over_diffs[n] = n * np.mean(mn / (mx - mn))
		means[n] = np.mean(y)
		sums[n] = np.mean(np.sum(y, axis=1))
		sorted_y = np.sort(y, axis=1)
		new_y = sorted_y[:,1:sorted_y.shape[1]-1]
		#new_y = sorted_y[:,0:sorted_y.shape[1]]
		new_y = new_y.flatten()
		distribution[n] = new_y
	#fig, axs = plt.subplots(1, 1, figsize=(10, 10))
	#axs[0].plot(list(means.keys()), 1 / np.array(list(range(2, 21))))
	#axs[0].plot(list(means.keys()), list(means.values()))
	plt.plot(list(means.keys()), list(means.values()))
	#plt.show()
	#plt.plot(list(sums.keys()), list(sums.values()), c="r")
	#plt.plot(list(reciprocal_diffs.keys()), list(reciprocal_diffs.values()), c="g")
	#plt.plot(list(n_min_over_diffs.keys()), list(n_min_over_diffs.values()), c="b")
	plt.show()
	for n, vals in distribution.items():
		plt.hist(vals, bins=40)
		#plt.plot(vals)
		plt.show()
	#plt.plot(list(diffs.keys()), list(diffs.values()))
	#plt.show()
	
	for n, diff in diffs.items():
		print(n, diff)
	for n, mean in means.items():
		print(n, mean)

if __name__ == "__main__":
	main()