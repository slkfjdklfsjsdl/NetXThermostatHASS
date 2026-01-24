## API Docs

This is a basic python script that can authenticate with the Official TCP API endpoint and read the state of the thermostat
```import socket
import hashlib
import base64

# Your credentials - UPDATE THESE
HOST = "192.168.1.2"
PORT = 10001
USERNAME = "your_username"
PASSWORD = "your_password"

# Generate auth hash (SHA256 of username:password, then base64)
auth_string = f"{USERNAME}:{PASSWORD}"
sha256_hash = hashlib.sha256(auth_string.encode()).digest()
base64_hash = base64.b64encode(sha256_hash).decode()

# Build login command
login_cmd = f"WMLS1D{USERNAME},{base64_hash}\r\n"

print(f"Login command: {login_cmd}")

# Connect and test
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(10)
sock.connect((HOST, PORT))

# Send login
sock.send(login_cmd.encode())
response = sock.recv(1024).decode()
print(f"Login response: {response}")

# If login succeeded, try reading state
if "OK" in response:
    # Get temperature scale
    sock.send(b"RTS1\r\n")
    response = sock.recv(1024).decode()
    print(f"RTS1 (temp scale): {response}")
sock.close()
print("Done!")
```
## Output example:
```
Login command: WMLS1Dthermostat,bF+eVjgq6HW+h/m7pOOunks2+8GtNDbxeyVpTNek0N8=

Login response: OK,USER,NO

RTS1 (temp scale): RTS1:CELSIUS

RAS1 (all states): RAS1:25,NA,HEAT,FAN AUTO,NO,NO,25,20,HEAT,1,NONE

RRHS1 (humidity): RRHS1:0

RNS1 (operation mode): RNS1:ON
```
Using this and reverse engineering the Control4 and RTI integrations we can find most of the control and status endpoints.
