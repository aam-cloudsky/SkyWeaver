from dataclasses import dataclass


@dataclass
class DistributionConfiguration:
    domain: tuple
    poi_uav: tuple
    poi_mav: tuple
