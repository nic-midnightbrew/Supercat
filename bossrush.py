import math
import random
import sys
import pygame

pygame.init()

VIRTUAL_WIDTH, VIRTUAL_HEIGHT = 960, 640
canvas = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

ARENA_MARGIN_X = 50
ARENA_MARGIN_Y = 50
ARENA_WIDTH = VIRTUAL_WIDTH - (ARENA_MARGIN_X * 2)
ARENA_HEIGHT = VIRTUAL_HEIGHT - (ARENA_MARGIN_Y * 2)

WINDOWED_WIDTH, WINDOWED_HEIGHT = 960, 640
screen = pygame.display.set_mode(
    (WINDOWED_WIDTH, WINDOWED_HEIGHT), pygame.RESIZABLE
)
pygame.display.set_caption("Neon Boss Rush (Pygame)")
clock = pygame.time.Clock()
FPS = 60

pygame.mouse.set_visible(False)
is_fullscreen = False

end_overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
end_overlay.fill((10, 12, 18, 220))

#PREGUIÇA de pensar em cor pvfr pensar nas cores e cenário
BG_COLOR = (14, 16, 24)
ARENA_COLOR = (22, 26, 38)
GRID_LINE = (32, 38, 54)
WALL_COLOR = (42, 50, 72)

PLAYER_COLOR = (0, 240, 255)       # Cyan,TEMP
PLAYER_BULLET = (120, 220, 255)
BOSS_COLOR_1 = (255, 0, 110)       # Neon Pink,TEMP
BOSS_COLOR_2 = (255, 180, 0)       # Amber,TEMP
BOSS_COLOR_3 = (180, 0, 255)       # Purple,TEMP
ENEMY_BULLET = (255, 50, 80)
HUD_BG = (10, 12, 18)
ITEM_COLOR = (0, 255, 160)

#INSUPORTÁVEL NUNCA MAIS FAZER!!!
class Projectile:
    def __init__(self, x, y, vel_x, vel_y, damage, range_limit, color=PLAYER_BULLET, size=6):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(vel_x, vel_y)
        self.damage = damage
        self.range_remaining = range_limit
        self.color = color
        self.size = size

    def update(self, dt):
        step = self.vel * (dt * 60.0)
        self.pos += step
        self.range_remaining -= step.length()

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.size)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), max(1, self.size // 2))

#PLAYER DPS MUDAR TÁ MUITO FORTE
class PlayerShip:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.radius = 16

        self.max_speed = 5.2
        self.accel = 0.8
        self.friction = 0.82


        self.hp = 12
        self.max_hp = 12


        self.damage = 4.0
        self.fire_delay = 0.2
        self.fire_cooldown = 0.0
        self.proj_speed = 9.5
        self.proj_range = 420
        self.proj_size = 6

        self.iframe = 0.0

    def handle_input(self, projectiles, dt):
        keys = pygame.key.get_pressed()
        move_dir = pygame.math.Vector2(0, 0)

        if keys[pygame.K_w]:
            move_dir.y -= 1
        if keys[pygame.K_s]:
            move_dir.y += 1
        if keys[pygame.K_a]:
            move_dir.x -= 1
        if keys[pygame.K_d]:
            move_dir.x += 1

        if move_dir.length_squared() > 0:
            move_dir = move_dir.normalize()
            self.vel += move_dir * (self.accel * dt * 60.0)
            if self.vel.length() > self.max_speed:
                self.vel = self.vel.normalize() * self.max_speed

        self.vel *= math.pow(self.friction, dt * 60.0)
        self.pos += self.vel * (dt * 60.0)

        #MARGIN DO CENÁRIO SE PÁ MUDAR DEPENDENDO DO BOSS SE ESSE FOR O JOGO
        self.pos.x = max(ARENA_MARGIN_X + self.radius, min(VIRTUAL_WIDTH - ARENA_MARGIN_X - self.radius, self.pos.x))
        self.pos.y = max(ARENA_MARGIN_Y + self.radius + 10, min(VIRTUAL_HEIGHT - ARENA_MARGIN_Y - self.radius - 20, self.pos.y))

        shoot_dir = pygame.math.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_j]:
            shoot_dir.x -= 1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_l]:
            shoot_dir.x += 1
        elif keys[pygame.K_UP] or keys[pygame.K_i]:
            shoot_dir.y -= 1
        elif keys[pygame.K_DOWN] or keys[pygame.K_k]:
            shoot_dir.y += 1

        if shoot_dir.length_squared() > 0 and self.fire_cooldown <= 0:
            shoot_vec = shoot_dir.normalize() * self.proj_speed
            final_vel = shoot_vec + (self.vel * 0.3)  # Momentum FODA
            projectiles.append(
                Projectile(
                    self.pos.x,
                    self.pos.y,
                    final_vel.x,
                    final_vel.y,
                    self.damage,
                    self.proj_range,
                    PLAYER_BULLET,
                    self.proj_size,
                )
            )
            self.fire_cooldown = self.fire_delay

    def update(self, dt):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt
        if self.iframe > 0:
            self.iframe -= dt

    def draw(self, surface):
        if self.iframe > 0 and int(self.iframe * 20) % 2 == 0:
            return  # Damage flicker MANEIRINHO

        x, y = int(self.pos.x), int(self.pos.y)
        pygame.draw.circle(surface, PLAYER_COLOR, (x, y), self.radius, 2)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 5)

