from engine import model
from modules import pymsf

name = "post_linux_rootacc"
os = "linux"
flavor = "any"
mod_type = "post"
mod_lang = "bash"
destructive = "False"
scannable = "False"
difficulty = "1"
priv_required = "root"


def create():
    module = model.Module(name, os, flavor, mod_type, mod_lang, destructive, scannable, difficulty, priv_required)

def handle(system, session):

    success = False
    newvuln = False

    return (success, newvuln)
