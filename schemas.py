from dataclasses import dataclass, field


@dataclass 
class Accumulated:
    kWh: float
    kVAh: float
    kVArh: float

@dataclass
class ModuleState:
    supervisor_state: str
    engine_generator: str
    mains_state: str
    load_switching_state: str
    accumulated: Accumulated

@dataclass
class BetweenPhases:
    l1_l2: float
    l2_l3: float
    l3_l1: float
    freq: float

@dataclass
class PhaseValues:
    v: float
    a: float 

@dataclass
class PerPhase:
    l1: PhaseValues
    l2: PhaseValues
    l3: PhaseValues

@dataclass
class CollectedData:
    start_state: str # auto, on, off
    module_state: ModuleState