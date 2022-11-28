import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

import replay_data_extraction as rde

content_frame = None
window = None
recent_replay = None

def create_replay_plots(window, replay):
  content_frame = tk.Frame(window)
  def add_resource_plot():
    resources_1 = np.array(replay["me"]["minerals"]) + np.array(replay["me"]["gas"])
    resources_2 = np.array(replay["opp"]["minerals"]) + np.array(replay["opp"]["gas"])
    min_shape = min(len(resources_1), len(resources_2))
    resources_1 = resources_1[:min_shape]
    resources_2 = resources_2[:min_shape]

    fig = Figure(figsize = (5, 5), dpi = 100)
    plot = fig.add_subplot(111)
    plot.plot(resources_1, color="green")
    plot.plot(resources_2, color="red")
    plot.set_title("Total resources in time")

    canvas = FigureCanvasTkAgg(fig, master = content_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
  add_resource_plot()
    
  def add_income_plot():
    income_1 = np.array(replay["me"]["income_minerals"]) + np.array(replay["me"]["income_gas"])
    income_2 = np.array(replay["opp"]["income_minerals"]) + np.array(replay["opp"]["income_gas"])
    min_shape = min(len(income_1), len(income_2))
    income_1 = income_1[:min_shape]
    income_2 = income_2[:min_shape]

    fig = Figure(figsize = (5, 5), dpi = 100)
    plot = fig.add_subplot(111)
    plot.plot(income_1, color="green")
    plot.plot(income_2, color="red")

    plot.set_title("Total income in time")

    canvas = FigureCanvasTkAgg(fig, master = content_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
  add_income_plot()
  return content_frame

def on_button_recent_match():
  global content_frame
  global recent_replay
  global window
  content_frame.destroy()
  content_frame = create_replay_plots(window, recent_replay)
  content_frame.pack()

def on_button_history():
  global content_frame
  global recent_replay
  global window
  content_frame.destroy()
    
def add_button_frame():
  button_frame = tk.Frame(window)
  button_frame.pack(fill="both")

  button1 = tk.Button(master = button_frame, height = 2, width = 10, text = "Recent Match (F1)", command=on_button_recent_match)
  button1.pack(side="left")
  button2 = tk.Button(master = button_frame, height = 2, width = 10, text = "History (F2)", command=on_button_history)
  button2.pack(side="left")
  
  window.bind('<F1>', on_button_recent_match)
  window.bind('<F2>', on_button_history)

replay_paths = rde.list_files("replays")
recent_replay = rde.open_replay(replay_paths[0])

window = tk.Tk()
add_button_frame()
content_frame = create_replay_plots(window, recent_replay)
content_frame.pack()
window.mainloop()



  
# content_frame.pack_forget()