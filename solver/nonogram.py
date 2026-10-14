from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from heapq import heappop, heappush
from collections import deque
from itertools import count
import tracemalloc
import time

UNKNOWN = -1
EMPTY = 0
FILLED = 1


@dataclass(frozen=True)
class Puzzle:
    rows: tuple[tuple[int, ...], ...]
    cols: tuple[tuple[int, ...], ...]

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.cols)


@dataclass
class SearchResult:
    algorithm: str
    solved: bool
    board: tuple[tuple[int, ...], ...] | None
    elapsed_seconds: float
    peak_memory_bytes: int
    expanded_nodes: int
    generated_nodes: int
    frontier_max: int


@lru_cache(maxsize=None)
def line_patterns(length: int, clues: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    # Este caso representa una línea completamente vacía.
    if not clues or clues == (0,):
        return ((EMPTY,) * length,)
    if any(value <= 0 for value in clues):
        return ()

    patterns: list[tuple[int, ...]] = []

    def place(clue_index: int, position: int, line: list[int]) -> None:
        if clue_index == len(clues):
            patterns.append(tuple(line + [EMPTY] * (length - len(line))))
            return

        block = clues[clue_index]
        remaining = sum(clues[clue_index + 1 :]) + max(0, len(clues) - clue_index - 1)
        last_start = length - block - remaining
        for start in range(position, last_start + 1):
            next_line = line + [EMPTY] * (start - len(line)) + [FILLED] * block
            next_position = start + block
            if clue_index < len(clues) - 1:
                next_line.append(EMPTY)
                next_position += 1
            place(clue_index + 1, next_position, next_line)

    if sum(clues) + len(clues) - 1 <= length:
        place(0, 0, [])
    return tuple(patterns)


def read_puzzle(path: str) -> Puzzle:
    rows: list[tuple[int, ...]] = []
    cols: list[tuple[int, ...]] = []
    section: list[tuple[int, ...]] | None = None

    with open(path, encoding="utf-8") as file:
        for number, raw_line in enumerate(file, 1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            lowered = line.lower()
            if lowered == "rows:":
                section = rows
                continue
            if lowered == "cols:":
                section = cols
                continue
            if section is None:
                raise ValueError(f"Línea {number}: falta indicar rows: o cols:")
            try:
                values = tuple(int(part) for part in line.replace(",", " ").split())
            except ValueError as error:
                raise ValueError(f"Línea {number}: pista no numérica") from error
            section.append(() if values == (0,) else values)

    if not rows or not cols:
        raise ValueError("El archivo debe contener pistas de filas y columnas")
    puzzle = Puzzle(tuple(rows), tuple(cols))
    validate_puzzle(puzzle)
    return puzzle


def validate_puzzle(puzzle: Puzzle) -> None:
    for clue in puzzle.rows:
        if any(value <= 0 for value in clue) or sum(clue) + max(0, len(clue) - 1) > puzzle.width:
            raise ValueError(f"Pista de fila inválida: {clue}")
    for clue in puzzle.cols:
        if any(value <= 0 for value in clue) or sum(clue) + max(0, len(clue) - 1) > puzzle.height:
            raise ValueError(f"Pista de columna inválida: {clue}")
    if sum(map(sum, puzzle.rows)) != sum(map(sum, puzzle.cols)):
        raise ValueError("Las pistas de filas y columnas no tienen la misma cantidad de celdas pintadas")


def _column_domains(puzzle: Puzzle) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(line_patterns(puzzle.height, clue) for clue in puzzle.cols)


def _compatible_domains(
    board: tuple[tuple[int, ...], ...],
    domains: tuple[tuple[tuple[int, ...], ...], ...],
) -> tuple[tuple[tuple[int, ...], ...], ...] | None:
    depth = len(board)
    compatible: list[tuple[tuple[int, ...], ...]] = []
    for column, domain in enumerate(domains):
        prefix = tuple(board[row][column] for row in range(depth))
        matches = tuple(pattern for pattern in domain if pattern[:depth] == prefix)
        if not matches:
            return None
        compatible.append(matches)
    return tuple(compatible)


def heuristic_uncertainty(
    board: tuple[tuple[int, ...], ...],
    compatible: tuple[tuple[tuple[int, ...], ...], ...],
    puzzle: Puzzle,
) -> float:
    # Este valor baja cuando las columnas tienen menos continuaciones posibles.
    remaining = puzzle.height - len(board)
    ambiguity = sum(len(domain) - 1 for domain in compatible)
    return remaining + ambiguity / max(1, puzzle.width)


def heuristic_cells(
    board: tuple[tuple[int, ...], ...],
    compatible: tuple[tuple[tuple[int, ...], ...], ...],
    puzzle: Puzzle,
) -> float:
    # Cuenta las celdas futuras que todavía no están forzadas por las columnas.
    depth = len(board)
    unresolved = 0
    for domain in compatible:
        for row in range(depth, puzzle.height):
            values = {pattern[row] for pattern in domain}
            unresolved += len(values) > 1
    return unresolved / max(1, puzzle.width)


def _goal(board: tuple[tuple[int, ...], ...], puzzle: Puzzle) -> bool:
    return len(board) == puzzle.height


def solve(puzzle: Puzzle, algorithm: str = "astar", heuristic: str = "uncertainty") -> SearchResult:
    algorithm = algorithm.lower()
    if algorithm not in {"astar", "bfs", "dfs", "greedy"}:
        raise ValueError("Algoritmo válido: astar, bfs, dfs o greedy")
    if heuristic not in {"uncertainty", "cells"}:
        raise ValueError("Heurística válida: uncertainty o cells")

    row_domains = tuple(line_patterns(puzzle.width, clue) for clue in puzzle.rows)
    col_domains = _column_domains(puzzle)
    if any(not domain for domain in row_domains) or any(not domain for domain in col_domains):
        return SearchResult(algorithm, False, None, 0.0, 0, 0, 0, 0)

    heuristic_function = heuristic_uncertainty if heuristic == "uncertainty" else heuristic_cells
    serial = count()
    start: tuple[tuple[int, ...], ...] = ()
    expanded = generated = 0
    frontier_max = 1

    if algorithm in {"astar", "greedy"}:
        start_compatible = _compatible_domains(start, col_domains)
        assert start_compatible is not None
        start_h = heuristic_function(start, start_compatible, puzzle)
        frontier_heap: list[tuple[float, int, tuple[tuple[int, ...], ...]]] = []
        heappush(frontier_heap, (start_h, next(serial), start))
    else:
        frontier_linear = deque([start])

    tracemalloc.start()
    started = time.perf_counter()
    solution = None

    while frontier_heap if algorithm in {"astar", "greedy"} else frontier_linear:
        if algorithm in {"astar", "greedy"}:
            _, _, board = heappop(frontier_heap)
        elif algorithm == "bfs":
            board = frontier_linear.popleft()
        else:
            board = frontier_linear.pop()

        expanded += 1
        if _goal(board, puzzle):
            solution = board
            break

        row_index = len(board)
        children = []
        for pattern in row_domains[row_index]:
            child = board + (pattern,)
            compatible = _compatible_domains(child, col_domains)
            if compatible is not None:
                children.append((child, compatible))

        # En DFS se invierte para visitar primero el mismo patrón que usan los otros métodos.
        if algorithm == "dfs":
            children.reverse()

        for child, compatible in children:
            generated += 1
            if algorithm in {"astar", "greedy"}:
                h = heuristic_function(child, compatible, puzzle)
                priority = h if algorithm == "greedy" else len(child) + h
                heappush(frontier_heap, (priority, next(serial), child))
            else:
                frontier_linear.append(child)

        current_size = len(frontier_heap) if algorithm in {"astar", "greedy"} else len(frontier_linear)
        frontier_max = max(frontier_max, current_size)

    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return SearchResult(algorithm, solution is not None, solution, elapsed, peak, expanded, generated, frontier_max)


def board_as_text(board: tuple[tuple[int, ...], ...]) -> str:
    return "\n".join("".join("#" if cell == FILLED else "." for cell in row) for row in board)
