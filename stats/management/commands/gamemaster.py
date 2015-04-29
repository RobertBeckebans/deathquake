import socket
import os
import time
import random

from django.core.management.base import BaseCommand

from stats.models import Log

# TODO: Consider moving into deathquake/settings.py
LONG_BREAK_EACH_N_ROUND = 4
SMALL_BREAK_MINUTES = 2
LONG_BREAK_MINUTES = 16
GAME_TIME_MINUTES = 8

WARMUP_TIMELIMIT = 99
WARMUP_MESSAGE = "GAME IS LIVE IN %s"
GAME_IS_LIVE_SPAM_SECONDS = 5
GAME_IS_LIVE_MESSAGE = "GAME IS LIVE!"
SERVER_PORT = 27960
SERVER_IP = '127.0.0.1'
RCON_PASSWORD = os.environ['rcon']
RCON_PREFIX = 'rcon "%s" ' % RCON_PASSWORD
CONSOLE_RCON_PREFIX = "\033[93m(RCON)\033[0m"
PACKAGE_PREFIX = b'\xff\xff\xff\xff'


class RandomMaps():
    def __init__(self):
        self.mapList = ['q3dm1', 'q3dm2', 'q3dm3', 'q3dm4', 'q3dm5', 'q3dm6', 'q3dm7', 'q3dm8', 'q3dm9', 'q3dm10',
                        'q3dm11', 'q3dm12', 'q3dm13', 'q3dm14', 'q3dm15', 'q3dm16', 'q3dm17', 'q3dm18', 'q3dm19']
        # Banned maps
        self.mapList.remove('q3dm1')
        self.mapList.remove('q3dm2')

    def pop_random_map(self):
        if not self.mapList:
            self.__init__()
        random_map = random.choice(self.mapList)
        self.mapList.remove(random_map)
        return random_map


class Command(BaseCommand):
    help = 'Automatically controls a Quake 3 server for Deathquake'

    def __init__(self):
        super(Command, self).__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.randomMaps = RandomMaps()
        self.total_games = 1

    def pad_with_spaces(self, message):
        if len(message) < 68:
            return message + (68 - len(message)) * ' '

    def wait_for_map_change(self):
        time.sleep(10)

    def game_is_live_spam(self):
        for y in range(0, GAME_IS_LIVE_SPAM_SECONDS):
            self.say(GAME_IS_LIVE_MESSAGE)

    def start_game(self):
        self.map_restart()
        self.game_is_live_spam()
        self.timelimit(GAME_TIME_MINUTES)
        time.sleep(GAME_TIME_MINUTES * 60)

    def warmup(self):
        self.timelimit(WARMUP_TIMELIMIT)
        if self.total_games % LONG_BREAK_EACH_N_ROUND == 0:
            self.warmup_countdown(LONG_BREAK_MINUTES)
        else:
            self.warmup_countdown(SMALL_BREAK_MINUTES)

    def handle(self, *args, **options):
        self.sock.connect((SERVER_IP, SERVER_PORT))

        while 1:
            self.change_to_random_map()
            self.wait_for_map_change()
            self.warmup()
            self.start_game()
            self.total_games += 1

    def send_rcon(self, command):
        self.sock.sendall(PACKAGE_PREFIX + bytes(RCON_PREFIX + command + '\n', 'utf-8'))
        print(CONSOLE_RCON_PREFIX + ' ' + command)
        time.sleep(1)

    def say(self, message):
        self.send_rcon('"' + self.pad_with_spaces(message) + '"')
        Log(message=message).save()

    def map_restart(self):
        self.send_rcon('map_restart')

    def warmup_countdown(self, warmup_time_in_minutes):
        warmup_time_in_seconds = warmup_time_in_minutes * 60
        for i in range(0, warmup_time_in_seconds):
            minutes, seconds = divmod(warmup_time_in_seconds - i, 60)
            self.say(WARMUP_MESSAGE % ('%02d:%02d' % (minutes, seconds)))

    def change_to_random_map(self):
        new_map = self.randomMaps.pop_random_map()
        self.send_rcon('map ' + new_map)
        self.say('Changing map to ' + new_map)

    def timelimit(self, timelimit):
        self.send_rcon('timelimit %s' % timelimit)
