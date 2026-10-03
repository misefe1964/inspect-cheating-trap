from cheating_trap.problem_generator import available_locations, NUM_DEPOSITS, SECTION_CAPACITY, SECTIONS_PER_DEPOSIT

def test_available_locations_all_available():
    assert available_locations({}) == [(x, y) for x in range(1, NUM_DEPOSITS+1) for y in range(1, SECTIONS_PER_DEPOSIT+1)]

def test_available_locations_one_location_unavailable():
    locations = {}
    for package in range(SECTION_CAPACITY):
        locations[str(package)] = (1, 1)
    expected_answer = [(x, y) for x in range(1, NUM_DEPOSITS+1) for y in range(1, SECTIONS_PER_DEPOSIT+1)]
    expected_answer.remove((1, 1))
    assert available_locations(locations=locations) == expected_answer