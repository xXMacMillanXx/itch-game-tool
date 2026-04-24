import json
import sqlite3
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import requests

from modules import utility


@dataclass
class Profile:
    id: int = 0
    api_key: str = ""
    last_connected: str = ""
    user_id: int = 0
    developer: bool = False
    press_user: bool = False


@dataclass
class Upload:
    id: int = 0
    storage: str = ""
    host: str = ""
    filename: str = ""
    display_name: str = ""
    size: int = 0
    channel_name: str = ""
    build_id: int = 0
    type: str = ""
    preorder: bool = False
    demo: bool = False
    windows: str = ""
    linux: str = ""
    osx: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Cave:
    id: str = ""
    game_id: int = 0
    external_game_id: int = 0
    upload_id: int = 0
    build_id: int = 0
    morphing: bool = False
    pinned: bool = False
    installed_at: str = ""
    last_touched_at: str = ""
    seconds_run: int = 0
    snoozed_at: str = ""
    verdict: str = ""
    settings: str = ""
    installed_size: int = 0
    install_location_id: str = ""
    install_folder_name: str = ""
    custom_install_folder: str = ""


@dataclass
class Game:
    id: int = 0
    url: str = ""
    title: str = ""
    short_text: str = ""
    type: str = ""
    classification: str = ""
    cover_url: str = ""
    still_cover_url: str = ""
    created_at: str = ""
    published_at: str = ""
    min_price: int = 0
    can_be_bought: bool = False
    has_demo: bool = False
    in_press_system: bool = False
    windows: str = ""
    linux: str = ""
    osx: str = ""
    user_id: int = 0


@dataclass
class ScriptInfo:
    interpreter: str = ""


@dataclass
class Candidate:
    path: str = ""
    depth: int = 0
    flavor: str = ""
    size: int = 0
    scriptInfo: Optional[ScriptInfo] = None


@dataclass
class Verdict:
    basePath: str = ""
    totalSize: int = 0
    candidates: list[Candidate] = field(default_factory=lambda: [Candidate()])


@dataclass
class InstallLocation:
    id: str = ""
    path: str = ""


