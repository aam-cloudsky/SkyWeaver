import matplotlib.pyplot as plt
import threading
import time
import matplotlib
matplotlib.use("TkAgg")


class GridStreaming:
    def __init__(self, interval: float = 0.1):
        self.interval = interval
        self._running = False
        self._thread = None
        self._grid_ref = None

        # matplotlib
        self._fig = None
        self._ax = None
        self._im = None

        # flag para controlar atualização
        self._update_flag = threading.Event()

    def start(self, grid_ref):
        if self._running:
            print("[GridStreaming] Já está rodando.")
            return

        self._grid_ref = grid_ref
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("[GridStreaming] Streaming iniciado.")

    def trigger_update(self):
        """Sinaliza que o grid foi atualizado (chamado no step)."""
        self._update_flag.set()

    def _run(self):
        if self._grid_ref is None:
            print("[GridStreaming] Nenhum grid foi passado.")
            return

        self._fig, self._ax = plt.subplots()
        self._im = self._ax.imshow(
            self._grid_ref[1, :, :], cmap="Reds", origin="lower"
        )
        plt.show(block=False)

        while self._running:
            # espera até receber trigger, mas com timeout para não travar
            if self._update_flag.wait(timeout=self.interval):
                self._update_flag.clear()
                self._im.set_data(self._grid_ref[1, :, :])
                self._ax.set_title("Grid Streaming (Restriction Layer)")
                self._fig.canvas.draw_idle()
                plt.pause(0.001)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        print("[GridStreaming] Streaming parado.")
        plt.close(self._fig)