from engine import model
from modules import pymsf

name = "annoy_linux_notify"
os = "linux"
flavor = "any"
mod_type = "annoy"
mod_lang = "bash"
destructive = "False"
scannable = "False"
difficulty = "1"
priv_required = "user"


def create():
    module = model.Module(name, os, flavor, mod_type, mod_lang, destructive,
                          scannable, difficulty, priv_required)

def handle(system, session):

    success = False

    for x in range(0, 5):
        # if sessio.type = meterpreter then:
            # data = meterpreter_Exec
        # else: or smth
        data = session.msf.shell_input(session.id, "notify-send -u critical -t 1000 'HEY' 'YOU GOT HACKED LOL'")
        if data:
            success = True

    return (success)
