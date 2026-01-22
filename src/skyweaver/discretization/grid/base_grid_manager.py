from abc import ABC, abstractmethod
from skyweaver.discretization.grid.base_grid import BaseGrid


class BaseGridManager(ABC):

    @abstractmethod
    def build(self) -> BaseGrid:
        pass

    @abstractmethod
    def get_grid(self) -> BaseGrid:
        pass
