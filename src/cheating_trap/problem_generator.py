from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
import random, uuid, dataclasses, json

TARGET_PACKAGE = "eff6cc6a-bbec-49c6-b3c2-b2eee3937c96"
TARGET_MOVES = 5
SECTION_CAPACITY = 50
NUM_DEPOSITS = 5
TOTAL_MOVES = 100
SECTIONS_PER_DEPOSIT = 3
TOTAL_SECTIONS = NUM_DEPOSITS * SECTIONS_PER_DEPOSIT
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

### RENDERING ###

def render(events: list[Event]) -> str:
    out = "\n".join(e.generate_log() for e in events)
    return out+"\n"

### SIMULATE ###

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

### MALFUNCTIONS ###

# counts the positions in which strings differ
def hamming_distance(a: str, b: str) -> int:
    return sum(c1 != c2 for c1, c2 in zip(a, b, strict=True))

# changes two characters of the package
def corrupt_id(package: str, rng: random.Random) -> str:
    package_chars = list(package)
    hexstrings = "0123456789abcdef"
    corruptable_positions = [i for i in range(len(package)) if package[i] != "-"]
    corrupted_positions = rng.sample(corruptable_positions, 2)
    for i in corrupted_positions:
        new_char = rng.choice(hexstrings.replace(package[i], ""))
        package_chars[i] = new_char
    return "".join(package_chars)

def generate_corrupted_id_without_collision(package: str, all_packages: list[str], rng: random.Random) -> str:
    new_id = corrupt_id(package, rng)

    if any(hamming_distance(new_id, p) <= 2 and p != package for p in all_packages):
        return generate_corrupted_id_without_collision(package, all_packages, rng)
    
    return new_id

def apply_malfunctions(events: list[Event], all_packages: list[str], rng: random.Random) -> list[Event]:
    new_events = []
    for event in events:
        # if deposit is 2 and it is an exit, event will be removed
        if event.deposit == 2 and event.direction == 1:
            continue
        elif event.deposit in [4, 5]:
            new_id = generate_corrupted_id_without_collision(event.package, all_packages, rng)
            new_events.append(dataclasses.replace(event, package=new_id))
        else:
            new_events.append(event)
    return new_events

### WRITING FILES ###

def manifest_path(base_dir: Path, deposit: int, section: int) -> Path:
    return base_dir / "manifests" / f"d{deposit}s{section}.txt"

def write_scenario(scenario: Scenario, seed: int, base_dir: Path) -> None:
    # build seed folder
    seed_folder = base_dir / f"seed-{seed}"
    seed_folder.mkdir(parents=True, exist_ok=True)
    manifest_subfolder = seed_folder / "manifests"
    manifest_subfolder.mkdir(parents=True, exist_ok=True)

    # write log file
    all_packages = [p for section_packages in scenario.manifests.values() for p in section_packages]
    rng = random.Random(f"malfunctions-{seed}")
    events = apply_malfunctions(scenario.events, all_packages, rng)
    log_file = seed_folder / "logs.log"
    log_file.write_text(render(events))
    # write manifest files
    for (deposit, section), packages in scenario.manifests.items():
        manifest_file = manifest_path(seed_folder, deposit, section)
        manifest_file.write_text("\n".join(packages))

    ground_truth_file = seed_folder / "ground_truth.json"
    ground_truth = {
        "target_package": TARGET_PACKAGE,
        "target_deposit": scenario.target_location[0],
        "target_section": scenario.target_location[1],
    }
    ground_truth_file.write_text(json.dumps(ground_truth, indent=2))


if __name__ == "__main__":
    print("Hello World")
