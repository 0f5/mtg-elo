import elo
import json
import os


class liga:

    def __init__(self, storage=None):
        self.game_id = 0
        self.players = {}
        self.games = {}
        self.storage = storage

        if(storage != None):

            # if file does not exist, create it
            if not os.path.exists(storage):
                with open(storage, 'w') as f:
                    json.dump({"players": {}, "games": {}}, f)

            with open(storage, "r") as f:
                d = json.load(f)
                self.players = d["players"]
                self.games = d["games"]

    def save(self):
        with open(self.storage, 'w') as f:
            #players = [{"id": k, "deck": p["deck"],"elo":p["elo"], "name":p["name"]} for k, p in .items()]
            #games = [{"id": k, "player1": g[0], "player2": g[1], "result": g[2]} for k, g in .items()]
            json.dump({"players": self.players, "games": self.games}, f)

    def register_player(self, id, name, deck):
        self.players[id] = {"name": name, "deck": deck, "elo": 1500}
        self.save()

    def change_result(self, game, result):
        self.games[game] = result

        # reevaluate elo
        games = self.games
        self.games = {}
        for player in self.players:
            self.players[player]["elo"] = 1500
        for game in games:
            self.register_game(game[0], game[1], game[2])
        self.save()

    def delete_game(self, game):
        del self.games[game]

        # reevaluate elo
        games = self.games
        self.games = {}
        for player in self.players:
            self.players[player]["elo"] = 1500
        for game in games:
            self.register_game(game[0], game[1], game[2])
        self.save()
    
    def register_game(self, player1, player2, result, timestamp):
        """
        result:
        1 - player1 won
        0 - player2 won
        0.5 - draw
        """
        if(self.players.get(player1) == None):
            raise Exception("Player 1 not found")
        if(self.players.get(player2) == None):
            raise Exception("Player 2 not found")
        if(player1 == player2):
            raise Exception("Players must be different")

        game_id = self.game_id
        self.game_id += 1

        self.games[game_id] = (player1, player2, result, timestamp)
        self.players[player1]["elo"], self.players[player2]["elo"] = elo.update_elo(self.players[player1]["elo"], self.players[player2]["elo"], result)
        self.save()


        