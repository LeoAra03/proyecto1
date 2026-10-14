from __future__ import annotations

import argparse
import csv
from pathlib import Path

from solver.nonogram import board_as_text, read_puzzle, solve


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolución de nonogramas mediante búsqueda")
    parser.add_argument("board", help="Archivo de pistas del nonograma")
    parser.add_argument("--algorithm", choices=["astar", "bfs", "dfs", "greedy"], default="astar")
    parser.add_argument("--heuristic", choices=["uncertainty", "cells"], default="uncertainty")
    parser.add_argument("--csv", help="Archivo CSV donde agregar las métricas")
    args = parser.parse_args()

    puzzle = read_puzzle(args.board)
    result = solve(puzzle, args.algorithm, args.heuristic)

    if result.solved and result.board is not None:
        print(board_as_text(result.board))
    else:
        print("No se encontró solución")

    print(f"algoritmo={result.algorithm}")
    print(f"tiempo_segundos={result.elapsed_seconds:.6f}")
    print(f"memoria_pico_bytes={result.peak_memory_bytes}")
    print(f"nodos_expandidos={result.expanded_nodes}")
    print(f"nodos_generados={result.generated_nodes}")
    print(f"frontera_maxima={result.frontier_max}")

    if args.csv:
        path = Path(args.csv)
        new_file = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if new_file:
                writer.writerow(["tablero", "algoritmo", "heuristica", "resuelto", "tiempo_s", "memoria_bytes", "expandidos", "generados", "frontera_max"])
            writer.writerow([args.board, args.algorithm, args.heuristic, result.solved, result.elapsed_seconds, result.peak_memory_bytes, result.expanded_nodes, result.generated_nodes, result.frontier_max])


if __name__ == "__main__":
    main()
