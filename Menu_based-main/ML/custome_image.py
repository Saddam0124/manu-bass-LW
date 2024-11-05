import numpy as np
import matplotlib.pyplot as plt

# Create a blank image
width = 500
height = 300
image = np.zeros((height, width, 3), dtype=np.uint8)

# Add some shapes and colors
# Red rectangle
image[50:150, 100:200, 0] = 255

# Green circle
center_x, center_y = 300, 150
radius = 50
for y in range(height):
    for x in range(width):
        if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
            image[y, x, 1] = 255

# Blue line
image[200:250, :, 2] = 255

# Display the image
plt.imshow(image)
plt.show()