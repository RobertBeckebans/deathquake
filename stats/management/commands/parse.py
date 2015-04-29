from collections import defaultdict
import re
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from stats.models import Game, Player, Frag, Scoreboard, Log

WARNING_PREFIX = '\033[095m(WARNING)\033[0m'


class Command(BaseCommand):
    help = 'Starts parsing and monitoring a Quake 3 log file'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='+', type=str)

    def __init__(self):
        super(Command, self).__init__()
        call_command('truncate')
        self.database = Database()
        self.game_id = 0
        self.database.create_game(self.game_id)
        self.parser_scoreboard = ParserScoreboard()
        self.logfile = None
        self.receiving_scores = False

    def handle(self, *args, **options):
        self.logfile = open(options['file'][0])
        while 1:
            previous_location = self.logfile.tell()
            line = self.logfile.readline()
            if not line:
                self.logfile.seek(previous_location)
                time.sleep(1)
            # Sometimes self.logfile.readline() retrieves a half line from the logfile and this error is fatal to the
            # underlying logic. We therefore wait till we have a newline at the end before parsing it.
            elif not line.endswith('\n'):
                self.logfile.seek(previous_location)
            else:
                self.parse_line(line)

    def parse_line(self, line):
        splitline = line.split(' ')
        action = splitline[0].rstrip()
        if action != 'score:' and self.receiving_scores:
            self.receiving_scores = False
        elif action == 'score:' and not self.receiving_scores:
            self.database.add_new_game(self.game_id, self.parser_scoreboard)
            self.new_game()
            self.receiving_scores = True
        elif action == 'ShutdownGame:':
            self.database.delete_warmup_frags(self.game_id)
            self.new_game()
        elif action == 'Kill:' and not self.contains_more_than_one_killed_string(line):
            attacker_id = int(splitline[1])
            attacker_name = self.extract_attacker_from_frag(line)
            victim_id = int(splitline[2])
            victim_name = self.extract_victim_from_frag(line)
            weapon = splitline[len(splitline) - 1].replace('\n', '')
            self.database.add_player(attacker_id, attacker_name)
            self.database.add_player(victim_id, victim_name)
            self.database.add_frag(self.game_id, attacker_id, victim_id, weapon)
            self.parser_scoreboard.add_frag(attacker_id, victim_id)

    def new_game(self):
        self.parser_scoreboard = ParserScoreboard()
        self.database = Database()
        self.game_id += 1
        self.database.create_game(self.game_id)

    # TODO: Prettify
    def extract_victim_from_frag(self, line):
        splitline = line.split(' ')
        killed_location = 0
        for x in range(0, len(splitline)):
            if splitline[x] == 'killed':
                killed_location = x
        victim_name = ''
        for x in range(killed_location + 1, len(splitline) - 2):
            victim_name += splitline[x]
            if x < (len(splitline) - 3):
                victim_name += ' '
        return victim_name

    # TODO: Prettify
    def extract_attacker_from_frag(self, line):
        splitline = line.split(' ')
        killed_location = 0
        for x in range(0, len(splitline)):
            if splitline[x] == 'killed':
                killed_location = x
        attacker_name = ''
        for x in range(4, killed_location):
            attacker_name += splitline[x]
            if x < killed_location - 1:
                attacker_name += ' '
        return attacker_name

    def contains_more_than_one_killed_string(self, line):
        search = re.compile('(killed.*){2,}', re.MULTILINE).search(line)
        if search is None:
            return False
        else:
            print ('%s IGNORED LINE: %s' % (WARNING_PREFIX, line.replace('\n', '')))
            return True


class Database:
    def __init__(self):
        self.database_prefix = "\033[93m(DATABASE)\033[0m"
        self.database_players = {}

    def add_scoreboard(self, scoreboard, game_id):
        scores = []
        for key, value in scoreboard.items():
            player = self.database_players[key]
            score = value
            scores.append(Scoreboard(player_id=player.id, score=score, game_id=game_id))
            print("%s: added score (playerid=%s, score=%s, gameid=%s)" % (
                self.database_prefix, player.id, score, game_id))

        for score in scores:
            score.save()

    def create_game(self, game_id):
        Game.objects.get_or_create(id=game_id)
        print("%s: Created game (%s)" % (self.database_prefix, game_id))

    def add_player(self, player_id, player_name):
        self.database_players[player_id] = Player.objects.get_or_create(name=player_name)[0]

    def add_new_game(self, game_id, parser_scoreboard):
        Game(id=game_id, fraglimit=parser_scoreboard.get_fraglimit()).save()
        print "%s: added game (%s, %s)" % (self.database_prefix, game_id, parser_scoreboard.get_fraglimit())
        self.add_scoreboard(parser_scoreboard.get_scoreboard(), game_id)

    def truncate(self):
        Game.objects.all().delete()
        Player.objects.all().delete()
        Frag.objects.all().delete()
        Scoreboard.objects.all().delete()
        Log.objects.all().delete()
        print "%s: Truncated tables: games, players, scoreboards" % self.database_prefix

    def add_frag(self, game_id, attacker_id, victim_id, weapon):
        game = Game.objects.get(id=game_id)
        attacker = self.database_players[attacker_id]
        victim = self.database_players[victim_id]
        Frag(game=game, attacker=attacker, victim=victim, weapon=weapon).save()
        print "%s: added frag (game.id=%s, attacker=%s, victim=%s, weapon=%s)" % \
              (self.database_prefix, game.id, attacker, victim, weapon)

    def delete_warmup_frags(self, gameid):
        frags = Frag.objects.filter(game__id=gameid)
        frags.delete()
        print "%s: deleted frags for warmup game with game.id=%s" % (self.database_prefix, gameid)


class ParserScoreboard:
    def __init__(self):
        self.scoreboard = defaultdict(int)

    def get_fraglimit(self):
        result = 0
        for key, value in self.scoreboard.items():
            result = max(value, result)
        return result

    def get_scoreboard(self):
        return self.scoreboard

    def add_frag(self, attacker_id, victim_id):
        world_id = 1022
        if attacker_id == world_id:
            self.scoreboard[victim_id] -= 1
        elif attacker_id == victim_id:
            self.scoreboard[victim_id] -= 1
        else:
            self.scoreboard[attacker_id] += 1