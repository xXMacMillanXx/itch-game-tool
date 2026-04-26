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

In case update doesn't work, try using add instead.

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

## Example Use

### Add a game (which the ItchIO client doesn't install, because the files are handled externally)

1. Download the game from itch or the itch provided download link (external website)
2. Unzip the downloaded file (usually an archive like .zip)
3. Copy the folder into your ItchIO game library:
  - If your ItchIO game library is `path/to/ItchIOGames` copy it into a new folder in ItchIOGames
  - The new folder should be the name of the game in lower case, like this: `Tic-Tac-Toe-0.3.5-pc.zip` -> `tic-tac-toe`
  - Inside your new folder (here: `tic-tac-toe`) the naming isn't that important, but I would call it `TicTacToe-0.3.5-pc` in this case
  - **Important** Be sure that the game files (like the .exe, .py or .sh) are inside the `TicTacToe-0.3.5-pc` folder:

```txt
path/to/ItchIOGames
 |- tic-tac-toe
     |- TicTacToe-0.3.5-pc
         |- game/
         |- data/
         |- ttt.exe
         |- ttt.py
         |- ttt.sh
```

With the game data prepared, call the script:

```bash
# If you are on Linux with the ItchIO client flatpak
python3 main.py add -u https://user.itch.io/game -g tic-tac-toe -v TicTacToe-0.3.5-pc

# In any other case (Windows, Mac or Linux without the flatpak) you want to add the path to the ItchIO database manually
# This should be the location for Linux with the non-flatpak client, for Mac and Windows you need to google or search for it 
python3 main.py add -u https://user.itch.io/game -g tic-tac-toe -v TicTacToe-0.3.5-pc -d /home/<username>/.config/itch/db/butler.db
```

Everything should be handled automatically unless the script can't find information via the ItchIO API or the local DB, in which case
the user has to provide the information.

### Update a game (which the ItchIO client can't update, because the files are suddenly handled externally)

1. Download the game from itch or the itch provided download link (external website)
2. Unzip the downloaded file (usually an archive like .zip)
3. Copy the game files into your ItchIO game library game (version) folder:
  - If your ItchIO game is located at `path/to/ItchIOGames/game-name` copy the game files into its folder inside `game-name/game-name-0.0.0-pc`
  - This should overwrite all the game files, essentially updating the game.
  - **Important** Be sure that the game files (like the .exe, .py or .sh) are inside the folder, inside the game folder:

```txt
path/to/ItchIOGames
 |- game-name
     |- game-name-0.0.0-pc
         |- game/
         |- data/
         |- game.exe
         |- game.py
         |- game.sh
```

With the game data prepared, call the script:

```bash
# If you are on Linux with the ItchIO client flatpak
python3 main.py update https://user.itch.io/game

# In any other case (Windows, Mac or Linux without the flatpak) you want to add the path to the ItchIO database manually
# This should be the location for Linux with the non-flatpak client, for Mac and Windows you need to google or search for it 
python3 main.py update https://user.itch.io/game /home/<username>/.config/itch/db/butler.db
```

Everything should be handled automatically unless the script can't find information via the ItchIO API.

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

 - Cleaning up the code, it's a bit of a mess (but does the job)
   - some dataclasses could be more aligned with the ItchIO interfaces
   - some code segments could be functions, maybe even reused
 - **maybe** a command which handles the unzip and copying of files, but only maybe
