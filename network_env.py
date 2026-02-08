import networkx as nx
import random
import config

class NetworkGraph:
    def __init__(self):
        print(f"Initializing {config.GRID_SIZE}x{config.GRID_SIZE} Grid...")
        self.G = nx.grid_2d_graph(config.GRID_SIZE, config.GRID_SIZE)
        self.pos = dict((n, n) for n in self.G.nodes())

        # Scale positions
        scale_x = (config.WINDOW_WIDTH - 100) / config.GRID_SIZE
        scale_y = (config.MAP_HEIGHT - 100) / config.GRID_SIZE

        for node in self.pos:
            x, y = node
            self.pos[node] = (50 + x * scale_x, 50 + y * scale_y)

        self.reset_network()

    def reset_network(self):
        """Restores everything to perfect condition."""
        for u, v in self.G.edges():
            self.G[u][v]['weight'] = 1      # Normal cost
            self.G[u][v]['status'] = 'up'
        return "%SYS-5-CONFIG_I: Network Reset to Factory Defaults"

    def trigger_mass_failure(self, percentage):
        """HACK: cuts cables (Infinite weight)."""
        self.reset_network()
        edges = list(self.G.edges())
        num_to_fail = int(len(edges) * percentage)

        failed_edges = random.sample(edges, num_to_fail)
        for u, v in failed_edges:
            self.G[u][v]['weight'] = float('inf')
            self.G[u][v]['status'] = 'down'

        return f"CRIT: Hard Failure! {num_to_fail} links severed."

    def trigger_congestion(self, percentage):
        """TRAFFIC: Makes cables slow (High weight)."""
        self.reset_network()
        edges = list(self.G.edges())
        num_to_slow = int(len(edges) * percentage)

        slow_edges = random.sample(edges, num_to_slow)
        for u, v in slow_edges:
            self.G[u][v]['weight'] = 15  # 15x slower than normal
            self.G[u][v]['status'] = 'congested'

        return f"WARN: High Latency Detected on {num_to_slow} interfaces."