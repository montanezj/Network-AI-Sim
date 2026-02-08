import pygame
import networkx as nx
import math
import random
import time

# Import our modules
import config
from network_env import NetworkGraph
from ai_agent import AIController

def dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def main():
    pygame.init()
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Gemini AI Network Controller - Phase 2")

    # Fonts
    console_font = pygame.font.SysFont("Consolas", 14)
    ui_font = pygame.font.SysFont("Arial", 20, bold=True)
    btn_font = pygame.font.SysFont("Arial", 16, bold=True)
    label_font = pygame.font.SysFont("Arial", 14, bold=True)

    # Initialize Modules
    net = NetworkGraph()
    ai = AIController()

    # State
    start_node = (0, 0)
    end_node = (config.GRID_SIZE-1, config.GRID_SIZE-1)
    packet_path = []
    packet_pos = net.pos[start_node]
    packet_idx = 0

    running = True
    clock = pygame.time.Clock()

    def recalculate_path():
        start_t = time.time()
        try:
            path_nodes = []

            # LOGIC:
            # A_Star (Standard) uses heuristic for speed.
            # Dijkstra (Safety) explores everywhere, safer for hacks.
            # A_Star (Traffic) uses weights to avoid yellow lines.

            if "Dijkstra" in ai.current_algo:
                path_nodes = nx.dijkstra_path(net.G, start_node, end_node, weight='weight')
            else:
                # Both Normal and Traffic modes use A*, but the 'weight' param handles the avoidance
                path_nodes = nx.astar_path(net.G, start_node, end_node, heuristic=lambda u, v: dist(u, v), weight='weight')

            pixel_path = [net.pos[n] for n in path_nodes]
            calc_time = (time.time() - start_t) * 1000
            return pixel_path, f"Route Established via {ai.current_algo} in {calc_time:.1f}ms"

        except nx.NetworkXNoPath:
            return [], f"%ROUTING-F-NO_ROUTE: No route to host {end_node}"
        except Exception as e:
            return [], f"%SYS-3-CPUHOG: Route calc failed - {str(e)}"

    # Initial Calc
    packet_path, msg = recalculate_path()
    ai.history.append(msg)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        is_hovering_btn = config.BTN_RECT.collidepoint(mouse_pos)

        # --- INPUT ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if mouse_pos[1] < config.MAP_HEIGHT:
                        if is_hovering_btn:
                            # RESET
                            msg = net.reset_network()
                            ai.history.append(msg)
                            ai.current_algo = "A_Star"
                            packet_path, msg = recalculate_path()
                            ai.history.append(msg)
                            if packet_path: packet_idx, packet_pos = 0, packet_path[0]
                        else:
                            # NEW PATH
                            start_node = (random.randint(0, config.GRID_SIZE-1), random.randint(0, config.GRID_SIZE-1))
                            end_node = (random.randint(0, config.GRID_SIZE-1), random.randint(0, config.GRID_SIZE-1))
                            packet_path, msg = recalculate_path()
                            ai.history.append(msg)
                            packet_idx = 0
                            packet_pos = net.pos[start_node]

            elif event.type == pygame.KEYDOWN:
                # 'H' for HACK (Breaks Links)
                if event.key == pygame.K_h:
                    packet_path = [] # Signal Loss
                    level = random.uniform(0.1, 0.6)
                    msg = net.trigger_mass_failure(level)
                    ai.history.append(msg)
                    ai.analyze_network(failure_rate=level, traffic_rate=0) # Ask Gemini
                    packet_path, msg = recalculate_path()
                    ai.history.append(msg)
                    if packet_path: packet_idx, packet_pos = 0, packet_path[0]

                # 'T' for TRAFFIC (Congestion)
                if event.key == pygame.K_t:
                    level = random.uniform(0.2, 0.7)
                    msg = net.trigger_congestion(level)
                    ai.history.append(msg)
                    ai.analyze_network(failure_rate=0, traffic_rate=level) # Ask Gemini
                    packet_path, msg = recalculate_path()
                    ai.history.append(msg)
                    # Note: We don't kill the packet here, it just slows down or reroutes
                    if packet_path: packet_idx, packet_pos = 0, packet_path[0]

                # 'R' for RESET
                if event.key == pygame.K_r:
                    msg = net.reset_network()
                    ai.history.append(msg)
                    ai.current_algo = "A_Star"
                    packet_path, msg = recalculate_path()
                    ai.history.append(msg)
                    if packet_path: packet_idx, packet_pos = 0, packet_path[0]

        # --- DRAWING ---
        screen.fill(config.BG_COLOR_MAP)

        # 1. Draw Grid
        for u, v in net.G.edges():
            status = net.G[u][v]['status']
            if status == 'down':
                pygame.draw.line(screen, config.LINK_BROKEN_COLOR, net.pos[u], net.pos[v], 2)
            elif status == 'congested':
                pygame.draw.line(screen, config.LINK_TRAFFIC_COLOR, net.pos[u], net.pos[v], 2)
            else:
                pygame.draw.line(screen, config.GRID_LINE_COLOR, net.pos[u], net.pos[v], 1)

        # 2. Draw Active Path
        if packet_path and len(packet_path) > 1:
            pygame.draw.lines(screen, config.ACTIVE_PATH_COLOR, False, packet_path, 2)

        pygame.draw.circle(screen, (0, 255, 0), (int(net.pos[start_node][0]), int(net.pos[start_node][1])), 6)
        pygame.draw.circle(screen, (255, 0, 0), (int(net.pos[end_node][0]), int(net.pos[end_node][1])), 6)

        # 3. Draw Packet
        if packet_path and len(packet_path) > 1:
            if packet_idx < len(packet_path) - 1:
                target = packet_path[packet_idx + 1]
                dx, dy = target[0] - packet_pos[0], target[1] - packet_pos[1]
                dist_rem = math.hypot(dx, dy)

                # SPEED LOGIC: Slow down if in traffic
                current_speed = config.PACKET_SPEED
                if "Traffic" in ai.current_algo:
                    current_speed = config.PACKET_SPEED * 0.8 # Slightly slower calculation

                if dist_rem < current_speed * 10:
                    packet_pos, packet_idx = target, packet_idx + 1
                else:
                    packet_pos = (packet_pos[0] + (dx/dist_rem)*current_speed*5, packet_pos[1] + (dy/dist_rem)*current_speed*5)
            else:
                packet_idx, packet_pos = 0, packet_path[0]
            pygame.draw.circle(screen, config.PACKET_COLOR, (int(packet_pos[0]), int(packet_pos[1])), 4)

        # 4. CLI
        pygame.draw.rect(screen, config.BG_COLOR_CLI, (0, config.MAP_HEIGHT, config.WINDOW_WIDTH, config.CLI_HEIGHT))
        pygame.draw.line(screen, config.BORDER_COLOR, (0, config.MAP_HEIGHT), (config.WINDOW_WIDTH, config.MAP_HEIGHT), 3)

        y_off = config.SCREEN_HEIGHT - 30
        lines_to_show = int(config.CLI_HEIGHT / 20) - 1
        for log in reversed(ai.history[-lines_to_show:]):
            color = (0, 255, 0)
            if "CRIT" in log or "down" in log: color = (255, 50, 50)
            elif "WARN" in log: color = (255, 165, 0)
            elif "GEMINI" in log: color = (0, 200, 255)
            elif "%" in log: color = (255, 165, 0)

            txt = console_font.render(log, True, color)
            screen.blit(txt, (15, y_off))
            y_off -= 20

            # 5. UI
        btn_col = config.BTN_HOVER_COLOR if is_hovering_btn else config.BTN_COLOR
        pygame.draw.rect(screen, btn_col, config.BTN_RECT, border_radius=5)
        btn_txt = btn_font.render("RESET (R)", True, (255, 255, 255))
        screen.blit(btn_txt, (config.BTN_RECT.x + 15, config.BTN_RECT.y + 10))

        stat_txt = ui_font.render(f"Algo: {ai.current_algo} | 'H' = Hack | 'T' = Traffic", True, (200, 200, 200))
        screen.blit(stat_txt, (15, 10))

        click_txt = label_font.render("[ CLICK MAP TO ROUTE ]", True, (150, 150, 150))
        screen.blit(click_txt, (config.WINDOW_WIDTH // 2 - 100, 20))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()