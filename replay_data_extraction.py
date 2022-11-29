import os
import datetime
import json
import math

import mpyq
from s2protocol import versions

from enum import Enum

UNRANKED = 8
GM = 7
MASTER = 6
DIAMOND = 5
PLATINUM = 4
GOLD = 3
SILVER = 2
BRONZE = 1
VSAI = 0

def walk_replays(dir, recursive = True):
  for path,dirs,files in os.walk(dir):
    if not recursive and path != dir: continue
    for file in files:
      result = path + "/" + file
      yield result

def list_files(path, recursive = True):
  replay_paths = [i for i in walk_replays(path, recursive)]
  return replay_paths

def game_loops_to_time_delta(game_loops):
  return datetime.timedelta(seconds=game_loops/22.4)

def open_replay(path):
  archive = mpyq.MPQArchive(path)
  header_contents = archive.header['user_data_header']['content']
  header = versions.latest().decode_replay_header(header_contents)
  base_build = header['m_version']['m_baseBuild']
  if base_build == 89165: base_build = 88500

  protocol = versions.build(base_build)

  replay = {}

  coded_init_data = archive.read_file('replay.initData')
  replay["init_data"] = protocol.decode_replay_initdata(coded_init_data)

  coded_details = archive.read_file('replay.details')
  replay["details"] = protocol.decode_replay_details(coded_details)

  coded_game_events = archive.read_file('replay.game.events')
  replay["game_events"] = list(protocol.decode_replay_game_events(coded_game_events))

  coded_message_events = archive.read_file('replay.message.events')
  replay["message_events"] = list(protocol.decode_replay_message_events(coded_message_events))

  coded_tracker_events = archive.read_file('replay.tracker.events')
  replay["tracker_events"] = list(protocol.decode_replay_tracker_events(coded_tracker_events))

  replay["path"] = path
  replay["duration"] = game_loops_to_time_delta(header['m_elapsedGameLoops'])
  replay["map"] = replay["details"]["m_title"].decode("utf-8")
  replay["date"] = datetime.datetime.fromtimestamp(round(replay["details"]["m_timeUTC"] / (10 * 1000 * 1000) - 11644473600 - ((replay["details"]['m_timeLocalOffset'] / 10000000))))
  replay["archive"] = archive
  replay["header_content"] = header_contents
  replay["header"] = header

  players = replay["details"]["m_playerList"]
  replay["players"] = []

  control_id = 1 #BE_CAREFUL: Seems to work but not sure if it's correct
  player_index = 0
  for i in players:
    p = {}
    # additional_data = replay["init_data"]["m_syncLobbyState"]["m_userInitialData"][i["m_workingSetSlotId"]]
    
    name = i["m_name"].decode("utf-8")
    p["name"] = name
    if name.find("&gt;<sp/>") != -1:
      clan, p["name"] = name.split("&gt;<sp/>")
      p["clan"] = clan.replace("&lt;", "")
    p["won"] = i["m_result"] == 1
    p["race"] = i["m_race"].decode("utf-8")
    p["mmr"] = replay["init_data"]['m_syncLobbyState']['m_userInitialData'][player_index]['m_scaledRating']
    p["league"] = replay["init_data"]['m_syncLobbyState']['m_userInitialData'][player_index]['m_highestLeague']

    p["build"] = []

    p["income_minerals"] = []
    p["income_gas"] = []
    p["minerals"] = []
    p["gas"] = []
    p["workers"] = []
    p["army_value_minerals"] = []
    p["army_value_gas"] = []

    minutes = replay["duration"].total_seconds() / 60
    actions = 1.4
    for ev in replay["game_events"]:
      id = ev["_userid"]["m_userId"]
      if id == player_index: continue

      match ev["_event"]:
        case "NNet.Game.SControlGroupUpdateEvent" |\
             "NNet.Game.SCameraSaveEvent" |\
             "NNet.Game.SCmdUpdateTargetPointEvent" |\
             "NNet.Game.SCmdUpdateTargetUnitEvent" |\
             "NNet.Game.SCmdEvent" |\
             "NNet.Game.SSelectionDeltaEvent":
          actions += 1.4

    p["apm_avg"] = actions / minutes

    for i in replay["tracker_events"]:
      time = game_loops_to_time_delta(i["_gameloop"])
      if i.get("m_controlPlayerId") != control_id and i.get("m_playerId") != control_id:
        continue
      
      match i["_eventid"]:
        case 6: # SUnitInitEvent
          p["build"].append([time, i["m_unitTypeName"].decode("utf-8")])
          # print(str(time), i["m_unitTypeName"].decode("utf-8"))
        case 0: # SPlayerStatsEvent
          p["income_minerals"].append(i["m_stats"]["m_scoreValueMineralsCollectionRate"])
          p["income_gas"].append(i["m_stats"]["m_scoreValueVespeneCollectionRate"])
          p["minerals"].append(i["m_stats"]["m_scoreValueMineralsCurrent"])
          p["gas"].append(i["m_stats"]["m_scoreValueVespeneCurrent"])
          p["workers"].append(i["m_stats"]["m_scoreValueWorkersActiveCount"])
          p["army_value_minerals"].append(i["m_stats"]["m_scoreValueMineralsUsedCurrentArmy"])
          p["army_value_gas"].append(i["m_stats"]["m_scoreValueVespeneUsedCurrentArmy"])

    p["index"] = player_index
    p["control_id"] = control_id
    control_id += 1 #BE_CAREFUL: Seems to work but not sure if it's correct
    player_index += 1
    replay["players"].append(p)

  return replay


