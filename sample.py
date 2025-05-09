import numpy as np

# Load the cached data
data = np.load('cache/processed_data.npz')

# Get the arrays
X1 = data['X1']
X2 = data['X2']
y = data['y']

# Print shapes
print("Dataset shapes:")
print(f"X1 shape: {X1.shape}")
print(f"X2 shape: {X2.shape}")
print(f"y shape: {y.shape}")

# Print some statistics
print("\nStatistics:")
print(f"Number of positive pairs (y=1): {np.sum(y == 1)}")
print(f"Number of negative pairs (y=0): {np.sum(y == 0)}")
print(f"X1 value range: [{X1.min():.3f}, {X1.max():.3f}]")
print(f"X2 value range: [{X2.min():.3f}, {X2.max():.3f}]")

# Print a few sample pairs
print("\nSample pairs:")
for i in range(3):
    print(f"\nPair {i+1}:")
    print(f"X1[{i}] shape: {X1[i].shape}")
    print(f"X2[{i}] shape: {X2[i].shape}")
    print(f"Label: {y[i]}")
