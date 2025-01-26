import time
import serial  # PySerial for USB communication

class FileHandler: #handles file operations for logging data
    def __init__(self): #CONSTRUCTOR, initializes class, we setting thngs up
        self.file = None #not assigned for now so it can be whatever we specify later
        self.filename = None

    def new_file(self): #create new file to record data
        if self.file:
            self.file.close() #close previously oven file, if any, so we dont overwrite/contaminate data/vause error
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime()) 
        self.filename = f"{timestamp}.csv" #generate a timestamp-based filename
        self.file = open(self.filename, 'w') #open new file, w/o 'w' file wouldnt be writeable 
        self.file.write("recording_start_time, current_phase, value\n") #defining header for csv row
        self.file.close()  # Close after initializing to ensure data is saved (save header)
        #always, do a thing ->close, open->do a thing-> close, NEVER LEAVE IT OPEN
        print(f"Started new file: {self.filename}")

    def write_buffer(self, buffer): #buffer storage for efficiency in processing
        with open(self.filename, 'a') as self.file: #open and add new data without erasing old ones
            for data_point in buffer:
                self.file.write(data_point + "\n") #\n= each data written in new line, acts like wordwrap
            self.file.flush() #flush to save data immediately

    def close_file(self): #so file isnt open even when we done using it
        if self.file:
            self.file.close() #CLOSE PROPERLY OR DATA WILL BE LOST/ FILE WILL BE LOCKED AAAAAA
            print(f"Closed file: {self.filename}")
            self.file = None #reset file thiingies so no file is open


def main(): #main data handling, serial port configuration
    port = 'COM5'  #top, left port
    try:
        ser = serial.Serial(port, 9600, timeout=1) #baud- usb port speed= 9600 bits/s
    except serial.SerialException:
        print("Failed to open serial port") #error message for port not working
        return #stop running program if cant connect w/ port

    file_handler = FileHandler() #manages data file
    buffer = [] #temporary list, saves data, like a container holding all that we record until we move it away
    buffer_size = 10 #file save only after collecting 10 datapoints

    file_handler.new_file() #to store data
    print(f"New file created for data logging.")

    try:
        while True: # Read data from USB in continuous loop
            if ser.in_waiting > 0: #check if anythings new to read
                line = ser.readline().decode("utf-8").strip() #convert from beepboop binary to readable text, remove unnecessary space
                print(f" Received: {line}") #to confirm we received it in the file
                buffer.append(line) #new data for temporary buffer

                if len(buffer) >= buffer_size: # Write to file when buffer is full
                    file_handler.write_buffer(buffer) #data from buffer to file 
                    buffer.clear()#empty, collect more
    except KeyboardInterrupt: # # If the user presses Ctrl+C, stop the program gracefully. giving people a way out
        print("Interrupted by user. Closing...") 
    finally: #check EVERYTHING is closed
        file_handler.close_file() # so things are closed properly
        print(f"File closed.")
        ser.close() #end usb connection
        print("Serial port closed.")

if __name__ == "__main__": #program starts when this script runs
    main()
