from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter
import random, uuid

TARGET_PACKAGE = "eff6cc6a-bbec-49c6-b3c2-b2eee3937c96"
SECTION_CAPACITY = 50
NUM_DEPOSITS = 5
SECTIONS_PER_DEPOSIT = 3
POSSIBLE_LOCATIONS = [(x, y) for x in range(1, NUM_DEPOSITS+1) for y in range(1, SECTIONS_PER_DEPOSIT+1)]

@dataclass
class Event:
    timestamp: datetime
    package: str
    deposit: int
    section: int
    direction: int
    
    def generate_log(self):
        return "{}\tPackage {} has passed checkpoint {}.{}.{}".format(self.timestamp.isoformat(), self.package, self.deposit, 
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
    rng = random.Random(seed)
    packages = [
        TARGET_PACKAGE,
	    *[str(uuid.UUID(int=rng.getrandbits(128), version=4)) for _ in range(99)], # 99 random uuids
    ]
    # randomly generate starting locations:
    locations: dict[str, tuple[int, int]] = {}
    for package in packages:
        locations[package] = rng.choice(available_locations(locations=locations))
    # print(locations)
    return None

def move(package: str, origin: tuple[int, int], destination: tuple[int, int], now: datetime, rng: random) -> tuple[list[Event], datetime]:
    events_list = []
    deposit_origin, section_origin = origin
    deposit_destination, section_destination = destination
    moves_deposit = (deposit_origin != deposit_destination)
    # log exit of section
    events_list.append(Event(now, package, deposit_origin, section_origin, 1))
    if moves_deposit:
        # log exit of deposit
        # between exit of section and exit of deposit, 90 to 120 seconds will go by
        time_increment = timedelta(seconds=rng.randint(90, 120))
        now = now + time_increment
        events_list.append(Event(now, package, deposit_origin, 0, 1))
        # log entry in new deposit
        # between exit of deposit and entry of another deposit, 120 to 240 seconds will go by
        time_increment = timedelta(seconds=rng.randint(120, 240))
        now = now + time_increment
        events_list.append(Event(now, package, deposit_destination, 0, 0))
        # log entry in section
        # between entry in deposit and entry in section, 90 to 120 seconds will go by
        time_increment = timedelta(seconds=rng.randint(90, 120))
        now = now + time_increment
        events_list.append(Event(now, package, deposit_destination, section_destination, 0))
    else:
        # for moves between sections of the same deposit, 60 to 90 seconds will go by
        time_increment = timedelta(seconds=rng.randint(60, 90))
        now = now + time_increment
        events_list.append(Event(now, package, deposit_destination, section_destination, 0))

    return (events_list, now)

"""Generate 400 sequential random ISO 8601 timestamps for October 2, 2026."""
def generate_timestamps(seed: int | None = None) -> list[str]:
	"""Return 400 distinct, chronologically ordered timestamps on the date."""
	start = datetime(2026, 10, 2)
	seconds_in_day = 24 * 60 * 60
	offsets = sorted(random.Random(seed).sample(range(seconds_in_day), 400))
	return [(start + timedelta(seconds=offset)).isoformat() for offset in offsets]

# timestamps = generate_timestamps(seed=seed)

simulate(seed=1)
