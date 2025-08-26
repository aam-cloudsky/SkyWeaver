import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")   # ou "Qt5Agg"


fig, ax = plt.subplots()
im = ax.imshow(np.random.rand(10, 10), cmap="Reds", origin="lower")
plt.show(block=False)
plt.pause(0.1)

for i in range(50):
    im.set_data(np.random.rand(10, 10))
    plt.pause(0.1)   # precisa disso
    print(f"Frame {i}")
    time.sleep(0.05)
