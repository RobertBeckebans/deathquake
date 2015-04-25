from django.db import models


class Game(models.Model):
    fraglimit = models.IntegerField(default=0)


class Player(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Scoreboard(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(Player)
    score = models.IntegerField()
    game = models.ForeignKey(Game)


class Frag(models.Model):
    game = models.ForeignKey(Game)
    attacker = models.ForeignKey(Player, related_name="frag_attacker")
    victim = models.ForeignKey(Player, related_name="frag_victim")
    weapon = models.CharField(max_length=255)


class Log(models.Model):
    message = models.CharField(max_length=255)