@dataclass
class Build:
    id: int = 0
    parent_build_id: int = 0
    state: str = ""
    version: int = 0
    user_version: str = ""
    created_at: str = ""
    updated_at: str = ""


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def __db_call__(self, query: str) -> list[tuple[Any]] | None:
        connection_obj = sqlite3.connect(self.db_path)
        cursor_obj = connection_obj.cursor()
        cursor_obj.execute(query)

        results = cursor_obj.fetchall()
        if not results:  # ensure it's None, rather than empty list
            results = None

        connection_obj.commit()
        connection_obj.close()

        return results

    def get_api_key(self) -> str | None:
        query = "SELECT api_key FROM profiles ORDER BY last_connected DESC LIMIT 1;"
        query = "SELECT * FROM profiles ORDER BY last_connected DESC LIMIT 1;"

        res = self.__db_call__(query)
        profile: Profile | None = None
        if res:
            profile = Profile(*res[0])  # explodes tuple for parameters
        else:
            return None

        return profile.api_key

    def get_caves(self, game_id: str) -> list[Cave] | None:
        query = f"""SELECT *
        FROM caves
        WHERE game_id = {game_id};"""

        res = self.__db_call__(query)
        caves: list[Cave] = []
        if not res:
            return None

        for cave in res:
            caves.append(Cave(*cave))

        return caves

    def get_cave(self, id: str) -> Cave | None:
        query = f"""SELECT *
        FROM caves
        WHERE id = {id};"""

        res = self.__db_call__(query)
        if not res:
            return None

        return Cave(*res[0])

    def get_install_location(self, install_location_id: str) -> str | None:
        query = f"""SELECT *
        FROM install_locations
        WHERE id = '{install_location_id}';"""

        res = self.__db_call__(query)
        if not res:
            return None

        inst_loc = InstallLocation(*res[0])
        return inst_loc.path

    def get_library_location(self) -> str | None:
        query = """SELECT *
        FROM install_locations
        LIMIT 1;"""

        res = self.__db_call__(query)
        if not res:
            return None

        inst_loc = InstallLocation(*res[0])
        return inst_loc.path

    def get_library_id(self, location: str) -> str | None:
        query = f"""SELECT *
        FROM install_locations
        WHERE path = '{location}'
        LIMIT 1;"""

        res = self.__db_call__(query)
        if not res:
            return None

        inst_loc = InstallLocation(*res[0])
        return inst_loc.id

    def get_next_low_upload_id(self) -> int:
        query = """SELECT id
        FROM uploads
        WHERE id = 0;
        """
        res = self.__db_call__(query)
        if not res:
            return 0

        query = """SELECT id
        FROM (
            SELECT id,
                   LEAD(id) OVER (ORDER BY id) AS next_id
            FROM uploads
        ) t
        WHERE next_id IS NULL OR next_id <> id + 1
        ORDER BY id
        LIMIT 1;
        """
        res = self.__db_call__(query)
        if not res:
            return 0

        return res[0][0]

    def add_or_update_game(self, game: Game) -> None:
        query = f"""INSERT INTO games
        VALUES({game.id}, '{game.url}', '{game.title}', '{game.short_text}', '{game.type}',
        '{game.classification}', '{game.cover_url}', '{game.still_cover_url}',
        '{game.created_at}', '{game.published_at}', {game.min_price}, {int(game.can_be_bought)},
        {int(game.has_demo)}, {int(game.in_press_system)}, '{game.windows}', '{game.linux}',
        '{game.osx}', {game.user_id})
        ON CONFLICT(id) DO UPDATE SET
        url = excluded.url,
        title = excluded.title,
        short_text = excluded.short_text,
        type = excluded.type,
        classification = excluded.classification,
        cover_url = excluded.cover_url,
        still_cover_url = excluded.still_cover_url,
        created_at = excluded.created_at,
        published_at = excluded.published_at,
        min_price = excluded.min_price,
        can_be_bought = excluded.can_be_bought,
        has_demo = excluded.has_demo,
        in_press_system = excluded.in_press_system,
        windows = excluded.windows,
        linux = excluded.linux,
        osx = excluded.osx,
        user_id = excluded.user_id;
        """
        self.__db_call__(query)

    def add_or_update_upload(self, upload: Upload) -> None:
        query = f"""INSERT INTO uploads
        VALUES ({upload.id}, '{upload.storage}', '{upload.host}', '{upload.filename}',
        '{upload.display_name}', {upload.size}, '{upload.channel_name}', {upload.build_id},
        '{upload.type}', {int(upload.preorder)}, {int(upload.demo)}, '{upload.windows}',
        '{upload.linux}', '{upload.osx}', '{upload.created_at}', '{upload.updated_at}')
        ON CONFLICT(id) DO UPDATE SET
        storage = excluded.storage,
        host = excluded.host,
        filename = excluded.filename,
        display_name = excluded.display_name,
        size = excluded.size,
        channel_name = excluded.channel_name,
        build_id = excluded.build_id,
        type = excluded.type,
        preorder = excluded.preorder,
        demo = excluded.demo,
        windows = excluded.windows,
        linux = excluded.linux,
        osx = excluded.osx,
        created_at = excluded.created_at,
        updated_at = excluded.updated_at;
        """
        self.__db_call__(query)

    def add_or_update_build(self, build: Build) -> None:
        query = f"""INSERT INTO builds
        VALUES ({build.id}, {build.parent_build_id}, '{build.state}', {build.version},
        '{build.user_version}', '{build.created_at}', '{build.updated_at}')
        ON CONFLICT(id) DO UPDATE SET
        parent_build_id = excluded.parent_build_id,
        state = excluded.state,
        version = excluded.version,
        user_version = excluded.user_version,
        created_at = excluded.created_at,
        updated_at = excluded.updated_at;
        """
        self.__db_call__(query)

    def add_or_update_cave(self, cave: Cave) -> None:
        query = f"""INSERT INTO caves
        VALUES('{cave.id}', {cave.game_id}, {cave.external_game_id}, {cave.upload_id},
        {cave.build_id}, {int(cave.morphing)}, {int(cave.pinned)}, '{cave.installed_at}',
        '{cave.last_touched_at}', {cave.seconds_run}, '{cave.snoozed_at}', '{cave.verdict}',
        '{cave.settings}', {cave.installed_size}, '{cave.install_location_id}',
        '{cave.install_folder_name}', '{cave.custom_install_folder}')
        ON CONFLICT(id) DO UPDATE SET
        upload_id = {cave.upload_id},
        installed_at = '{cave.installed_at}',
        snoozed_at = '',
        build_id = {cave.build_id},
        verdict = '{cave.verdict}';
        """
        self.__db_call__(query)


