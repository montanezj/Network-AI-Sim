import time
from google import genai
import config

class AIController:
    def __init__(self):
        self.current_algo = "A_Star"
        self.history = ["System Initialized.", "Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M)", "Technical Support: http://www.cisco.com/techsupport"]

        try:
            self.client = genai.Client(api_key=config.GOOGLE_API_KEY)
            self.connected = True
        except:
            self.history.append("WARNING: API Key invalid. AI Offline.")
            self.connected = False

        self.last_request_time = 0
        self.cooldown = 2.0

    def analyze_network(self, failure_rate, traffic_rate):
        """
        Decides between A* (Speed), Dijkstra (Safety), or others based on chaos.
        """
        if not self.connected or time.time() - self.last_request_time < self.cooldown:
            return self.current_algo

        self.last_request_time = time.time()
        self.history.append("Thinking... (Analyzing Telemetry)")

        prompt = f"""
        Network Telemetry:
        - Broken Links: {int(failure_rate * 100)}%
        - Congested Links: {int(traffic_rate * 100)}%
        
        Task: Select Routing Protocol.
        - If Broken > 5% -> 'Dijkstra' (Reliability)
        - If Congested > 10% -> 'A_Star_Weighted' (Avoid Traffic)
        - Otherwise -> 'A_Star' (Speed)
        
        Respond with ONE word only.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite-001",
                contents=prompt
            )
            text = response.text.strip()

            if "Dijkstra" in text:
                algo = "Dijkstra"
            elif "Weighted" in text:
                algo = "A_Star (Traffic Mode)"
            else:
                algo = "A_Star"

            self.history.append(f"GEMINI: Switched to {algo}.")
            self.current_algo = algo
            return algo
        except Exception as e:
            print(f"API Error: {e}")
            self.history.append("API Error. Holding current protocol.")
            return self.current_algo