#OS BOSSES SEM CRIATIVIDADE PENSAR É DIFICIL(ODEIO TODOS)
class BossPrism:
    def __init__(self):
        self.name = "FODÂO"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, 200)
        self.radius = 42
        self.hp = 280
        self.max_hp = 280

        self.timer = 0.0
        self.action_timer = 0.0
        self.is_airborne = False
        self.jump_y_offset = 0
        self.jump_target = pygame.math.Vector2(self.pos)

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        self.action_timer += dt

        if not self.is_airborne:
            if self.action_timer >= 2.5:
                self.action_timer = 0.0
                if random.random() < 0.5:
                    dir_to_p = (player_pos - self.pos).normalize()
                    base_angle = math.atan2(dir_to_p.y, dir_to_p.x)
                    for _ in range(8):
                        spread = random.uniform(-0.4, 0.4)
                        spd = random.uniform(3.5, 6.0)
                        vx = math.cos(base_angle + spread) * spd
                        vy = math.sin(base_angle + spread) * spd
                        enemy_projectiles.append(
                            Projectile(self.pos.x, self.pos.y, vx, vy, 1, 380, ENEMY_BULLET, 5)
                        )
                else:
                    self.is_airborne = True
                    self.jump_target = pygame.math.Vector2(player_pos)
                    self.action_timer = 0.0
        else:
            jump_progress = min(1.0, self.action_timer / 0.9)
            self.jump_y_offset = math.sin(jump_progress * math.pi) * 160
            self.pos += (self.jump_target - self.pos) * (0.06 * dt * 60.0)

            if jump_progress >= 1.0:
                self.is_airborne = False
                self.jump_y_offset = 0
                self.action_timer = 0.0
                for i in range(8):
                    a = i * (math.tau / 8)
                    enemy_projectiles.append(
                        Projectile(self.pos.x, self.pos.y, math.cos(a) * 4, math.sin(a) * 4, 1, 280, ENEMY_BULLET, 5)
                    )

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y - self.jump_y_offset)

        if self.is_airborne:
            pygame.draw.ellipse(surface, (10, 10, 15), (int(self.pos.x) - 30, int(self.pos.y) + 20, 60, 20))

        pts = []
        for i in range(8):
            ang = i * (math.tau / 8) + (self.timer * 1.2)
            pts.append((x + math.cos(ang) * self.radius, y + math.sin(ang) * self.radius))

        pygame.draw.polygon(surface, BOSS_COLOR_1, pts, 3)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 8)


