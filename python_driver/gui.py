from tkinter import *
from tkinter import ttk

from driver import ControllerE220
from e220_config import AirSpeed, MessageRSSI, TxPower, UARTSpeed
from PIL import Image, ImageTk
from serial.tools import list_ports

controller = ControllerE220()

def load_com_ports(com_combo):
    ports = list_ports.comports()
    com_names = [p.device for p in ports]
    com_combo['values'] = com_names
    if len(com_names):
        com_combo.set(com_names[0])
        com_descrip.set(ports[0].description)
        cnt_button['state'] = NORMAL
    else:
        com_combo.set('')
        com_descrip.set('')
        cnt_button['state'] = DISABLED

    return ports

def connect(ports, index):
    if cnt_button['text'] == 'Connect':
        if index < 0:
            print('No port detected!')
            return
        controller.connect(ports[index].device, int(baud_rate.get()))
        cnt_button['text'] = 'Disconnect'

    elif cnt_button['text'] == 'Disconnect':
        controller.disconnect()
        cnt_button['text'] = 'Connect'

def load_icon(icon_size):
    im = Image.open("arrow.png")
    im = im.resize(icon_size, Image.ANTIALIAS)
    img = ImageTk.PhotoImage(im)
    return img

root = Tk()
root.title("E220 LoRa GUI")
root.geometry('500x250')

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

com_descrip = StringVar()
ttk.Label(mainframe, textvariable=com_descrip).grid(column=0, row=1, columnspan=6)
com_port_combo = ttk.Combobox(mainframe, width=13)
com_port_combo.grid(column=0, row=0)
com_port_combo.bind("<<ComboboxSelected>>", lambda _: com_descrip.set(ports[com_port_combo.current()].description))
baud_rate = ttk.Combobox(mainframe, width=13)
baud_rate['values'] = [9600, 19200, 38400, 57600, 115200]
baud_rate.set(115200)
baud_rate.grid(column=1, row=0)
ttk.Button(mainframe, text="Reload", command=lambda: load_com_ports(com_port_combo)).grid(column=2, row=0)
cnt_button = ttk.Button(mainframe, text="Connect", command=lambda: connect(ports, com_port_combo.current()))
cnt_button.grid(column=3, row=0)
ports = load_com_ports(com_port_combo)

combo_width = 23
power_combo = ttk.Combobox(mainframe, width=combo_width)
power_combo['values'] = [e.name for e in TxPower]
power_combo.grid(column=0, row=2)
ttk.Button(mainframe, text="Set power", command=lambda: controller.set_tx_power(TxPower[power_combo.get()])).grid(column=1, row=2)

air_speed_combo = ttk.Combobox(mainframe, width=combo_width)
air_speed_combo['values'] = [e.name for e in AirSpeed]
air_speed_combo.grid(column=0, row=3)
ttk.Button(mainframe, text="Set air speed", command=lambda: controller.set_air_speed(AirSpeed[air_speed_combo.get()])).grid(column=1, row=3)

uart_speed_combo = ttk.Combobox(mainframe, width=combo_width)
uart_speed_combo['values'] = [e.name for e in UARTSpeed]
uart_speed_combo.grid(column=0, row=4)
ttk.Button(mainframe, text="Set UART speed", command=lambda: controller.set_uart_speed(UARTSpeed[uart_speed_combo.get()])).grid(column=1, row=4)

def cmd_set_config():
    controller.set_tx_power(TxPower[power_combo.get()])
    controller.set_air_speed(AirSpeed[air_speed_combo.get()])
    controller.set_uart_speed(UARTSpeed[uart_speed_combo.get()])

def cmd_get_config():
    config = controller.get_config()
    if config is not None:
        power_combo.set(TxPower(config.tx_power).name)
        air_speed_combo.set(AirSpeed(config.air_speed).name)
        uart_speed_combo.set(UARTSpeed(config.uart_speed).name)

ttk.Button(mainframe, text="Set config", command=cmd_set_config).grid(column=1, row=5)
ttk.Button(mainframe, text="Get config", command=cmd_get_config).grid(column=2, row=5)

msg_frame = ttk.Frame(mainframe, height=20, relief=GROOVE)
msg_frame.grid(column=0, row=6, columnspan=6)
rssi_var = StringVar(value='---')
seq_num_var = StringVar(value='---')
ttk.Label(msg_frame, text="RSSI:").pack(side=LEFT)
ttk.Label(msg_frame, textvariable=rssi_var).pack(side=LEFT)
ttk.Label(msg_frame, text="Seq num:").pack(side=LEFT)
ttk.Label(msg_frame, textvariable=seq_num_var).pack(side=LEFT)
# update rssi_var in a thread using controller.get_data()
def update_rssi():
    packet = controller.get_data(MessageRSSI, timeout=0)
    if packet is not None:
        rssi_var.set(packet.rssi)
        seq_num_var.set(packet.msg.seq_num)
    root.after(100, update_rssi)

update_rssi()

# icon_size = (15, 15)
# icon = load_icon(icon_size)

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)


def on_close():
    if controller.connected:
        controller.disconnect()
    exit()

# feet_entry.focus()
# root.bind("<Return>", calculate)

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()