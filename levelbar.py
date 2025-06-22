class LevelBar:

    def __init__(self,canvas,server_data):
        self.canvas = canvas
        self.level = float(server_data['level'])
        self.displayLevel = str(round(float(server_data['level']),2)) + " feet"
        self.low = float(server_data['low'])
        self.high = float(server_data['high'])
        self.maximum = float(server_data['max'])
        self.minimum = float(server_data['min'])
        self.name = server_data['name']


        height = int( (400 / self.maximum ) * self.level ) 
        top = 450 - height

        highpx = 450 - int( (400 / self.maximum ) * self.high )
        lowpx = 450 - int( (400 / self.maximum ) * self.low )

        #print(f"height:{height}")
        
        self.canvas.create_text(60, 20, fill='black', font='Arial 20 bold', text=self.name)
        
        self.empty = self.canvas.create_rectangle(50, 50, 70, 450, fill="#999999")
        self.fill = self.canvas.create_rectangle(50, top, 70, 450, fill="#a2eaf5")  # Rectangle
        self.fill_text = canvas.create_text(50, 465, fill='black', font='Arial', text=self.displayLevel)
        if(server_data['filling'] == 1):
            self.pumping_text = self.canvas.create_text(60, 485, fill='green', font='Arial', text="Filling")
        else:
            self.pumping_text = self.canvas.create_text(60, 485, fill='red', font='Arial', text=" ")
        
        self.topline = self.canvas.create_line(45, highpx, 75, highpx, fill="red", width=3)
        self.toptext = self.canvas.create_text(95, highpx, fill='black', font='Times 12 italic bold', text=self.high)
                
        self.lowline = self.canvas.create_line(45, lowpx, 75, lowpx, fill="red", width=3)
        self.lowtext = self.canvas.create_text(95, lowpx, fill='black', font='Times 12 italic bold', text=self.low)
        
    def update_levels(self,canvas,server_data):
        self.canvas.delete(self.topline)
        self.canvas.delete(self.toptext)
        self.canvas.delete(self.lowline)
        self.canvas.delete(self.lowtext)
        
        self.level = float(server_data['level'])
        self.displayLevel = str(round(float(server_data['level']),2)) + " feet"
        self.low = float(server_data['low'])
        self.high = float(server_data['high'])
        self.maximum = float(server_data['max'])
        self.minimum = float(server_data['min'])

        highpx = 450 - int( (400 / self.maximum ) * self.high )
        lowpx = 450 - int( (400 / self.maximum ) * self.low )

        self.canvas.delete(self.pumping_text)
        if(server_data['filling'] == 1):
            self.pumping_text = self.canvas.create_text(60, 485, fill='green', font='Arial', text="Filling")
        else:
            self.pumping_text = self.canvas.create_text(60, 485, fill='red', font='Arial', text=" ")

            
        self.topline = self.canvas.create_line(45, highpx, 75, highpx, fill="red", width=3)
        self.lowtext = self.canvas.create_text(95, highpx, fill='black', font='Times 12 italic bold', text=self.high)
                
        self.lowline = self.canvas.create_line(45, lowpx, 75, lowpx, fill="red", width=3)
        self.lowtext = self.canvas.create_text(95, lowpx, fill='black', font='Times 12 italic bold', text=self.low)
        
        height = int( (400 / self.maximum ) * self.level ) 
        top = 450 - height
    
        self.canvas.coords(self.empty, 50, 50, 70, 450)
        self.canvas.coords(self.fill, 50, top, 70, 450)
        self.canvas.itemconfig(self.fill_text,text=self.displayLevel)