#SUPER INUTIL NÃO FAZ NADA PREGUIÇA DE FAZER OS DRONES FUNCIONAR
class BossOrbital:
    def __init__(self):
        self.name = "BETINHA"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, 200)
        self.radius = 38
        self.hp = 360
        self.max_hp = 360
        self.timer = 0.0
        self.drone_timer = 0.0
        self.burst_timer = 0.0
        self.drones = []

    def update(self, enemy_projectiles, dt):
        self.timer += dt
        self.drone_timer += dt
        self.burst_timer += dt

        self.pos.x += math.sin(self.timer * 1.2) * (2.0 * dt * 60.0)
        self.pos.y += math.cos(self.timer * 1.8) * (1.2 * dt * 60.0)

        if self.drone_timer >= 2.67 and len(self.drones) < 4:
            self.drone_timer = 0.0
            self.drones.append({"angle": random.uniform(0, math.tau), "dist": 60})

        for drone in self.drones:
            drone["angle"] += 2.4 * dt

        if self.burst_timer >= 1.83:
            self.burst_timer = 0.0
            for i in range(6):
                a = (self.timer * 6.0) + (i * math.tau / 6)
                enemy_projectiles.append(
                    Projectile(self.pos.x, self.pos.y, math.cos(a) * 3.8, math.sin(a) * 3.8, 1, 320, BOSS_COLOR_2, 5)
                )

    def draw(self, surface):
        x, y = int(self.pos.x), int(self.pos.y)

        pygame.draw.circle(surface, BOSS_COLOR_2, (x, y), self.radius, 3)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 10)

        for drone in self.drones:
            dx = int(self.pos.x + math.cos(drone["angle"]) * drone["dist"])
            dy = int(self.pos.y + math.sin(drone["angle"]) * drone["dist"])
            pygame.draw.circle(surface, BOSS_COLOR_2, (dx, dy), 6)


#AMO AS MULHERES
class BossCore:
    def __init__(self):
        self.name = "PODER FEMININO"
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 40)
        self.radius = 48
        self.hp = 480
        self.max_hp = 480
        self.timer = 0.0
        self.radial_timer = 0.0
        self.aimed_timer = 0.0

    def update(self, player_pos, enemy_projectiles, dt):
        self.timer += dt
        self.radial_timer += dt
        self.aimed_timer += dt

        if self.radial_timer >= 1.5:
            self.radial_timer = 0.0
            for i in range(12):
                a = i * (math.tau / 12)
                enemy_projectiles.append(
                    Projectile(self.pos.x, self.pos.y, math.cos(a) * 3.8, math.sin(a) * 3.8, 1, 400, BOSS_COLOR_3, 6)
                )

        if self.aimed_timer >= 2.16:
            self.aimed_timer = 0.0
            dir_to_p = (player_pos - self.pos).normalize()
            base_a = math.atan2(dir_to_p.y, dir_to_p.x)
            for spread in [-0.15, 0, 0.15]:
                vx = math.cos(base_a + spread) * 5.0
                vy = math.sin(base_a + spread) * 5.0
                enemy_projectiles.append(
                    Projectile(self.pos.x, self.pos.y, vx, vy, 1, 400, BOSS_COLOR_3, 6)
                )

    def draw(self, surface):
        r = int(self.radius + math.sin(self.timer * 7.2) * 4)
        x, y = int(self.pos.x), int(self.pos.y)

        pygame.draw.rect(surface, BOSS_COLOR_3, (x - r, y - r, r * 2, r * 2), width=3, border_radius=6)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 12)

#UPGRADES GENERICOS SEM GRAÇA MAS FUNCIONA(+/-)
class UpgradeCapsule:
    def __init__(self, item_type):
        self.pos = pygame.math.Vector2(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 60)
        self.item_type = item_type
        self.collected = False

    def draw(self, surface, font):
        if self.collected:
            return

        x, y = int(self.pos.x), int(self.pos.y)
        pygame.draw.rect(surface, (40, 50, 70), (x - 20, y, 40, 18), border_radius=3)

        bob = math.sin(pygame.time.get_ticks() * 0.005) * 4
        item_y = y - 20 + bob

        pygame.draw.circle(surface, ITEM_COLOR, (x, int(item_y)), 10, 2)
        pygame.draw.circle(surface, (255, 255, 255), (x, int(item_y)), 4)

        if self.item_type == "CADENCE":
            txt = font.render("(+FIRE RATE)", True, ITEM_COLOR)
        elif self.item_type == "AMPLIFIER":
            txt = font.render("(+DAMAGE)", True, ITEM_COLOR)
        else:
            txt = font.render("(+RANGE & SIZE)", True, ITEM_COLOR)

        surface.blit(txt, txt.get_rect(center=(x, y + 35)))


