import numpy as np
import matplotlib as plt


if __name__ == "__main__":
    GA_result = np.load('GA_results.npy')
    X = range(0, len(GA_result) + 1)
    plt.plot(X, GA_result)
    plt.xlabel('Iteration/ Gen')
    plt.ylabel('RMSD')
    plt.show()