@dataclass
class ApiBuild:
    parent_build_id: int = 0
    id: int = 0
    version: int = 0
    created_at: str = ""
    updated_at: str = ""
    upload_id: int = 0  # available if in ApiUpload


@dataclass
class ApiUpload:
    p_windows: bool = False
    p_osx: bool = False
    p_linux: bool = False
    host: str = ""  # available if game is extern
    display_name: str = ""
    game_id: int = 0
    build: ApiBuild = field(default_factory=lambda: ApiBuild())
    build_id: int = 0
    storage: str = ""
    demo: bool = False
    created_at: str = ""
    channel_name: str = ""
    preorder: bool = False
    p_android: bool = False
    updated_at: str = ""
    type: str = ""
    size: int = 0
    position: int = 0
    id: int = 0
    filename: str = ""


@dataclass
class ApiUser:
    id: int = 0
    cover_url: str = ""
    username: str = ""
    url: str = ""
    display_name: str = ""
    still_cover_url: str = ""


@dataclass
class ApiGame:
    created_at: str = ""
    cover_url: str = ""
    classification: str = ""
    p_android: bool = False
    published_at: str = ""
    url: str = ""
    id: int = 0
    short_text: str = ""
    title: str = ""
    user: ApiUser = field(default_factory=lambda: ApiUser())
    can_be_bought: bool = False
    min_price: int = 0
    p_windows: bool = False
    p_osx: bool = False
    type: str = ""
    has_demo: bool = False
    in_press_system: bool = False
    p_linux: bool = False


class API:
    def __init__(self, api_key: str) -> None:
        self.url_base = "https://itch.io/api/1"
        self.api_key = api_key
        self.url = f"{self.url_base}/{self.api_key}"

    def fetch_uploads(self, game_id: str | int) -> list[ApiUpload]:
        r = requests.get(f"{self.url}/game/{game_id}/uploads")
        raw_uploads = r.json()["uploads"]

        uploads: list[ApiUpload] = []
        for upload in raw_uploads:
            if "build" in upload.keys():
                raw_build = upload["build"]
                build = ApiBuild(**raw_build)
                upload["build"] = build
            uploads.append(ApiUpload(**upload))

        return uploads

    def fetch_builds(self, upload_id: int) -> list[ApiBuild]:
        r = requests.get(f"{self.url}/upload/{upload_id}/builds")
        raw_builds = r.json()["builds"]

        builds: list[ApiBuild] = []
        for build in raw_builds:
            builds.append(ApiBuild(**build))

        return builds

    def fetch_game(self, game_id: str | int) -> ApiGame:
        r = requests.get(f"{self.url}/game/{game_id}")
        raw_game = r.json()["game"]

        user: ApiUser = ApiUser(**raw_game["user"])
        raw_game["user"] = user
        game: ApiGame = ApiGame(**raw_game)
        return game


def get_game_id(url: str) -> str:
    r = requests.get(url)
    html = r.text
    # <meta name="itch:path" content="games/1234567">
    game_id_index = html.find('content="games/') + len('content="games/')
    return html[game_id_index : html.find('"', game_id_index)]


def to_dict(obj: Any) -> dict:
    return asdict(obj)


def dict_to_json(d: dict) -> str:
    return json.dumps(d)


def to_json(obj: Any) -> str:
    return dict_to_json(to_dict(obj))


def create_candidate(
    game_version_folder: str, exec_filename: str, file_size: int
) -> Candidate:
    flavor = ""
    script = ""
    match exec_filename[exec_filename.rindex(".") :]:
        case ".sh":
            flavor = "script"
            script = "/bin/sh"
        case ".py":
            flavor = "script"
            script = "/usr/bin/env python"
        case ".html":
            flavor = "html"
        case ".bat" | ".cmd":
            flavor = "windows-script"
        case ".exe":
            flavor = "windows"
        case ".jar":
            flavor = "jar"
        case _:
            flavor = "linux"

    if script:
        si = ScriptInfo(script)
        return Candidate(
            f"{game_version_folder}/{exec_filename}",
            2,
            flavor,
            file_size,
            si,
        )
    else:
        return Candidate(
            f"{game_version_folder}/{exec_filename}",
            2,
            flavor,
            file_size,
        )


