import json
import datetime
import time
import websocket
from colorama import Fore
W = Fore.RESET
C = "\033[38;2;75;0;130m"
L = Fore.LIGHTYELLOW_EX
V = Fore.GREEN
B = Fore.LIGHTBLACK_EX
I = Fore.LIGHTRED_EX
class Scrape:
    def __init__(self, token) -> None:
        self.ws = websocket.WebSocket()
        self.ws.connect("wss://gateway.discord.gg/?v=8&encoding=json")
        response = self.ws.recv()
        if response:
            hello = json.loads(response)
            self.heartbeat_interval = hello['d']['heartbeat_interval']
            self.ws.send(json.dumps({"op": 2, "d": {"token": token, "properties": {"$os": "windows", "$browser": "Discord", "$device": "desktop"}}}))
        else:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"{W}{current_time}{C}||Token doesnt work: {token}")
        self.users = []

    def find_user_ids(self, data):
        ids = []
        if isinstance(data, dict):
            if 'username' in data and 'id' in data:
                ids.append(data['id'])
            else:
                for v in data.values():
                    if isinstance(v, (dict, list)):
                        ids.extend(self.find_user_ids(v))
        elif isinstance(data, list):
            for item in data:
                ids.extend(self.find_user_ids(item))
        return ids

    def write_user_ids_to_file(self, file_path):
        with open(file_path, 'w') as file:
            for user_id in self.users:
                file.write(user_id + '\n')

    def send_op14(self, range):
        self.ws.send(json.dumps({
            "op": 14,
            "d": {
                "guild_id": self.guild_id,
                "typing": True,
                "threads": True,
                "activities": True,
                "members": [],
                "channels": {
                    f"{self.channel_id}": [[range * 100, range * 100 + 100 - 1]]
                },
                "thread_member_lists": []
            }
        }))

    def scrape(self, guild_id, channel_id):
            self.guild_id = guild_id
            self.channel_id = channel_id
            self.send_op14(0)
            self.first = False
            last_message = datetime.datetime.now()
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"{W}{current_time}{C}|| Scraping users from Guild ID {self.guild_id}")

            while True:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                response = self.ws.recv()
                if response:
                    try:
                        json_data = json.loads(response)
                        if json_data["t"] == "GUILD_MEMBER_LIST_UPDATE":
                            if not self.first:
                                _range = json_data["d"]["online_count"] / 100
                                for i in range(int(_range) + 2):
                                    time.sleep(1)
                                    self.send_op14(i)
                                self.first = True
                            for ops in json_data["d"]["ops"]:
                                if ops["op"] == "SYNC":
                                    for member in ops["items"]:
                                        try:
                                            member = member["member"]
                                        except KeyError:
                                            continue
                                        user_ids = self.find_user_ids(member)
                                        self.users.extend(user_ids)

                        if (datetime.datetime.now() - last_message).total_seconds() > 10:
                            print(f"{W}{current_time}{C}||Scraped {len(self.users)} users from {self.guild_id}")
                            self.write_user_ids_to_file('user_ids.txt')
                            time.sleep(2.5)
                            return True
                    except json.JSONDecodeError as e:
                        print(f"{W}{current_time}{C}||{I}Error: {e}")
                else:
                    print(f"{W}{current_time}{C}||Couldn't scrape {self.guild_id}")

token = ""
scraper = Scrape(token)
guild_id = ""
channel_id = ""
scraper.scrape(guild_id, channel_id)
