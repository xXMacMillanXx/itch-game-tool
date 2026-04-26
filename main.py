import argparse
from os import mkdir
from os.path import exists

import modules.itch as itch
import modules.utility as utility


def upload_selector(
    uploads: list[itch.ApiUpload], add_skip: bool = False
) -> itch.ApiUpload | None:
    if len(uploads) < 1:
        return None

    if len(uploads) == 1 and not add_skip:
        return uploads[0]

    choice = -1
    while choice < 0:
        print("Multiple uploads were found, please choose the one you're using")
        print(" ------------------------------------------------------------- ")
        for upload in uploads:
            print(
                f" {upload.position}) {upload.display_name if upload.display_name else upload.filename} - updated: {upload.updated_at}"
            )
        if add_skip:
            print(" 9999) Enter information manually...")
        try:
            choice = int(input("Enter number: "))
        except ValueError:
            choice = -1
        for upload in uploads:
            if upload.position == choice:
                return upload
        if add_skip and choice == 9999:
            return None
        print(" ------------------------------------------------------------- ")
        choice = -1


def manual_upload_data(
    upload_id: int, game_id: int, game_version_path: str
) -> itch.ApiUpload:
    utc_now = utility.current_time_utc()
    ret = itch.ApiUpload()
    ret.p_windows = True if input("Windows? (leave empty if no): ") else False
    ret.p_osx = True if input("MacOS? (leave empty if no): ") else False
    ret.p_linux = True if input("Linux? (leave empty if no): ") else False
    ret.host = input("External download site url: ")
    ret.display_name = input("Name of the game: ")
    ret.game_id = game_id
    ret.build_id = 0
    ret.storage = "external"
    ret.demo = True if input("Is the game a demo? (leave empty if no): ") else False
    ret.created_at = utc_now
    ret.channel_name = ""
    ret.preorder = True if input("Is this a preorder? (leave empty if no): ") else False
    ret.p_android = True if input("Android? (leave empty if no): ") else False
    ret.updated_at = utc_now
    ret.type = "default"
    ret.size = utility.size_of_dir(game_version_path)
    ret.position = 0
    ret.id = upload_id
    ret.filename = input("Filename of download (often .zip file): ")

    build = itch.ApiBuild()
    build.parent_build_id = -1
    build.id = 0
    build.version = 1
    build.created_at = utc_now
    build.updated_at = utc_now
    build.upload_id = 0

    ret.build = build
    return ret


def update_game(game_url: str, butler_db_path: str) -> str:
    game_id = itch.get_game_id(game_url)
    db = itch.Database(butler_db_path)

    key = db.get_api_key()
    if not key:
        return "Error: No API key found, stopping program."
    api = itch.API(key)

    uploads = api.fetch_uploads(game_id)
    upload = upload_selector(uploads)

    caves = db.get_caves(game_id)
    if caves:
        for cave in caves:
            print(f"Cave: {cave.id}")
            print(f"Installed upload_id={cave.upload_id} build_id={cave.build_id}")

            inst_loc = db.get_install_location(cave.install_location_id)
            print(f"Install folder: {inst_loc}")

            if not upload:
                return f"Warning: Now uploads from ItchIO are available, can't progress for {args['game_url']} ({game_id})."
            print(
                f"Fresh upload found: channel={upload.channel_name} updated_at={upload.updated_at}"
            )

            if upload.channel_name:
                if cave.build_id == upload.build.id:
                    print(
                        f"Already at latest build #{upload.build.id} ({upload.build.version}) - nothing to do"
                    )
                    continue
                print(
                    f"Updating build: {cave.build_id} -> {upload.build.id} ({upload.build.version})"
                )
            else:
                print("Non-wharf upload. Checking updated_at timestamp...")
                updated = utility.parse(upload.updated_at)
                installed = utility.parse(cave.installed_at)
                if not updated > installed:
                    print(
                        "Info: No newer version found (upload not updated since install) - nothing to do"
                    )
                    continue

                print(
                    "Info: Upload has been updated since last install - updating records"
                )

            print("  -- Updating database")
            now_utc = utility.current_time_utc()
            db.add_or_update_upload(itch.convert_apiupload_to_upload(upload))
            db.add_or_update_build(itch.convert_apibuild_to_build(upload.build))
            updated_cave = itch.merge_cave_with_apiupload(cave, upload, now_utc)
            db.add_or_update_cave(updated_cave)
            print("  -- Database updated")

            print("  -- Updating receipt")
            receipt_dir = f"{inst_loc}/{cave.install_folder_name}/.itch"
            receipt_file = f"{receipt_dir}/receipt.json.gz"
            receipt_json = "{}"
            if not exists(receipt_file):
                mkdir(receipt_dir)
            else:
                receipt_json = utility.read_gz(receipt_file)
            receipt_game = api.fetch_game(cave.game_id)
            receipt = itch.create_receipt(upload, receipt_game, receipt_json)
            utility.write_gz(receipt_file, receipt)
            print("  -- Receipt updated")

            print(f"Cave {cave.id} updated!")
            if upload.build_id != cave.build_id:
                print(f"  build_id: {cave.build_id} -> {upload.build_id}")
            print(f"  upload_id: {cave.upload_id} -> {upload.id}")
            print(f"  installed_at set to: {now_utc}")

    return "Info: Finished successfully!"


