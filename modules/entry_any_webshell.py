from engine import model

name = "entry_any_webshell"
os = "any"
flavor = "any"
mod_type = "entry"
mod_lang = "bash"
destructive = "False"
scannable = "False"
difficulty = "2"
priv_required = "none"


def create():
    module = model.Module(name, os, flavor, mod_type, mod_lang, destructive,
                          scannable, difficulty, priv_required)


def handle(system, vuln, msf):

    session = False
    access = ""

    return (session, access)
