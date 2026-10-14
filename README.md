# Proyecto 1: resolución de nonogramas

**Estudiante:** Leonardo Araya Labarca  
**RUT:** 21.290.314-0  
**Carrera:** IECI 2023

## Requisitos

- Python 3.10 o superior.
- `pytest` solo es necesario para ejecutar las pruebas.

## Ejecución

Desde la carpeta del proyecto:

```bash
python main.py boards/5x5.txt
python main.py boards/10x10.txt --algorithm astar --heuristic uncertainty
python main.py boards/15x15.txt --csv results/nueva_medicion.csv
```

Algoritmos disponibles: `astar`, `bfs`, `dfs` y `greedy`. Heurísticas: `uncertainty` y `cells`.

## Pruebas

```bash
PYTHONPATH=. pytest -q
```

## Formato de entrada

Cada línea contiene las pistas de una fila o columna. Cero representa una línea vacía.

```text
rows:
1 1
3
0
cols:
1
2
1
```

Los ejemplos deterministas están en `boards/`. El programa no genera tableros aleatorios.

## Resultados

Además del tablero resuelto, se muestran tiempo, memoria pico, nodos expandidos, nodos generados y tamaño máximo de la frontera. `--csv` agrega estas métricas a un archivo para repetir el experimento.

## Estructura

- `main.py`: interfaz por consola y exportación de métricas.
- `solver/nonogram.py`: modelo, validación, patrones y búsquedas.
- `boards/`: instancias de 5x5, 10x10 y 15x15.
- `tests/`: pruebas automatizadas.
- `results/metrics.csv`: medición de referencia.
- `docs/`: informe 
