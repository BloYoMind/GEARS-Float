import socket
import time
import threading
import random

debugMode = True  # Always use debug mode for testing

# Global HTML content
html = "<html><body><h1>Waiting for data...</h1></body></html>"

# Webserver function
def webserver():
    global html
    addr = ('127.0.0.1', 8080)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)

    print(f'Listening on {addr}.')
    try:
        while True:
            cl, addr = s.accept()
            print(f'Client connected from {addr}.')
            cl.recv(1024)  # Simulate request read
            cl.sendall(b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n' + html.encode())
            cl.close()
    except OSError as e:
        print(e)

# Simulated SquidControl class
class SquidControl:
    def __init__(self):
        print("Initialized SquidControl simulation")

    def getPressure(self):
        return round(random.uniform(100.000, 130.000), 2)

    def record(self):
        global html
        while True:
            print(f'Updating pressure data...')
            new_html = "<html><body><h1>Pressure Data</h1><table border='1'><tr><th>Time</th><th>Pressure</th></tr>"
            for _ in range(8):
                timestamp = round(time.time(), 2)
                pressure = self.getPressure()
                new_html += f"<tr><td>{timestamp}</td><td>{pressure}</td></tr>"
                print(f'Data packet: {timestamp}, {pressure}')
                time.sleep(1)  # Simulate data collection delay
            new_html += "</table></body></html>"
            html = new_html  # Update web page content

# Main function
def main():
    squid = SquidControl()
    
    # Start webserver in a separate thread
    threading.Thread(target=webserver, daemon=True).start()

    # Continuously update pressure data
    squid.record()

if __name__ == "__main__":
    main()
