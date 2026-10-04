from cheating_trap.problem_generator import hamming_distance

def solve(log_text: str, target: str) -> tuple[int, int]:
    lines = log_text.split("\n")
    target_locations = []
    for line in lines:
        words = line.split(" ")
        if len(words) > 1 and hamming_distance(words[2], target) <= 2:
            target_locations.append(words[6])
    last_deposit, last_section, _ = target_locations[-1].split(".")
    return (int(last_deposit), int(last_section))
