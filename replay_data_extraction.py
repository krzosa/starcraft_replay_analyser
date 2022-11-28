import os
import datetime

import mpyq
from s2protocol import versions

from enum import Enum

class League(Enum):
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

def open_replay(path, account_name = "Owen"):
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
  replay["game_events"] = protocol.decode_replay_game_events(coded_game_events)

  coded_message_events = archive.read_file('replay.message.events')
  replay["message_events"] = protocol.decode_replay_message_events(coded_message_events)

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
    p["league"] = League(replay["init_data"]['m_syncLobbyState']['m_userInitialData'][player_index]['m_highestLeague'])

    p["build"] = []

    p["income_minerals"] = []
    p["income_gas"] = []
    p["minerals"] = []
    p["gas"] = []
    p["workers"] = []
    p["army_value_minerals"] = []
    p["army_value_gas"] = []

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

    control_id += 1 #BE_CAREFUL: Seems to work but not sure if it's correct
    player_index += 1
    replay["players"].append(p)

  # if len(replay["players"]) == 2:
  #   if replay["players"][0]["name"] == account_name:
  #     replay["me"] = replay["players"][0]
  #     replay["opp"] = replay["players"][1]

  #   if replay["players"][1]["name"] == account_name:
  #     replay["me"] = replay["players"][1]
  #     replay["opp"] = replay["players"][0]

  #   me = replay.get("me")
  #   opp = replay.get("opp")
  #   if me != None and opp != None:
  #     replay["matchup"] = f"{me['race'][0]}v{opp['race'][0]}"

  return replay

