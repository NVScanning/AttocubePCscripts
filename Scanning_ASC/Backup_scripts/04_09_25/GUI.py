import tkinter as tk
from tkinter import ttk
import threading
from ANC300 import ANC300App

host = "192.168.10.2" #ANC 300 IP
port = 7230 #standard console port

ANC = ANC300App(host, port) #connect to machine
main = tk.Tk()

icon = tk.PhotoImage(file='GUIlogo.png')
main.geometry("1000x400")
main.title("NV Scanning")
main.iconphoto(True,icon)
main.config(bg="#E4E2E2")

frame = tk.Frame(master=main)
frame.config(bg="#EDECEC")

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
    width=3,
)

frame.place(x=122, y=54, width=1000, height=400)

#Title labels
label = ttk.Label(master=frame, text="Step", style="Std.TLabel")
label1 = ttk.Label(master=frame, text="Move To", style="Std.TLabel")
label2 = ttk.Label(master=frame, text="Position", style="Std.TLabel", width=10, anchor="center")
label3 = ttk.Label(master=frame, text="X", style="Std.TLabel", padding=[10,0])
label4 = ttk.Label(master=frame, text="Y", style="Std.TLabel", padding=[10,0])
label5 = ttk.Label(master=frame, text="Z", style="Std.TLabel", padding=[10,0])
label.grid(column=4, row=0, padx=10, pady=5)
label1.grid(column=2, row=0, padx=10, pady=5)
label2.grid(column=1, row=0, padx=10, pady=5)
label3.grid(column=0, row=1, padx=10, pady=5)
label4.grid(column=0, row=2, padx=10, pady=5)
label5.grid(column=0, row=3, padx=10, pady=5)


#Dynamic position labels
PosX_var = tk.StringVar()
PosY_var = tk.StringVar()
PosZ_var = tk.StringVar()

dynamiclabels = [PosX_var, PosY_var, PosZ_var]
for i in range(3):
    dynamiclabels[i].set(f"{ANC.get_output(i+1, print=False)} V")

PosX = ttk.Label(master=frame, textvar=PosX_var, style="Txt.TLabel", width=10, anchor="center")
PosY = ttk.Label(master=frame, textvar=PosY_var, style="Txt.TLabel", width=10, anchor="center")
PosZ = ttk.Label(master=frame, textvar=PosZ_var, style="Txt.TLabel", width=10, anchor="center")
PosX.grid(column=1, row=1, padx=10, pady=5)
PosY.grid(column=1, row=2, padx=10, pady=5)
PosZ.grid(column=1, row=3, padx=10, pady=5)

#User entries for movement
MoveX = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
MoveY = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
MoveZ = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
StepX = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
StepY = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
StepZ = ttk.Entry(master=frame, style="Txt.TLabel", width=10)
MoveX.grid(column=2, row=1, padx=10, pady=5)
MoveY.grid(column=2, row=2, padx=10, pady=5)
MoveZ.grid(column=2, row=3, padx=10, pady=5)
StepX.grid(column=4, row=1, padx=10, pady=5)
StepY.grid(column=4, row=2, padx=10, pady=5)
StepZ.grid(column=4, row=3, padx=10, pady=5)

Moves = [MoveX, MoveY, MoveZ]
def set_move(axis): 
    pos = float(Moves[axis-1].get())
    ANC.ramp(axis, pos)
    dynamiclabels[axis-1].set(f"{ANC.get_output(axis)} V")
    
Steps = [StepX, StepY, StepZ]
def set_step(axis, direction):
    step = abs(float(Steps[axis-1].get()))*direction
    ANC.step(axis, step)
    dynamiclabels[axis-1].set(f"{ANC.get_output(axis)} V")
    
#Buttons to set movements
Button_MoveX = ttk.Button(master=frame, text="\u2713", style="Std.TButton", command= lambda:set_move(1))
Button_MoveY = ttk.Button(master=frame, text="\u2713", style="Std.TButton", command= lambda:set_move(2))
Button_MoveZ = ttk.Button(master=frame, text="\u2713", style="Std.TButton", command= lambda:set_move(3))
X_smaller = ttk.Button(master=frame, text="\u2BC7", style="Std.TButton", command= lambda:set_step(1,-1))
X_larger = ttk.Button(master=frame, text="\u2BC8", style="Std.TButton", command= lambda:set_step(1,1))
Y_smaller = ttk.Button(master=frame, text="\u2BC7", style="Std.TButton", command= lambda:set_step(2,-1))
Y_larger = ttk.Button(master=frame, text="\u2BC8", style="Std.TButton", command=lambda:set_step(2,1))
Z_smaller = ttk.Button(master=frame, text="\u2BC7", style="Std.TButton", command=lambda:set_step(3,-1))
Z_larger = ttk.Button(master=frame, text="\u2BC8", style="Std.TButton", command=lambda:set_step(3,1))
Button_MoveX.grid(column=3,row=1)
Button_MoveY.grid(column=3,row=2)
Button_MoveZ.grid(column=3,row=3)
X_smaller.grid(column=5, row=1)
X_larger.grid(column=6, row=1)
Y_smaller.grid(column=5, row=2)
Y_larger.grid(column=6, row=2)
Z_smaller.grid(column=5, row=3)
Z_larger.grid(column=6, row=3)

main.mainloop()