from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter
import random, uuid

seed = 1 #1-5
rng = random.Random(seed)

packages = [
    "eff6cc6a-bbec-49c6-b3c2-b2eee3937c96",
	*[str(uuid.UUID(int=rng.getrandbits(128), version=4)) for _ in range(99)], # 99 random uuids
];

SECTION_CAPACITY = 50
NUM_DEPOSITS = 5
SECTIONS_PER_DEPOSIT = 3
POSSIBLE_LOCATIONS = [(x, y) for x in range(1, NUM_DEPOSITS+1) for y in range(1, SECTIONS_PER_DEPOSIT+1)]

@dataclass
class Event:
    timestamp: str
    package: str
    deposit: int
    section: int
    direction: int
    
    def generate_log(self):
        return "{}\tPackage {} has passed checkpoint {}.{}.{}".format(self.timestamp, self.package, self.deposit, 
                                                                      self.section, self.direction)
@dataclass
class Scenario:
    events: list[Event]
    manifests: dict[tuple[int, int], list[str]]
    target_location: tuple[int, int]

def available_locations(locations: dict[str, tuple[int, int]]) -> list[tuple[int, int]]:
    output = []
    packages_per_location = Counter(locations.values())
    for location in POSSIBLE_LOCATIONS:
        if packages_per_location[location] < SECTION_CAPACITY:
            output.append(location)
    return output

def simulate(seed) -> Scenario:
    # randomly generate starting locations:
    locations: dict[str, tuple[int, int]] = {}
    for package in packages:
        locations[package] = rng.choice(available_locations(locations=locations))
    return None

"""Generate 400 sequential random ISO 8601 timestamps for October 2, 2026."""
def generate_timestamps(seed: int | None = None) -> list[str]:
	"""Return 400 distinct, chronologically ordered timestamps on the date."""
	start = datetime(2026, 10, 2)
	seconds_in_day = 24 * 60 * 60
	offsets = sorted(random.Random(seed).sample(range(seconds_in_day), 400))
	return [(start + timedelta(seconds=offset)).isoformat() for offset in offsets]

timestamps = generate_timestamps(seed=seed)
