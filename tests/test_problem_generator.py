from cheating_trap.problem_generator import available_locations, move, Event, NUM_DEPOSITS, SECTION_CAPACITY, SECTIONS_PER_DEPOSIT
from datetime import datetime
import random

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
    assert all(zip(events, events[1:]))

def test_move_within_deposit():
    rng = random.Random(1)
    events, _ = move("a", (3, 1), (3, 2), datetime(2026, 10, 1), rng)
    assert len(events) == 2
    assert event_match(events[0], "a", 3, 1, 1)
    assert event_match(events[1], "a", 3, 2, 0)
    assert all(zip(events, events[1:]))
    