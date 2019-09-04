#!/usr/bin/python3
from hashlib import sha256
import collections
import sys
import yaml
import json
import db

def load_config(filename):
    print("Loading config...")
    with open(filename, 'r') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    settings = config['settings']
    print("Hashing password...")
    settings['password'] = sha256(settings['password'].encode('utf-8')).hexdigest()
    
    teams = config['teams']
    systems = config['systems']

    print("Emptying existing database...")
    db.reset_all_tables()
    print("Writing global settings to database...")
    db.write_settings(settings)
    print("Writing teams to database...")
    db.write_teams(teams)
    print("Writing systems to database...")
    db.write_systems(systems, teams)
    return

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./load_config CONFIG_FILE")
    else:
        load_config(sys.argv[1])
