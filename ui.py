import tkinter as tk
import datetime

window = tk.Tk()
window.geometry("100x50+0+0")
window.attributes("-topmost", "true")

start_button = None
timer_text = tk.StringVar(value="0:00")
timer = 0
stop = 60*50
timer_running = True


def handle_start():
  global timer_running
  global timer
  global stop
  global timer_text
  global start_button

  start_button.configure(command=handle_pause, text="pause")
  if timer_running:
    timer += 1

    
    timer_text.set(str(datetime.timedelta(seconds=timer)))
    window.update()
  if timer < stop:
    window.after(1000, handle_start)

def handle_pause():
  global timer_running
  timer_running = not timer_running


start_button = tk.Button(text="start", command=handle_start)
start_button.pack()

# pause_button = tk.Button(text="pause", command=handle_pause)
# pause_button.pack()

timer_label = tk.Label(textvariable=timer_text)
timer_label.pack()

# window.bind('<Control-i>', handle_start_bind)
window.mainloop()
