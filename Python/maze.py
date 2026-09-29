import pygame
import random
import sys

CELL_SIZE = 10  # tamaño en píxeles de cada celda

def create_grid(size):
    return [["P" for _ in range(size)] for _ in range(size)]  # P = camino (path)

def create_guaranteed_paths(grid, start, end):
    size = len(grid)
    sx, sy = start
    ex, ey = end
    
    # Limpiar la cuadrícula
    for y in range(size):
        for x in range(size):
            grid[y][x] = "W"  # W = muro
    
    # Ruta 1: horizontal y luego vertical
    for x in range(sx, ex + 1):
        grid[sy][x] = "P"
    for y in range(sy, ey + 1):
        grid[y][ex] = "P"
    
    # Ruta 2: vertical y luego horizontal
    for y in range(sy, ey + 1):
        grid[y][sx] = "P"
    for x in range(sx, ex + 1):
        grid[ey][x] = "P"
    
    # Ruta 3: diagonal con escalones
    x, y = sx, sy
    while x < ex or y < ey:
        if random.random() < 0.5 and x < ex:
            x += 1
        elif y < ey:
            y += 1
        grid[y][x] = "P"

def add_random_walls(grid, density=0.3):
    size = len(grid)
    for y in range(size):
        for x in range(size):
            # Solo añadir muros en celdas que no son parte de las rutas garantizadas
            if grid[y][x] == "P" and random.random() < density:
                grid[y][x] = "W"

def draw_grid(screen, grid, start, end):
    size = len(grid)
    for y in range(size):
        for x in range(size):
            color = (0, 0, 0)  # muro negro
            if grid[y][x] == "P":
                color = (255, 255, 255)  # camino blanco
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, color, rect)

    # inicio (azul) y fin (rojo)
    pygame.draw.rect(screen, (0, 0, 255),
                     (start[0] * CELL_SIZE, start[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(screen, (255, 0, 0),
                     (end[0] * CELL_SIZE, end[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))

def main():
    try:
        size = int(input("Introduce el tamaño del laberinto (mínimo 10): "))
    except ValueError:
        print("Entrada inválida. Usa un número entero.")
        sys.exit(1)

    if size < 10:
        print("El tamaño debe ser al menos 10.")
        sys.exit(1)

    grid = create_grid(size)
    start = (0, 0)
    end = (size - 1, size - 1)

    # Crear rutas garantizadas
    create_guaranteed_paths(grid, start, end)
    
    # Añadir muros aleatorios sin borrar rutas garantizadas
    add_random_walls(grid, density=0.3)

    pygame.init()
    screen = pygame.display.set_mode((size * CELL_SIZE, size * CELL_SIZE))
    pygame.display.set_caption("Laberinto con 3 caminos garantizados")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        draw_grid(screen, grid, start, end)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()