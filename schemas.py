from dataclasses import dataclass


def flatten_dataclass(data, prefix=""):
    result = {}
    if hasattr(data, "__dataclass_fields__"):
        for field in data.__dataclass_fields__:
            value = getattr(data, field)
            key = f"{prefix}.{field}" if prefix else field
            result.update(flatten_dataclass(value, key))
    elif isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            result.update(flatten_dataclass(value, full_key))
    else:
        result[prefix] = data
    return result

@dataclass 
class Accumulated:
    kwh: float
    kvah: float
    kvarh: float

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
class GeneratorData:
    between_phases: BetweenPhases
    per_phase: PerPhase

@dataclass
class MainsData:
    between_phases: BetweenPhases
    per_phase: PerPhase

@dataclass
class PhasePower:
    kw: float
    kva: float
    kvar: float
    pf: float


@dataclass
class PowerData:
    l1: PhasePower
    l2: PhasePower
    l3: PhasePower
    total: PhasePower


@dataclass
class EngineData:
    speed: float
    oil_pressure: float
    coolant_temperature: float
    fuel_level: int
    charge_alternator: float
    engine_battery: float
    engine_starts: int
    engine_minutes: int

@dataclass
class CollectedData:
    start_state: str # auto, on, off
    module_state: ModuleState
    generator: GeneratorData
    mains: MainsData
    power: PowerData
    engine: EngineData