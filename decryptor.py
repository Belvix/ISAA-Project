import os
import tkinter as tk
import math
from tkinter import filedialog
import zipfile
from PIL import ImageTk, Image, ImageDraw
from Crypto.Protocol.KDF import scrypt
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class ImageViewerApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Image Viewer, Canvas, and Encryption")

        self.file_path = ""
        self.original_image = None
        self.original_image_copy = None
        self.canvas_image = Image.new("RGB",(200,300))
        self.drawing = False
        self.last_x = 0
        self.last_y = 0
        self.last_last_x = 0
        self.last_last_y = 0
        self.line_count = 0
        self.lines = []
        self.angles = []

        self.create_ui()

    def create_ui(self):
        left_frame = tk.Frame(self.window)
        left_frame.pack(side="left", padx=10, pady=10)

        open_button = tk.Button(left_frame, text="Open Image", command=self.open_image)
        open_button.pack()

        self.file_label = tk.Label(left_frame)
        self.file_label.pack()

        middle_frame = tk.Frame(self.window)
        middle_frame.pack(side="left", padx=10, pady=10)

        self.canvas = tk.Canvas(middle_frame, width=300, height=300, bg="white")
        self.canvas.pack()

        decrypt_button = tk.Button(middle_frame, text="Decrypt", command=self.decrypt_image)
        decrypt_button.pack()

        clear_button = tk.Button(middle_frame, text="Clear Canvas", command=self.clear_canvas)
        clear_button.pack()

        self.angle_label = tk.Label(middle_frame, text="Angle: ")
        self.angle_label.pack()

        right_frame = tk.Frame(self.window)
        right_frame.pack(side="left", padx=10, pady=10)

        self.new_image_label = tk.Label(right_frame)
        self.new_image_label.pack()

        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.preview)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)

    def preview(self, event):
        if self.drawing:
            self.canvas.delete("preview_line")
            x = event.x
            y = event.y
            dx1 = self.last_last_x - self.last_x
            dy1 = self.last_last_y - self.last_y
            dx2 = event.x - self.last_x
            dy2 = event.y - self.last_y
            angle1 = math.atan2(dy1, dx1)
            angle2 = math.atan2(dy2, dx2)
            angle = math.degrees(angle2 - angle1)
            if self.line_count > 0:
                rounded_angle = math.ceil(angle / 5.0) * 5.0
                self.angle_label.config(text="Angle: {:.2f}".format(rounded_angle))
            self.canvas.create_line(self.last_x, self.last_y, x, y, fill="black", width=2, tags="preview_line")

    def open_image(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Encrypted files", "*.enc *.zip *.encrypted")])
        if self.file_path:
            self.file_label.config(text=self.file_path.split('/')[-1])

    def start_drawing(self, event):
        if self.line_count == 0:
            self.last_x = event.x
            self.last_y = event.y
        if event.num == 1:
            self.drawing = True

    def stop_drawing(self, event):
        if self.drawing and event.num == 1:
            self.drawing = False
            self.canvas.delete("preview_line")
            self.line_count += 1
            self.draw(event)

    def draw(self, event):
        x = event.x
        y = event.y
        self.canvas.create_line(self.last_x, self.last_y, x, y, fill="black", width=2)
        draw = ImageDraw.Draw(self.canvas_image)
        dx1 = self.last_last_x - self.last_x
        dy1 = self.last_last_y - self.last_y
        dx2 = event.x - self.last_x
        dy2 = event.y - self.last_y
        angle1 = math.atan2(dy1, dx1)
        angle2 = math.atan2(dy2, dx2)
        angle = math.degrees(angle2 - angle1)
        if self.line_count > 1:
            rounded_angle = math.ceil(angle / 5.0) * 5.0
            self.angles.append(rounded_angle)
        draw.line([(self.last_x, self.last_y), (x, y)], fill="black", width=2)
        self.lines.append(((self.last_x, self.last_y), (x, y)))
        self.last_last_x = self.last_x
        self.last_last_y = self.last_y
        self.last_x = event.x
        self.last_y = event.y

    def decrypt_image(self):
        if self.file_path:
            s=""
            for angle in self.angles:
                s+=str(angle)
            print(s)
            password = bytes(s,'utf-8')
            salt = b'salt'
            key = scrypt(password, salt, 32, N=2 ** 14, r=8, p=1)
            cipher = AES.new(key, AES.MODE_CBC)
            data = 0
            print(self.file_path.split('/')[-1])
            with zipfile.ZipFile(self.file_path.split('/')[-1],'r') as zip:
                zip.extractall()
            with open("encrypted_image.enc","rb") as fobj:
                data = fobj.read()
            decrypted_data = cipher.decrypt(data)
            decrypted_data = unpad(decrypted_data,AES.block_size)
            size = ()
            with open("data.txt","r") as fobj:
                size = tuple(map(int,fobj.read().split(",")))
            img = Image.frombytes("RGB",size,decrypted_data)
            os.remove("encrypted_image.enc")
            os.remove("data.txt")
            img.save("decrypted.png")
            

    def clear_canvas(self):
        self.canvas.delete("all")
        self.angle_label.config(text="Angle: ")
        self.line_count = 0
        self.lines = []
        self.angles = []

if __name__ == "__main__":
    window = tk.Tk()
    app = ImageViewerApp(window)
    window.mainloop()
