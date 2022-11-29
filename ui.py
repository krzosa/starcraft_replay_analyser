import tkinter as tk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)

import replay_data_extraction as rde

ACCOUNT_NAME = "Owen"
CACHE_FILE = "replays.json"
REPLAY_FOLDER = "replays"

global_last_loaded_replays = None

def try_updating_cache_file(replays):
  global global_last_loaded_replays
  if global_last_loaded_replays != None and len(replays) > len(global_last_loaded_replays):
    rde.save_replay_cache(replays, CACHE_FILE)
  global_last_loaded_replays = replays

def create_history_plots(window):
  frame = tk.Frame(window)
  replays = rde.load_replay_folder(REPLAY_FOLDER, cache_file=CACHE_FILE)
  try_updating_cache_file(replays)

  def add_time_played_per_day():
    times = {}
    for r in replays:
      date = r["date"].date()
      if not times.get(date):
        times[date] = r["duration"]
      else: times[date] += r["duration"]

    values_second = []
    for v in times.values():
      values_second.append(v.seconds)

    def time_formatter(x, pos):
      minutes, seconds = divmod(x, 60)
      hours, minutes = divmod(minutes, 60)
      return f"{int(hours):0>2d}:{int(minutes):0>2d}:{int(seconds):0>2d}"

    fig = Figure(figsize = (8, 4), dpi = 100)
    ax = fig.gca()
    ax.set_title("Time played")
    ax.bar(x=list(times.keys()), height=values_second)
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(time_formatter))
    
    canvas = FigureCanvasTkAgg(fig, master = frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
  add_time_played_per_day()
    
  def add_protoss_mmr():
    #copy_pasta
    filtered_replays_protoss = rde.filter_replays(replays, player=ACCOUNT_NAME, race="Protoss")
    mmr_protoss = []
    for r in filtered_replays_protoss:  
      me, opp = rde.get_players(r, ACCOUNT_NAME)
      mmr_protoss.append(me["mmr"])

    #copy_pasta
    filtered_replays_zerg = rde.filter_replays(replays, player=ACCOUNT_NAME, race="Zerg")
    mmr_zerg = []
    for r in filtered_replays_zerg:  
      me, opp = rde.get_players(r, ACCOUNT_NAME)
      mmr_zerg.append(me["mmr"])

    #copy_pasta
    filtered_replays_terran = rde.filter_replays(replays, player=ACCOUNT_NAME, race="Terran")
    mmr_terran = []
    for r in filtered_replays_terran:  
      me, opp = rde.get_players(r, ACCOUNT_NAME)
      mmr_zerg.append(me["mmr"])

    fig = Figure(figsize = (8, 4), dpi = 100)
    plot = fig.add_subplot(111)
    plot.plot(mmr_protoss, label="Protoss")
    plot.plot(mmr_zerg, label = "Zerg", color="purple")
    plot.plot(mmr_terran, label = "Terran")
    plot.set_title("MMR")
    plot.legend()

    canvas = FigureCanvasTkAgg(fig, master = frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
  add_protoss_mmr()

  

  return frame

def create_replay_plots(window):
  frame = tk.Frame(window)
  replays = rde.load_replay_folder(REPLAY_FOLDER, cache_file=CACHE_FILE)
  try_updating_cache_file(replays)
  
  # Search for last 1v1 replay
  replay = replays[-1]
  i = 0
  while i < (len(replays) - 1):
    index = -1 - i
    replay = replays[index]
    me, opp = rde.get_players(replay, ACCOUNT_NAME) 
    if me != None: break

  me, opp = rde.get_players(replay, ACCOUNT_NAME)

  me_mmr_str = str(me["mmr"])
  opp_mmr_str = str(opp["mmr"])
  won = "won" if me["won"] == 1 else "lost"
  replay_info = tk.Label(frame, text=f"""{won} {me["name"]} {me_mmr_str} VS {opp["name"]} {opp_mmr_str} ({rde.get_matchup(replay, ACCOUNT_NAME)})""")
  replay_info.pack()

  def add_resource_plot():
    resources_1 = np.array(me["minerals"]) + np.array(me["gas"])
    resources_2 = np.array(opp["minerals"]) + np.array(opp["gas"])
    min_shape = min(len(resources_1), len(resources_2))
    resources_1 = resources_1[:min_shape]
    resources_2 = resources_2[:min_shape]

    fig = Figure(figsize = (8, 4), dpi = 100)
    plot = fig.add_subplot(111)
    plot.plot(resources_1, color="green")
    plot.plot(resources_2, color="red")
    plot.set_title("Resources")

    canvas = FigureCanvasTkAgg(fig, master = frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
  add_resource_plot()
    
  def add_income_plot():
    income_1 = np.array(me["income_minerals"]) + np.array(me["income_gas"])
    income_2 = np.array(opp["income_minerals"]) + np.array(opp["income_gas"])
    min_shape = min(len(income_1), len(income_2))
    income_1 = income_1[:min_shape]
    income_2 = income_2[:min_shape]

    fig = Figure(figsize = (8, 4), dpi = 100)
    plot = fig.add_subplot(111)
    plot.plot(income_1, color="green")
    plot.plot(income_2, color="red")

    plot.set_title("Income")

    canvas = FigureCanvasTkAgg(fig, master = frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
  add_income_plot()

  def add_worker_plot():
    workers_me  = me["workers"]
    workers_opp = opp["workers"]

    fig = Figure(figsize = (8, 4), dpi = 100)
    plot = fig.add_subplot(111)

    plot.plot(workers_me , color="green")
    plot.plot(workers_opp, color="red")
    plot.set_title("Workers")

    canvas = FigureCanvasTkAgg(fig, master = frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
  add_worker_plot()

  return frame

content_frame = None
window = None

def on_button_recent_match():
  global content_frame
  global window
  content_frame.destroy()
  content_frame = create_replay_plots(window)
  content_frame.pack()

def on_key_recent_match(e):
  on_button_recent_match()  

def on_button_history():
  global content_frame
  global window
  content_frame.destroy()
  content_frame = create_history_plots(window)
  content_frame.pack()

def on_key_history(e):
  on_button_history()  

def add_button_frame():
  global window
  button_frame = tk.Frame(window)
  button_frame.pack(fill="both")

  button1 = tk.Button(master = button_frame, height = 2, width = 10, text = "Recent Match (F1)", command=on_button_recent_match)
  button1.pack(side="left")
  button2 = tk.Button(master = button_frame, height = 2, width = 10, text = "History (F2)", command=on_button_history)
  button2.pack(side="left")

  window.bind('<F1>', on_key_recent_match)
  window.bind('<F2>', on_key_history)

window = tk.Tk()
add_button_frame()
content_frame = create_history_plots(window)
content_frame.pack()
window.mainloop()
