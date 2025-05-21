import tkinter as tk
from tkinter import ttk
import threading
from ANC300 import ANC300App

host = "192.168.10.2" #ANC 300 IP
port = 7230 #standard console port

ANC = ANC300App(host, port) #connect to machine



main = tk.Tk()

style = ttk.Style()
style.configure(
    "Std.TLabel",
    foreground="#000",
    background="#EDECEC",
    anchor="tk.center",
)
style.configure(
    "Txt.TLabel",
    foreground="#000",
    background="#fff",
    anchor="center",
)

style.configure(
    "Std.TButton",
    foreground="#000",
    background="#E4E2E2",
)
main.title("Main Window")
main.config(bg="#E4E2E2")
main.geometry("1000x400")

frame = tk.Frame(master=main)
frame.config(bg="#EDECEC")
frame.place(x=122, y=54, width=1000, height=400)

label = ttk.Label(master=frame, text="Step", style="Std.TLabel")
label.grid(column=4, row=0, padx=10, pady=5)

label1 = ttk.Label(master=frame, text="Move To", style="Std.TLabel")
label1.grid(column=2, row=0, padx=10, pady=5)

label2 = ttk.Label(master=frame, text="Position", style="Std.TLabel", width=10, anchor="center")
label2.grid(column=1, row=0, padx=10, pady=5)

label3 = ttk.Label(master=frame, text="X", style="Std.TLabel", padding=[10,0])
label3.grid(column=0, row=1, padx=10, pady=5)

label4 = ttk.Label(master=frame, text="Y", style="Std.TLabel", padding=[10,0])
label4.grid(column=0, row=2, padx=10, pady=5)

label5 = ttk.Label(master=frame, text="Z", style="Std.TLabel", padding=[10,0])
label5.grid(column=0, row=3, padx=10, pady=5)

PosX = ttk.Label(master=frame, text=f"{ANC.get_output(1)} V", style="Txt.TLabel", width=10, anchor="center")
PosX.grid(column=1, row=1, padx=10, pady=5)

PosY = ttk.Label(master=frame, text=f"{ANC.get_output(2)} V", style="Txt.TLabel", width=10, anchor="center")
PosY.grid(column=1, row=2, padx=10, pady=5)

PosZ = ttk.Label(master=frame, text=f"{ANC.get_output(3)} V", style="Txt.TLabel", width=10, anchor="center")
PosZ.grid(column=1, row=3, padx=10, pady=5)

X_var = tk.StringVar(value="0.0")

MoveX = ttk.Entry(master=frame, textvariable=X_var, style="Txt.TLabel", width=10)
MoveX.grid(column=2, row=1, padx=10, pady=5)

MoveY = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
MoveY.grid(column=2, row=2, padx=10, pady=5)

MoveZ = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
MoveZ.grid(column=2, row=3, padx=10, pady=5)

StepX = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
StepX.grid(column=4, row=1, padx=10, pady=5)

StepY = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
StepY.grid(column=4, row=2, padx=10, pady=5)

StepZ = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
StepZ.grid(column=4, row=3, padx=10, pady=5)

Moves = [MoveX, MoveY, MoveZ]

def set_move(axis): 
    pos = float(Moves[axis-1].get())
    ANC.ramp(axis, pos)

Button_MoveX = ttk.Button(master=frame, text="\u2713", command=lambda: threading.Thread(target=self.move_x_to).start())
Button_MoveX.grid(column=3,row=1)

Button_MoveY = ttk.Button(master=frame, text="\u2713", command=set_move(2))
Button_MoveY.grid(column=3,row=2)

Button_MoveZ = ttk.Button(master=frame, text="\u2713", command=set_move(3))
Button_MoveZ.grid(column=3,row=3)

X_smaller = ttk.Button(master=frame, text="<", style="Std.TButton")
X_smaller.grid(column=5, row=1)
X_larger = ttk.Button(master=frame, text=">", style="Std.TButton")
X_larger.grid(column=6, row=1)

Y_smaller = ttk.Button(master=frame, text="<", style="Std.TButton")
Y_smaller.grid(column=5, row=2)
Y_larger = ttk.Button(master=frame, text=">", style="Std.TButton")
Y_larger.grid(column=6, row=2)

Z_smaller = ttk.Button(master=frame, text="<", style="Std.TButton")
Z_smaller.grid(column=5, row=3)
Z_larger = ttk.Button(master=frame, text=">", style="Std.TButton")
Z_larger.grid(column=6, row=3)


main.mainloop()