def serialize_replays_to_json(replays):
  """
  Warning! Avoids copies so it alters the data directly.
  Afterwards the data needs to get deserialized to convert string dates to objects etc.
  """
  for i in replays:
    if i.get("init_data"): del i["init_data"]
    if i.get("details"): del i["details"]
    if i.get("game_events"): del i["game_events"]
    if i.get("message_events"): del i["message_events"]
    if i.get("tracker_events"): del i["tracker_events"]
    if i.get("archive"): del i["archive"]
    if i.get("header"): del i["header"]
    if i.get("header_content"): del i["header_content"]
    if type(i["date"]) != str: 
      i["date"] = i["date"].strftime("%Y-%m-%d %H:%M:%S")
    if type(i["duration"]) != str:
      i["duration"] = str(i["duration"])
      if i["duration"].find(".") == -1: 
        i["duration"] += ".000000"

    for p in i.get("players"):
      if p.get("build"): del p["build"]
  result = json.dumps(replays)
  return result

def deserialize_replays(replays):
  if type(replays) == str:
    replays = json.loads(replays)
  for i in replays:
    i["date"] = datetime.datetime.strptime(i["date"], "%Y-%m-%d %H:%M:%S")
    t = datetime.datetime.strptime(i["duration"], "%H:%M:%S.%f")
    i["duration"] = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
  return replays

def is_replay_1v1_ladder(replay):
  if len(replay["players"]) != 2: return False
  if replay["players"][0]["league"] == VSAI: return False
  if replay["players"][1]["league"] == VSAI: return False
  return True

def get_players(replay, account_name):
  if not is_replay_1v1_ladder(replay): return None, None
  if replay["players"][0]["name"] in account_name: return replay["players"][0], replay["players"][1]
  if replay["players"][1]["name"] in account_name: return replay["players"][1], replay["players"][0]
  return None, None

def replay_included(replays, path):
  for r in replays:
    if r["path"] == path: 
      return True
  return False

def try_adding_replay(replays, path):
  if not replay_included(replays, path):
    parsed_replay = open_replay(path)
    replays.append(parsed_replay)

def try_adding_replays(replays, path):
  for i in list_files(path):
    try_adding_replay(replays, i)
  
def read_file(path):
  fd = open(path, "r")
  result = fd.read()  
  fd.close()
  return result

def write_file(path, content):
  fd = open(path, "w")
  fd.write(content)
  fd.close()

def save_replay_cache(replays, file_path):
  cache = serialize_replays_to_json(replays)
  write_file(file_path, cache)
  deserialize_replays(replays)

def sort_replays_by_date(replays): 
  replays.sort(key = lambda x: x["date"])

def filter_replays(replays, player, race):
  filtered_replays = []
  for r in replays:
    if is_replay_1v1_ladder(r):
      me, opp = get_players(r, player)
      if me and me["race"] == race:
        filtered_replays.append(r)
  return filtered_replays

def load_replay_folder(path, cache_file = None):
  replays = []
  if cache_file:
    try: 
      content = read_file(cache_file)
      replays = deserialize_replays(content)
    except FileNotFoundError: 
      replays = []
  
  try_adding_replays(replays, path)
  sort_replays_by_date(replays)
  # save_replay_cache(replays, cache_file)
  return replays


def get_matchup(replay, account):
  me, opp = get_players(replay, account)
  return f"""{me["race"][0]}v{opp["race"][0]}"""