from cheating_trap.problem_generator import plan_target_route, available_locations, move, simulate, hamming_distance, corrupt_id, apply_malfunctions, write_scenario, manifest_path, Event, NUM_DEPOSITS, SECTION_CAPACITY, SECTIONS_PER_DEPOSIT, MALFUNCTION_DEPOSITS, TARGET_MOVES, POSSIBLE_LOCATIONS, TARGET_PACKAGE, TOTAL_SECTIONS
from datetime import datetime
from pathlib import Path
import random, pytest, uuid, json

def test_available_locations_all_available():
    assert available_locations({}) == [(x, y) for x in range(1, NUM_DEPOSITS+1) for y in range(1, SECTIONS_PER_DEPOSIT+1)]

def test_available_locations_one_location_unavailable():
    locations = {}
    for package in range(SECTION_CAPACITY):
        locations[str(package)] = (1, 1)
    expected_answer = [(x, y) for x in range(1, NUM_DEPOSITS+1) for y in range(1, SECTIONS_PER_DEPOSIT+1)]
    expected_answer.remove((1, 1))
    assert available_locations(locations=locations) == expected_answer

def event_match(event: Event, package: str, deposit: int, section: int, direction: int) -> bool:
    if package != event.package:
        return False
    if section != event.section:
        return False
    if deposit != event.deposit:
        return False
    if direction != event.direction:
        return False
    return True

def test_move_across_deposits():
    rng = random.Random(1)
    events, _ = move("a", (2, 1), (4, 3), datetime(2026, 10, 1), rng)
    assert len(events) == 4
    assert event_match(events[0], "a", 2, 1, 1)
    assert event_match(events[1], "a", 2, 0, 1)
    assert event_match(events[2], "a", 4, 0, 0)
    assert event_match(events[3], "a", 4, 3, 0)
    assert all(a.timestamp < b.timestamp for a, b in zip(events, events[1:]))

def test_move_within_deposit():
    rng = random.Random(1)
    events, _ = move("a", (3, 1), (3, 2), datetime(2026, 10, 1), rng)
    assert len(events) == 2
    assert event_match(events[0], "a", 3, 1, 1)
    assert event_match(events[1], "a", 3, 2, 0)
    assert all(a.timestamp < b.timestamp for a, b in zip(events, events[1:]))

def test_plan_target_route_many_seeds():
    num_seeds = 1000
    starting_location = (1, 1)
    for i in range(num_seeds):
        rng = random.Random(i)
        planned_route = plan_target_route(starting_location, POSSIBLE_LOCATIONS, rng)
        assert len(planned_route) == TARGET_MOVES
        # at least one malfunction deposit is included
        assert any(location[0] in MALFUNCTION_DEPOSITS for location in planned_route)
        # make sure no location repeats in a row
        planned_route = [starting_location] + planned_route
        assert all(a != b for a, b in zip(planned_route, planned_route[1:]))

def test_plan_target_route_too_few_locations():
    possible_locations = [(1, 1)]
    rng = random.Random(1)
    with pytest.raises(ValueError, match="There are not enough possible locations to plan target route"):
        plan_target_route((1, 1), possible_locations, rng)

def test_plan_target_route_no_malfunction_deposits():
    possible_locations = [(1, 1), (1, 2), (1, 3)]
    rng = random.Random(1)
    with pytest.raises(ValueError, match="No possible locations contain a malfunction for target route"):
        plan_target_route((3, 2), possible_locations, rng)

def test_simulate_target_location():
    for seed in range(1, 6):
        scenario = simulate(seed)
        # retrieve target's last section
        target_events = [e for e in scenario.events if e.package == TARGET_PACKAGE]
        last_event = target_events[-1]
        last_location = (last_event.deposit, last_event.section)
        assert scenario.target_location == last_location
        assert last_event.direction == 0
        assert last_event.section != 0
        assert TARGET_PACKAGE in scenario.manifests[scenario.target_location]

def test_hamming_distance():
    assert hamming_distance("abc", "abc") == 0
    assert hamming_distance("aaa", "abc") == 2
    with pytest.raises(ValueError):
        hamming_distance("a", "ab")

def test_corrupt_id():
    for seed in range(1000):
        rng = random.Random(seed)
        package = str(uuid.UUID(int=rng.getrandbits(128), version=4))
        result = corrupt_id(package, rng)
        assert len(result) == len(package)
        assert hamming_distance(result, package) == 2
        assert [len(s) for s in package.split("-")] == [len(s) for s in result.split("-")]

def test_apply_malfunctions():
    seed = 1
    rng = random.Random(seed)
    scenario = simulate(seed)
    events = scenario.events
    original = list(events)
    deposit_2_exits = sum(1 for e in events if e.deposit == 2 and e.direction == 1)
    other_events = []
    for event in events:
        if event.deposit not in [4, 5] and not (event.deposit == 2 and event.direction == 1):
            other_events.append(event)
    old_4_5_events = [event for event in events if event.deposit in [4, 5]]
    all_packages = [p for section_packages in scenario.manifests.values() for p in section_packages]
    new_events = apply_malfunctions(events, all_packages, rng)
    new_4_5_events = [event for event in new_events if event.deposit in [4, 5]]
    for untouched_event in other_events:
        assert untouched_event in new_events
    assert original == events
    assert len(events) == len(new_events) + deposit_2_exits
    assert len(new_4_5_events) == len(old_4_5_events)
    for i in range(len(new_4_5_events)):
        assert hamming_distance(new_4_5_events[i].package, old_4_5_events[i].package) == 2
    for nv in new_events:
        if nv.direction == 1:
            assert nv.deposit != 2

def test_write_scenario_tmp_path(tmp_path):
    seed = 1
    rng = random.Random(f"malfunctions-{seed}")
    scenario = simulate(seed)
    seed_folder = tmp_path / f"seed-{seed}"
    write_scenario(scenario, seed, tmp_path)

    log_file = seed_folder / "logs.log"
    assert log_file.exists()

    manifest_subfolder = seed_folder / "manifests"
    assert manifest_subfolder.exists()
    assert len(list(manifest_subfolder.iterdir())) == TOTAL_SECTIONS

    ground_truth_file = seed_folder / "ground_truth.json"
    assert ground_truth_file.exists()
    ground_truth = json.loads(ground_truth_file.read_text())
    assert ground_truth["target_package"] == TARGET_PACKAGE
    assert ground_truth["target_deposit"] == scenario.target_location[0]
    assert ground_truth["target_section"] == scenario.target_location[1]

    all_packages = [p for section_packages in scenario.manifests.values() for p in section_packages]
    events_with_malfunctions = apply_malfunctions(scenario.events, all_packages, rng)
    lines_in_logs = log_file.read_text().splitlines()
    assert lines_in_logs == [e.generate_log() for e in events_with_malfunctions]

    for (deposit, section), expected_packages in scenario.manifests.items():
        path = manifest_path(seed_folder, deposit, section)
        listed_packages = path.read_text().splitlines()
        assert listed_packages == expected_packages