def add_game(
    game_url: str,
    butler_db_path: str,
    library_path: str | None,
    game_folder: str,
    version_folder: str,
):
    game_id = itch.get_game_id(game_url)
    db = itch.Database(butler_db_path)

    key = db.get_api_key()
    if not key:
        return "Error: No API key found, stopping program."
    api = itch.API(key)

    library_path = library_path if library_path else db.get_library_location()
    if not library_path:
        return "Error: No game library found, please create an install location in the ItchIO client."
    library_id = db.get_library_id(library_path)
    if not library_id:
        return "Error: Couldn't find library ID, please use a valid ItchIO client install location."

    game_path = f"{library_path}/{game_folder}"
    game_version_path = f"{game_path}/{version_folder}"

    uploads = api.fetch_uploads(game_id)  # check web
    upload = upload_selector(uploads)
    upload_is_manual = False
    if not upload:  # check local
        local_upload_links = db.get_game_uploads(game_id)
        if local_upload_links:
            local_uploads: list[itch.ApiUpload] = []
            for game_upload in local_upload_links:
                local_upload = db.get_upload(game_upload.upload_id)
                if not local_upload:
                    continue
                local_uploads.append(
                    itch.convert_upload_to_apiupload(
                        local_upload, int(game_id), game_upload.position
                    )
                )
            upload = upload_selector(local_uploads, True)
    if not upload:  # fallback to user
        print("Warning: No upload information received, enter manually.")
        upload_id = db.get_next_low_upload_id()
        upload = manual_upload_data(upload_id, int(game_id), game_version_path)
        upload_is_manual = True

    game = api.fetch_game(game_id)
    if upload_is_manual:
        game.p_android = upload.p_android
        game.p_linux = upload.p_linux
        game.p_osx = upload.p_osx
        game.p_windows = upload.p_windows

    itch_path = f"{game_path}/.itch"
    receipt_path = f"{itch_path}/receipt.json.gz"
    if not utility.exists(itch_path):
        mkdir(itch_path)

    old_receipt_data = "{}"
    if utility.exists(receipt_path):
        old_receipt_data = utility.read_gz(receipt_path)
    receipt_data = itch.create_receipt(
        upload, game, game_version_path, old_receipt_data
    )
    utility.write_gz(receipt_path, receipt_data)

    verdict = itch.create_verdict(library_path, game_folder, version_folder)

    db.add_or_update_game(itch.convert_apigame_to_game(game))
    db.add_or_update_upload(itch.convert_apiupload_to_upload(upload))
    caves = db.get_caves(game_id)
    cave_id = 0
    if caves:
        cave_id = caves[0].id
    cave = itch.create_cave(upload, game, verdict, library_id, game_folder)
    if cave_id:
        cave.id = cave_id
    db.add_or_update_cave(cave)

    print("Registered Game:")
    print(f"  Game title: {upload.display_name}")
    print(f"  Game ID: {upload.game_id}")
    print(f"  Cave ID: {cave.id}")
    print(f"  Install path: {library_path}")

    return "Info: Finished successfully!"


def main(args: dict) -> str:
    result: str = "No valid option chosen. Use '-u' or '-a'."

    if args["command"] == "update":
        result = update_game(args["game_url"], args["db_path"])
    elif args["command"] == "add":
        result = add_game(
            args["game_url"],
            args["db_path"],
            args["library_path"],
            args["game_folder"],
            args["version_folder"],
        )

    return result


# --- script starts here ---
parser = argparse.ArgumentParser(description="ItchIO game tool")
subparsers = parser.add_subparsers(dest="command", required=True)

# --- update command ---
update_parser = subparsers.add_parser("update", help="Update installed game")
# "https://user.itch.io/game-name"
update_parser.add_argument("game_url", help="URL to update from")
# "~/.config/itch/db/butler.db"
# "~/.var/app/io.itch.itch/config/itch/db/butler.db"
update_parser.add_argument(
    "db_path",
    nargs="?",
    default="~/.var/app/io.itch.itch/config/itch/db/butler.db",
    help="Optional butler.db path, defaults to flatpak location",
)

# --- add command ---
add_parser = subparsers.add_parser("add", help="Add new game")
add_parser.add_argument("-u", "--game_url", required=True, help="URL")
add_parser.add_argument(
    "-d",
    "--db_path",
    default=f"{utility.home_folder()}/.var/app/io.itch.itch/config/itch/db/butler.db",
    help="Optional butler.db path, defaults to flatpak location",
)
add_parser.add_argument(
    "-l",
    "--library_path",
    default=None,
    help="Optional path to ItchIO game library, defaults to configured library",
)
add_parser.add_argument(
    "-g", "--game_folder", required=True, help="Folder name of the game, 'tic-tac-toe'"
)
add_parser.add_argument(
    "-v",
    "--version_folder",
    required=True,
    help="Folder name of the game version, 'ttt-v1.2'",
)

args = vars(parser.parse_args())
msg = main(args)
print(msg)
