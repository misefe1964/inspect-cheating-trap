from cheating_trap.reference_solver import solve
from cheating_trap.problem_generator import NUM_SCENARIOS
from pathlib import Path
import json

def test_solve_with_generated_data():
    data_dir = Path(__file__).resolve().parents[1] / "data"
    for seed in range(1, NUM_SCENARIOS+1):
        log_file = data_dir / f"seed-{seed}" / "logs.log"
        log_text = log_file.read_text()

        ground_truth_file = data_dir / f"seed-{seed}" / "ground_truth.json"
        ground_truth = json.loads(ground_truth_file.read_text())

        result = solve(log_text, ground_truth["target_package"])
        assert result[0] == ground_truth["target_deposit"]
        assert result[1] == ground_truth["target_section"]
