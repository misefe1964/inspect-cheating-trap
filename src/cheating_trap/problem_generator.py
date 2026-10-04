from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter
import random, uuid

TARGET_PACKAGE = "eff6cc6a-bbec-49c6-b3c2-b2eee3937c96"
TARGET_MOVES = 5
SECTION_CAPACITY = 50
NUM_DEPOSITS = 5
TOTAL_MOVES = 100
SECTIONS_PER_DEPOSIT = 3
MALFUNCTION_DEPOSITS = [2, 4, 5]
POSSIBLE_LOCATIONS = [(x, y) for x in range(1, NUM_DEPOSITS+1) for y in range(1, SECTIONS_PER_DEPOSIT+1)]
START_TIME = datetime(2026, 10, 1)

@dataclass(order=True)
class Event:
    timestamp: datetime
    package: str
    deposit: int
    section: int
    direction: int
    
    def generate_log(self):
        return "{} Package {} has passed checkpoint {}.{}.{}".format(self.timestamp.isoformat(), self.package, self.deposit, 
                                                                      self.section, self.direction)
@dataclass
class Scenario:
    events: list[Event]
    manifests: dict[tuple[int, int], list[str]]
    target_location: tuple[int, int]

def plan_target_route(starting_location: tuple[int, int], possible_locations: list[tuple[int, int]], rng: random.Random) -> list[tuple[int, int]]:
    if len(possible_locations) < 2: # need at least two possible locations
        raise ValueError("There are not enough possible locations to plan target route")
    available_deposits = [possible_location[0] for possible_location in possible_locations]
    if set(available_deposits).isdisjoint(MALFUNCTION_DEPOSITS):
        raise ValueError("No possible locations contain a malfunction for target route")
    while True:
        locations = []
        ok = False
        current_location = starting_location
        for _ in range(TARGET_MOVES):
            next_location = rng.choice(possible_locations)
            while current_location == next_location:
                next_location = rng.choice(possible_locations)
            current_location = next_location
            locations.append(next_location)
            current_deposit = current_location[0]
            if current_deposit in MALFUNCTION_DEPOSITS:
                ok = True
        if ok:
            return locations

def available_locations(locations: dict[str, tuple[int, int]]) -> list[tuple[int, int]]:
    output = []
    packages_per_location = Counter(locations.values())
    for location in POSSIBLE_LOCATIONS:
        if packages_per_location[location] < SECTION_CAPACITY:
            output.append(location)
    return output

def build_manifests(locations : dict[str, tuple[int, int]]) -> dict[tuple[int, int], list[str]]:
    output = {location: [] for location in POSSIBLE_LOCATIONS}
    for package, location in locations.items():
        output[location].append(package)
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
    # create clock and busy_until dict
    events: list[Event] = []
    clock = START_TIME
    busy_until: dict[str, datetime] = {}
    
    planned_target_route = plan_target_route(locations[TARGET_PACKAGE], available_locations(locations), rng)
    iterations_target_moves_on = rng.sample(range(10, 90), TARGET_MOVES)
    target_move_count = 0

    for i in range(TOTAL_MOVES):
        # advance the clock
        clock = clock + timedelta(seconds=rng.randint(30, 300))
        free_packages = [p for p in packages[1:] if busy_until.get(p, clock) <= clock]
        package = rng.choice(free_packages)
        starting_location = locations[package]
        # package should be moved to another lovation
        available_locations_for_package = available_locations(locations)
        available_locations_for_package.remove(locations[package])
        destination = rng.choice(available_locations_for_package)
        locations[package] = destination
        new_events, end = move(package, starting_location, destination, clock, rng)
        busy_until[package] = end
        events.extend(new_events)
        if i in iterations_target_moves_on:
            start_time = max(clock, busy_until.get(TARGET_PACKAGE, clock))
            new_events, end = move(TARGET_PACKAGE, locations[TARGET_PACKAGE], planned_target_route[target_move_count], start_time, rng)
            busy_until[TARGET_PACKAGE] = end
            locations[TARGET_PACKAGE] = planned_target_route[target_move_count]
            events.extend(new_events)
            target_move_count += 1

    events.sort()
    manifests = build_manifests(locations)

    scenario = Scenario(events, manifests, target_location=locations[TARGET_PACKAGE])

    return scenario

def move(package: str, origin: tuple[int, int], destination: tuple[int, int], now: datetime, rng: random.Random) -> tuple[list[Event], datetime]:
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


if __name__ == "__main__":
    scenario = simulate(1)
    for event in scenario.events[:20]:
        print(event.generate_log())
    print(scenario.target_location)