#MAIN
def main():
    global is_fullscreen, screen

    def reset_game():
        player = PlayerShip(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 120)
        boss_queue = [BossPrism(), BossOrbital(), BossCore()]
        items_queue = ["CADENCE", "AMPLIFIER", "EXTENDER"]
        current_boss = boss_queue.pop(0)
        return player, boss_queue, items_queue, current_boss, None, [], [], 1, False, False

    (
        player,
        boss_queue,
        items_queue,
        current_boss,
        active_capsule,
        player_projectiles,
        enemy_projectiles,
        wave_number,
        game_over,
        victory,
    ) = reset_game()

    font_large = pygame.font.SysFont("consolas", 40, bold=True)
    font_small = pygame.font.SysFont("consolas", 14, bold=True)

    while True:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11 or (
                    event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)
                ):
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(
                            (WINDOWED_WIDTH, WINDOWED_HEIGHT), pygame.RESIZABLE
                        )

                if event.key == pygame.K_r:
                    (
                        player,
                        boss_queue,
                        items_queue,
                        current_boss,
                        active_capsule,
                        player_projectiles,
                        enemy_projectiles,
                        wave_number,
                        game_over,
                        victory,
                    ) = reset_game()

        if not game_over and not victory:
            player.handle_input(player_projectiles, dt)
            player.update(dt)

            if current_boss:
                if isinstance(current_boss, BossOrbital):
                    current_boss.update(enemy_projectiles, dt)
                else:
                    current_boss.update(player.pos, enemy_projectiles, dt)

                    #COLISÃO BEM FRAQUINHA, FAZ MELHOR PFVR
                is_grounded = not getattr(current_boss, "is_airborne", False)
                if is_grounded:
                    diff = player.pos - current_boss.pos
                    min_dist = player.radius + current_boss.radius
                    dist_sq = diff.length_squared()

                    if dist_sq < min_dist * min_dist:
                        dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001
                        push_dir = diff / dist if dist_sq > 0 else pygame.math.Vector2(0, 1)

                        player.pos = current_boss.pos + (push_dir * min_dist)

                        if player.iframe <= 0:
                            player.hp -= 1
                            player.iframe = 1.0
                            if player.hp <= 0:
                                game_over = True

                for p in player_projectiles[:]:
                    if current_boss and (p.pos - current_boss.pos).length() < (p.size + current_boss.radius):
                        current_boss.hp -= p.damage
                        player_projectiles.remove(p)

                        if current_boss.hp <= 0:
                            current_boss = None
                            enemy_projectiles.clear()

                            if len(items_queue) > 0:
                                active_capsule = UpgradeCapsule(items_queue.pop(0))

            if active_capsule and not active_capsule.collected:
                if (player.pos - active_capsule.pos).length() < (player.radius + 20):
                    active_capsule.collected = True

                    if active_capsule.item_type == "CADENCE":
                        player.fire_delay = max(0.06, player.fire_delay - 0.06)
                    elif active_capsule.item_type == "AMPLIFIER":
                        player.damage += 3.0
                    elif active_capsule.item_type == "EXTENDER":
                        player.proj_range += 140
                        player.proj_size += 3

                    if len(boss_queue) > 0:
                        current_boss = boss_queue.pop(0)
                        wave_number += 1
                        active_capsule = None
                    else:
                        victory = True

            for p in player_projectiles[:]:
                p.update(dt)
                if (
                    p.range_remaining <= 0
                    or p.pos.x < ARENA_MARGIN_X
                    or p.pos.x > VIRTUAL_WIDTH - ARENA_MARGIN_X
                    or p.pos.y < ARENA_MARGIN_Y
                    or p.pos.y > VIRTUAL_HEIGHT - ARENA_MARGIN_Y
                ):
                    player_projectiles.remove(p)

            for p in enemy_projectiles[:]:
                p.update(dt)

                if player.iframe <= 0 and (p.pos - player.pos).length() < (p.size + player.radius):
                    player.hp -= 1
                    player.iframe = 1.0  # SE PÁ 0.5 É MELHOR
                    enemy_projectiles.remove(p)
                    if player.hp <= 0:
                        game_over = True
                    continue

                if (
                    p.range_remaining <= 0
                    or p.pos.x < ARENA_MARGIN_X
                    or p.pos.x > VIRTUAL_WIDTH - ARENA_MARGIN_X
                    or p.pos.y < ARENA_MARGIN_Y
                    or p.pos.y > VIRTUAL_HEIGHT - ARENA_MARGIN_Y
                ):
                    enemy_projectiles.remove(p)

        #RENDERIZA O CANVA(NAO ESQUECE DNV)
        canvas.fill(BG_COLOR)


        pygame.draw.rect(canvas, ARENA_COLOR, (ARENA_MARGIN_X, ARENA_MARGIN_Y, ARENA_WIDTH, ARENA_HEIGHT))
        for x in range(ARENA_MARGIN_X, VIRTUAL_WIDTH - ARENA_MARGIN_X, 50):
            pygame.draw.line(canvas, GRID_LINE, (x, ARENA_MARGIN_Y), (x, VIRTUAL_HEIGHT - ARENA_MARGIN_Y))
        for y in range(ARENA_MARGIN_Y, VIRTUAL_HEIGHT - ARENA_MARGIN_Y, 50):
            pygame.draw.line(canvas, GRID_LINE, (ARENA_MARGIN_X, y), (VIRTUAL_WIDTH - ARENA_MARGIN_X, y))


        pygame.draw.rect(canvas, WALL_COLOR, (ARENA_MARGIN_X, ARENA_MARGIN_Y, ARENA_WIDTH, ARENA_HEIGHT), width=3)

        if active_capsule:
            active_capsule.draw(canvas, font_small)

        for p in player_projectiles:
            p.draw(canvas)
        for p in enemy_projectiles:
            p.draw(canvas)

        if current_boss:
            current_boss.draw(canvas)

        if not game_over and not victory:
            player.draw(canvas)

        top_hud = pygame.Rect(0, 0, VIRTUAL_WIDTH, 48)
        pygame.draw.rect(canvas, HUD_BG, top_hud)

        #HP EM BARRINHAS FODINHAS
        for i in range(player.max_hp // 2):
            hx = 20 + (i * 22)
            hy = 24
            if player.hp >= (i + 1) * 2:
                col = PLAYER_COLOR
            elif player.hp == (i * 2) + 1:
                col = (0, 140, 160)
            else:
                col = (30, 40, 50)
            pygame.draw.rect(canvas, col, (hx - 7, hy - 7, 14, 14), border_radius=2)

        #HP DO BOSS EM BARRA SE PÁ TROCAR A COR CONFORME O BOSS MAS SLA PREGUIÇA
        if current_boss:
            bar_w, bar_h = 380, 14
            bar_x = (VIRTUAL_WIDTH - bar_w) // 2
            bar_y = 20
            pct = max(0, current_boss.hp / current_boss.max_hp)
            pygame.draw.rect(canvas, (30, 20, 30), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=3)
            pygame.draw.rect(canvas, BOSS_COLOR_1, (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=2)

            boss_txt = font_small.render(f"{current_boss.name} [WAVE {wave_number}/3]", True, (240, 200, 220))
            canvas.blit(boss_txt, (bar_x, bar_y - 15))

        bot_hud = pygame.Rect(0, VIRTUAL_HEIGHT - 40, VIRTUAL_WIDTH, 40)
        pygame.draw.rect(canvas, HUD_BG, bot_hud)
        pygame.draw.line(canvas, WALL_COLOR, (0, VIRTUAL_HEIGHT - 40), (VIRTUAL_WIDTH, VIRTUAL_HEIGHT - 40), 2)

        ctrl_txt = font_small.render("[WASD] Move  |  [←↑↓→/IJKL] Shoot  |  [F11] Fullscreen", True, (160, 180, 200))
        canvas.blit(ctrl_txt, ctrl_txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT - 20)))

        if game_over or victory:
            canvas.blit(end_overlay, (0, 0))

            if game_over:
                txt = font_large.render("PATÉTICO:BETINHA DEMAIS", True, (255, 50, 80))
                sub = font_small.render("Pressione 'R' para tentar novamente", True, (200, 200, 200))
            else:
                txt = font_large.render("BOSS RUSH FINALIZADO!", True, ITEM_COLOR)
                sub = font_small.render("Pressione 'R' para jogar novamente", True, (200, 200, 200))

            canvas.blit(txt, txt.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 20)))
            canvas.blit(sub, sub.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 + 25)))

        scaled_canvas = pygame.transform.scale(canvas, screen.get_size())
        screen.fill((0, 0, 0))
        screen.blit(scaled_canvas, (0, 0))
        pygame.display.flip()


if __name__ == "__main__":
    main()
    #QUALQUER DUVIDA DE ALGO NISSO ME CHAMA, FOI MAL PELO O INGLÊS, MAS É ASSIM QUE EU FAÇO ^^
    #ACHO QUE ESSE É O MAIS LEGAL DOS QUE EU FIZ, MAS SÃO SÓ PROTÓTIPOS ENTÃO É ISSO