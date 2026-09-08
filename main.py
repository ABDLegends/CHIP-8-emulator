import sys
import random
import pygame

FONT = [
    0xF0, 0x90, 0x90, 0x90, 0xF0, 0x20, 0x60, 0x20, 0x20, 0x70,
    0xF0, 0x10, 0xF0, 0x80, 0xF0, 0xF0, 0x10, 0xF0, 0x10, 0xF0,
    0x90, 0x90, 0xF0, 0x10, 0x10, 0xF0, 0x80, 0xF0, 0x10, 0xF0,
    0xF0, 0x80, 0xF0, 0x90, 0xF0, 0xF0, 0x10, 0x20, 0x40, 0x40,
    0xF0, 0x90, 0xF0, 0x90, 0xF0, 0xF0, 0x90, 0xF0, 0x10, 0xF0,
    0xF0, 0x90, 0xF0, 0x90, 0x90, 0xE0, 0x90, 0xE0, 0x90, 0xE0,
    0xF0, 0x80, 0x80, 0x80, 0xF0, 0xE0, 0x90, 0x90, 0x90, 0xE0,
    0xF0, 0x80, 0xF0, 0x80, 0xF0, 0xF0, 0x80, 0xF0, 0x80, 0x80,
]

KEYS = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF,
}

# --- state -------------------------------------------------------------
memory = bytearray(4096)
memory[0x50:0x50 + len(FONT)] = bytes(FONT)
v = [0] * 16          # registers V0-VF
i_reg = 0              # index register
pc = 0x200             # program counter
stack = []
delay_timer = 0
sound_timer = 0
display = [[0] * 64 for _ in range(32)]
keys = [0] * 16


def load_rom(path):
    with open(path, "rb") as f:
        rom = f.read()
    memory[0x200:0x200 + len(rom)] = rom


def draw_sprite(x, y, n):
    global v
    x, y = v[x] % 64, v[y] % 32
    v[0xF] = 0
    for row in range(n):
        if y + row >= 32:
            break
        byte = memory[i_reg + row]
        for col in range(8):
            if x + col >= 64:
                continue
            if byte & (0x80 >> col):
                if display[y + row][x + col] == 1:
                    v[0xF] = 1
                display[y + row][x + col] ^= 1


def cycle():
    global pc, i_reg, delay_timer, sound_timer

    op = (memory[pc] << 8) | memory[pc + 1]
    pc += 2

    x = (op & 0x0F00) >> 8
    y = (op & 0x00F0) >> 4
    n = op & 0x000F
    nn = op & 0x00FF
    nnn = op & 0x0FFF

    if op == 0x00E0:
        for row in display:
            for col in range(64):
                row[col] = 0
    elif op == 0x00EE:
        pc = stack.pop()
    elif op & 0xF000 == 0x1000:
        pc = nnn
    elif op & 0xF000 == 0x2000:
        stack.append(pc)
        pc = nnn
    elif op & 0xF000 == 0x3000:
        if v[x] == nn:
            pc += 2
    elif op & 0xF000 == 0x4000:
        if v[x] != nn:
            pc += 2
    elif op & 0xF00F == 0x5000:
        if v[x] == v[y]:
            pc += 2
    elif op & 0xF000 == 0x6000:
        v[x] = nn
    elif op & 0xF000 == 0x7000:
        v[x] = (v[x] + nn) & 0xFF
    elif op & 0xF00F == 0x8000:
        v[x] = v[y]
    elif op & 0xF00F == 0x8001:
        v[x] |= v[y]
    elif op & 0xF00F == 0x8002:
        v[x] &= v[y]
    elif op & 0xF00F == 0x8003:
        v[x] ^= v[y]
    elif op & 0xF00F == 0x8004:
        result = v[x] + v[y]
        v[0xF] = 1 if result > 0xFF else 0
        v[x] = result & 0xFF
    elif op & 0xF00F == 0x8005:
        v[0xF] = 1 if v[x] >= v[y] else 0
        v[x] = (v[x] - v[y]) & 0xFF
    elif op & 0xF00F == 0x8006:
        v[0xF] = v[x] & 1
        v[x] = (v[x] >> 1) & 0xFF
    elif op & 0xF00F == 0x8007:
        v[0xF] = 1 if v[y] >= v[x] else 0
        v[x] = (v[y] - v[x]) & 0xFF
    elif op & 0xF00F == 0x800E:
        v[0xF] = (v[x] >> 7) & 1
        v[x] = (v[x] << 1) & 0xFF
    elif op & 0xF00F == 0x9000:
        if v[x] != v[y]:
            pc += 2
    elif op & 0xF000 == 0xA000:
        i_reg = nnn
    elif op & 0xF000 == 0xB000:
        pc = (nnn + v[0]) & 0xFFF
    elif op & 0xF000 == 0xC000:
        v[x] = random.randint(0, 255) & nn
    elif op & 0xF000 == 0xD000:
        draw_sprite(x, y, n)
    elif op & 0xF0FF == 0xE09E:
        if keys[v[x]]:
            pc += 2
    elif op & 0xF0FF == 0xE0A1:
        if not keys[v[x]]:
            pc += 2
    elif op & 0xF0FF == 0xF007:
        v[x] = delay_timer
    elif op & 0xF0FF == 0xF00A:
        pressed = [k for k in range(16) if keys[k]]
        if pressed:
            v[x] = pressed[0]
        else:
            pc -= 2  # keep retrying this instruction until a key is pressed
    elif op & 0xF0FF == 0xF015:
        delay_timer = v[x]
    elif op & 0xF0FF == 0xF018:
        sound_timer = v[x]
    elif op & 0xF0FF == 0xF01E:
        i_reg = (i_reg + v[x]) & 0xFFFF
    elif op & 0xF0FF == 0xF029:
        i_reg = 0x50 + v[x] * 5
    elif op & 0xF0FF == 0xF033:
        memory[i_reg] = v[x] // 100
        memory[i_reg + 1] = (v[x] // 10) % 10
        memory[i_reg + 2] = v[x] % 10
    elif op & 0xF0FF == 0xF055:
        for reg in range(x + 1):
            memory[i_reg + reg] = v[reg]
    elif op & 0xF0FF == 0xF065:
        for reg in range(x + 1):
            v[reg] = memory[i_reg + reg]


def main():
    if len(sys.argv) < 2:
        print("Usage: python chip8_simple.py rom.ch8")
        return
    load_rom(sys.argv[1])

    pygame.init()
    scale = 12
    screen = pygame.display.set_mode((64 * scale, 32 * scale))
    clock = pygame.time.Clock()

    global delay_timer, sound_timer
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in KEYS:
                keys[KEYS[event.key]] = 1
            elif event.type == pygame.KEYUP and event.key in KEYS:
                keys[KEYS[event.key]] = 0

        for _ in range(10):        # run ~10 opcodes per frame
            cycle()

        if delay_timer > 0:
            delay_timer -= 1
        if sound_timer > 0:
            sound_timer -= 1

        screen.fill((10, 15, 10))
        for row in range(32):
            for col in range(64):
                if display[row][col]:
                    pygame.draw.rect(screen, (57, 255, 20), (col * scale, row * scale, scale, scale))
        pygame.display.flip()

        clock.tick(60)             # 60 Hz frame rate = 60 Hz timers

    pygame.quit()


if __name__ == "__main__":
    main()
