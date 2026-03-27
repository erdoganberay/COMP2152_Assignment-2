"""
Author: Beray Erdogan
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import socket
import threading
import sqlite3
import os
import platform
import sys
import datetime

# Print Python version and OS name (Step iii)
print("System Information")
print(f"Operating System: {os.name}")
print(f"Python Info: {sys.version}")
print()

# Create the common_ports dictionary (Step iv)
# Maps common network port numbers to their protocol names
common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}



#Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"

class NetworkTool:
    def __init__(self,target: str):
        if not isinstance(target, str):
            raise TypeError("Target must be string type.") 
        self.__target = target


# Q3: What is the benefit of using @property and @target.setter?
# Answer: @property and @target.setter gives simple direct access to private 
# datawithout compromising security
    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Target must be string type.")
        if not value:
            raise ValueError("Target cannot be empty")
        self.__target = value

    def __del__(self):
        print('NetworkTool instance destroyed')



# Create the PortScanner child class that inherits from NetworkTool (Step vi)
# Q1: How does PortScanner reuse code from NetworkTool?
# Answer: By inheritng methods from NetworkTool. 
class PortScanner(NetworkTool):
    def __init__(self,target: str):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()


# - scan_port(self, port):
#     - try-except with socket operations
#     - Create socket, set timeout, connect_ex
#     - Determine Open/Closed status
#     - Look up service name from common_ports (use "Unknown" if not found)
#     - Acquire lock, append (port, status, service_name) tuple, release lock
#     - Close socket in finally block
#     - Catch socket.error, print error message

    def scan_port(self, port: int):
#     Q4: What would happen without try-except here?
#     Answer: Any error in proccess would crash the entire program.
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))
            port_status = "Open" if result == 0 else "Closed"
            protocol_name = common_ports.get(port,"Unknown")

            with self.lock:
                 self.scan_results.append((port, port_status, protocol_name))


        except socket.error as error:
            print(f"Error scanning port {port}: {error}")
        finally:
            sock.close()


# - get_open_ports(self):
#     - Use list comprehension to return only "Open" results

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"] 
        

# - scan_range(self, start_port, end_port):
#     - Create threads list
#     - Create Thread for each port targeting scan_port
#     - Start all threads (one loop)
#     - Join all threads (separate loop)

#     Q2: Why do we use threading instead of scanning one port at a time?
#     Answer: Threading makes scanning faster since ports are scanned in 
#     parallel, eliminating the need to wait for each port one by one.
    def scan_range(self, start_port: int, end_port: int):
        threads = []
        for port in range(start_port, end_port+1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)
        
        for t in threads: t.start()
        for t in threads: t.join() 



# Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error
    
    def save_results(self,target, results):
        time = str(datetime.datetime.now())
        try:
            conn = sqlite3.connect("scan_history.db")
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS scans (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           target TEXT,
                           port INTEGER,
                           status TEXT,
                           service TEXT,
                           scan_date TEXT)""")

            for result in results:
                cursor.execute("""INSERT INTO scans 
                              (target, port, status, service, scan_date)
                               VALUES (?, ?, ?, ?, ?)""", 
                              (target, result[0], result[1], result[2], time))
            conn.commit()
            conn.close()

        except sqlite3.Error as e:
             print(f"DB error: {e}")   



# Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection
    def load_past_scans(self):
        try:
                conn = sqlite3.connect("scan_history.db")
                cursor = conn.cursor()
                result = cursor.execute("SELECT * FROM scans")
                past_scans = result.fetchall()
                for _, target, port, status, service, scan_date in past_scans:
                    print(f"[{scan_date}]/{target} : Port {port} ({service}) - {status}")
        except sqlite3.Error:
            print("No scans found.")

# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    # Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."
    while True:
        try:
            target = input("Target IP: ").strip() or "127.0.0.1"
            break
        except ValueError:
            print("Invalid input!")

    while True:
        try:
            start = int(input("Start Port: "))
            if 1 <= start <= 1024:
                break
            else:
                print("Port must be between 1 and 1024.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    while True:
        try:
            end = int(input("End Port: "))
            if 1 <= end <= 1024 and end >= start:
                break
            else:
                print("Port must be between 1 and 1024 and >= start.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")   

# After valid input (Step x)
    # - Create PortScanner object
    # - Print "Scanning {target} from port {start} to {end}..."
    # - Call scan_range()
    # - Call get_open_ports() and print results
    # - Print total open ports found
    # - Call save_results()
    # - Ask "Would you like to see past scan history? (yes/no): "
    # - If "yes", call load_past_scans()

    sc = PortScanner(target)
    print(f"Scanning {target} from port {start} to {end}...")
    sc.scan_range(start,end)

    open_ports = sc.get_open_ports()
    print(f"\n--- Scan Results for IP: {target} ---")
    for port, status, service in open_ports:
        print(f"Port {port} ==> {status} ({service})")
    print("------------------------------------")
    print(f"Total open ports found: {len(open_ports)}")
    sc.save_results(target, sc.scan_results)

    history = input("Would you like to see past scan history? (y/n): ").strip()
    if history == "y":
        sc.load_past_scans()
    else:
        exit


    
# Q5: New Feature Proposal
# get_closed_ports()
# Gives a list of closed ports in range using list comprehension
# Diagram: See diagram_studentID.png in the repository root
