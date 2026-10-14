from pathlib import Path
import pytest
from solver.nonogram import Puzzle, line_patterns, read_puzzle, solve

ROOT = Path(__file__).parents[1]

def test_line_patterns():
    patterns = line_patterns(5, (2, 1))
    assert (1, 1, 0, 1, 0) in patterns
    assert len(patterns) == 3

def test_invalid_total_is_rejected(tmp_path):
    file = tmp_path / "bad.txt"
    file.write_text("rows:\n2\ncols:\n1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_puzzle(str(file))

@pytest.mark.parametrize("name", ["5x5.txt", "10x10.txt", "15x15.txt"])
def test_astar_solves_examples(name):
    puzzle = read_puzzle(str(ROOT / "boards" / name))
    result = solve(puzzle, "astar")
    assert result.solved
    assert result.board is not None
    assert len(result.board) == puzzle.height
