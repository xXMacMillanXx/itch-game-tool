# Itch IO Game Tool

## The Issue

The ItchIO client manages your ItchIO games, and updates them,
though some games might not work because they are handled externally,
rather than using the system ItchIO provides.

To solve this, I created a script which can add and update ItchIO games.

## Functionality

Sometimes you have a game, but when you try to update it in the ItchIO client, it suddenly can't.
Maybe because the update isn't handled via ItchIO anymore. In that case:
**Itch client installed a game, but can install the update for it**, you can download
the update, replace them in the ItchIO library game folder and use:

```sh
# this will update the local database
python3 main.py update https://itch.io/game_url

# if you are not using the ItchIO client via flatpak
python3 main.py update https://itch.io/game_url "path/to/butler.db"
# you need to add the path to your butler.db
```

Sometimes a game just can't be added, because you get the game files and they are not
managed by ItchIO. In that case, download the file and unpack it in your ItchIO library,
so you have this structure `<itch_io_library>/<game_name>/<game_version>/<actual_game_files>`.

```sh
# game_name and game_version are the same folder names as described in the structure above
python main.py add -u https://itch.io/game_url -g "game_name" -v "game_version"

# if you are not using the ItchIO client via flatpak
python main.py add -u https://itch.io/game_url -g "game_name" -v "game_version" -d "path/to/butler.db"
# you need to add the path to your butler.db

# If you have multiple ItchIo libraries, you can specify which one you are using for this game
python main.py add -u https://itch.io/game_url -g "game_name" -v "game_version" -l "path/to/ItchIOLibrary"
```

If you added a game this way, use add again if you update the game files, though it's probably not 
necessary for ItchIO to function with the updated files.

## What the script doesn't do

It doesn't download, unpack, copy game files for you.

## What the script does do

It collects needed information via the ItchIO API or the input of the user and sets
the values in the local database so the games are updated or added to the ItchIO client.

## Assumptions

The script assumes the following structure for a game:

```
/path/to/itch_library/game_folder/game_version_folder/game_files

game_files contains all neccesary game data. (game.py, game.sh, game.exe, ... )

As an example:
/mnt/Games/ItchIO/tic-tac-toe/ttt-v0.6/ttt.py
G:\ItchIO\tic-tac-toe\ttt-v0.6\ttt.py
```

## Features for the future?

 - Cleaning up the code (it's a bit messy, but does the job, some dataclasses could be more aligned with the ItchIO interfaces)
 - 