def create_verdict(
    library_path: str, game_folder: str, game_version_folder: str
) -> Verdict:
    game_path = f"{library_path}/{game_folder}"
    version_path = f"{game_path}/{game_version_folder}"
    exec_filenames = []
    file_extensions = ["sh", "py", "html", "bat", "cmd", "exe", "jar"]
    for ext in file_extensions:
        files = utility.get_files(version_path, f"*.{ext}")
        exec_filenames += files
    candidates = []
    for fn in exec_filenames:
        candidates.append(
            create_candidate(
                game_version_folder, fn, utility.size_of_file(f"{version_path}/{fn}")
            )
        )
    return Verdict(game_path, utility.size_of_dir(game_path), candidates)


def create_receipt(
    upload_: ApiUpload, game_: ApiGame, game_version_path: str, old_receipt: str = "{}"
) -> str:
    existing = json.loads(old_receipt)
    game = to_dict(game_)
    upload = to_dict(upload_)
    build = to_dict(upload_.build)

    receipt = {
        "game": game,
        "upload": upload,
        "build": build,
        "files": utility.get_files(game_version_path, "**", True),
        "installerName": existing.get("installerName"),
    }
    # Remove null values to keep the receipt clean
    receipt = {k: v for k, v in receipt.items() if v is not None}
    return json.dumps(receipt, separators=(",", ":"))


def create_cave(
    upload: ApiUpload,
    game: ApiGame,
    verdict: Verdict,
    install_id: str,
    game_folder: str,
) -> Cave:
    utc_now = utility.current_time_utc()
    d_verdict = to_dict(verdict)
    for idx, candidate in enumerate(verdict.candidates):
        if not candidate.scriptInfo:
            del d_verdict["candidates"][idx]["scriptInfo"]
    return Cave(
        utility.generate_uuid(),
        game.id,
        0,
        upload.id,
        upload.build_id,
        False,
        False,
        utc_now,
        "",
        0,
        "",
        dict_to_json(d_verdict),
        "",
        verdict.totalSize,
        install_id,
        game_folder,
        "",
    )


def convert_apigame_to_game(game: ApiGame) -> Game:
    return Game(
        id=game.id,
        url=game.url,
        title=game.title,
        short_text=game.short_text,
        type=game.type,
        classification=game.classification,
        cover_url=game.cover_url,
        still_cover_url="",
        created_at=game.created_at,
        published_at=game.published_at,
        min_price=game.min_price,
        can_be_bought=game.can_be_bought,
        has_demo=game.has_demo,
        in_press_system=game.in_press_system,
        windows="all" if game.p_windows else "",
        linux="all" if game.p_linux else "",
        osx="all" if game.p_osx else "",
        user_id=game.user.id,
    )


def convert_apiupload_to_upload(upload: ApiUpload) -> Upload:
    return Upload(
        upload.id,
        upload.storage,
        upload.host,
        upload.filename,
        upload.display_name,
        upload.size,
        upload.channel_name,
        upload.build_id,
        upload.type,
        upload.preorder,
        upload.demo,
        "all" if upload.p_windows else "",
        "all" if upload.p_linux else "",
        "all" if upload.p_osx else "",
        upload.created_at,
        upload.updated_at,
    )


def convert_apibuild_to_build(build: ApiBuild) -> Build:
    return Build(
        id=build.id,
        parent_build_id=build.parent_build_id,
        version=build.version,
        created_at=build.created_at,
        updated_at=build.updated_at,
    )


def merge_cave_with_apiupload(
    cave: Cave, upload: ApiUpload, install_date: str = ""
) -> Cave:
    return Cave(
        id=cave.id,
        game_id=cave.game_id,
        external_game_id=cave.external_game_id,
        upload_id=upload.id,
        build_id=upload.build_id,
        morphing=cave.morphing,
        pinned=cave.pinned,
        installed_at=upload.updated_at if not install_date else install_date,
        last_touched_at=cave.last_touched_at,
        seconds_run=cave.seconds_run,
        snoozed_at=cave.snoozed_at,
        verdict=cave.verdict,
        settings=cave.settings,
        installed_size=upload.size,
        install_location_id=cave.install_location_id,
        install_folder_name=cave.install_folder_name,
        custom_install_folder=cave.custom_install_folder,
    )
