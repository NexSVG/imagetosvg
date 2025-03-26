import numpy as np
from opensimplex import OpenSimplex
import matplotlib.pyplot as plt

def test_noise_generation():
    # Initialize noise generator with a fixed seed for reproducibility
    noise_gen = OpenSimplex(seed=42)
    
    # Create a grid of points
    size = 100
    x = np.linspace(0, 10, size)
    y = np.linspace(0, 10, size)
    X, Y = np.meshgrid(x, y)
    
    # Generate noise values
    noise_values = np.zeros((size, size))
    for i in range(size):
        for j in range(size):
            noise_values[i, j] = noise_gen.noise2(X[i, j], Y[i, j])
    
    # Plot the noise
    plt.figure(figsize=(10, 10))
    plt.imshow(noise_values, cmap='gray')
    plt.colorbar()
    plt.title('OpenSimplex Noise Visualization')
    plt.savefig('noise_test.png')
    plt.close()

if __name__ == "__main__":
    test_noise_generation() 