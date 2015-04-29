Deathquake
===========

Deathquake is a drinking game for Quake 3 Arena. This repository contains a log parser and a scoreboard.

##Rules
Each round, there are `n` possible sips in one beer.

`n = max(player['frags'] for player in players)`.

Each round, the number of sips each player has to drink is `f`.

`f = player['frags']`.

Each round, everyone drinks `f` sip(s) of their beer which is `f/n` of a beer.

The winner is the person who can drink the most during the game duration, because the person must be good at both drinking beer and playing Quake 3 Arena.

##Screenshot
![Screenshot of Deathquake](http://i.imgur.com/DDgMvdK.png)

##Configuration

###Install ioquake3
http://ioquake3.org/get-it/

###Django Project
Before configuring the django project I strongly recommend that you set up and use a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/).

Install project requirements.

`pip install -r requirements.txt`

####Install PostgreSQL (Optional but recommended)

If you wish to skip this step, jump to **Migrate**.

https://help.ubuntu.com/community/PostgreSQL#Installation

Replace SQLite with PostgreSQL in `deathquake/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'quake',
        'USER': 'postgres',
        'PASSWORD': 'Hunter2',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

Next, install the PostgreSQL adapter psycopg2.

`pip install psycopg2`

#### Migrate

`python manage.py migrate`

Usage
=====

###Start ioquake3
Start ioquake3 with **sudo** and pipe `stderr` into a logfile.

`sudo ioquake3 &> game.log`

In ioquake3, go `Multiplayer` -> `Create` -> `Next` -> Set `Dedicated` to `LAN` and press `Fight`.

Congratulations, your Quake 3 server is now running!

###Parse the logfile
Now start parsing the logfile with the django command parse. The command will monitor a logfile for changes and parse them.

`python manage.py parse game.log`

###Start the webserver
We can now start the Django webserver.

`python manage.py runserver`

Your scoreboard should now be available at `http://127.0.0.1:8000`. Happy fragging!

###Game master (Optional)
The game master command `python manage.py gamemaster` automates map change, warmup periods and breaks. This is _optional_, but remember this, managing a Deathquake game while participating is **HARD**.

It's a good idea to take a look at the variables declared at the top of `stats/management/commands/gamemaster.py` before starting it.

##Notes
* The game is usually played till a player reaches score 16. This is defined through the variable `DEATHQUAKE_WINNER_SCORE` in `deathquake/settings.py`.
* Remember to set the timelimit to 99 when warming up. The parser picks up every single game that ends with a scoreboard!
* It's possible to play towards a **fraglimit**, however it's my experience that playing towards a **timelimit** works best.

###Server configuration
Here is my `~/.q3a/base3/server.cfg` which I execute with `\exec server` after starting the server.

```
seta sv_hostname "Deathquake"
seta sv_maxclients 16
seta fraglimit 0
seta timelimit 10
seta g_gametype 0
seta g_forcerespawn 0
seta rconpassword "Hunter2"
```

* Note that changes to `sv_maxclients` will take effect on map change.
