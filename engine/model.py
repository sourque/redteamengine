import logging, datetime, random, copy, json, ast, subprocess, yaml
import collections, sys, json
from threading import Thread, Timer
from hashlib import sha256
from enum import IntEnum
from time import sleep
from engine import db
import modules

class MetaModel(object):
    """
    Data for all components of this project.

    """

    def __init__(self):

        print("Loading config...")
        with open('config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)

        self.settings = config['settings']
        print("Hashing password...")
        self.settings['password'] = sha256(
            self.settings['password'].encode('utf-8')).hexdigest()

        self.config_teams = config['teams']
        self.config_systems = config['systems']

        print("Emptying existing database...")
        db.reset_all_tables()

        logging.info(
            "------------------------ APP LAUNCHED ------------------------")
        logging.info("Loading data into the in-memory model.")

        # Initialize modules into the database
        for module in modules.module_info.list_modules():
            getattr(modules, module).create()

        # Set MSFRPC current setting to off
        self.msfrpc_loaded = 0
        self.autostart = 0

        # todo run through jobs
        self.jobs = []

        # Load global settings
        self.run = 0
        self.dest = 0
        self.thread_lock = 0
        self.msf_pw = "9wFZ8T7KWyydh2z4"

        # Load teams and systems
        self.teams = []
        sorted_teams = sorted(self.config_teams.items(), key=lambda kv: kv[0])
        for team in sorted_teams:
            team_info = (team[1]['team_name'], team[1]['prefix'],
                         team[1]['difficulty'])
            self.write_team(team_info)


    def write_team(self, team_info):
        team = Team("new", *team_info)
        self.teams.append(team)
        sorted_systems = sorted(self.config_systems.items(), key=lambda kv: kv[0])
        sys_num = 1
        for system in sorted_systems:
            sys_vulns = []
            for vuln in system[1]['vulns'].items():
                sys_vulns.append((vuln[1]['name'], vuln[1]['info']))
            system_info = (sys_num, "Inactive", system[1]['name'], team.id,
                           team.ip + str(system[1]['ip']),
                           system[1]['os'], system[1]['flavor'], sys_vulns)
            new_system = System("new", *system_info)
            team.systems.append(new_system)
            sys_num += 1

    def create_msf(self):
        # FOR PROXY whatever, create msf objects
        # mm.msfs = []
        self.msf = modules.pymsf.Msfrpc(self)
        if not self.msf.start(self.msf_pw):
            logging.warning("Unable to initialize MSF connection.")
            exit()
        if not self.msf.generate_token():
            logging.warning("Failed to generate permanent token.")
            exit()

class Team(object):
    def __init__(self, team_id, team_name, team_ip, team_difficulty):
        self.name = team_name
        self.ip = team_ip
        self.difficulty = int(team_difficulty)
        self.root_shells = 0
        self.user_shells = 0
        self.unpriv_shells = 0
        self.systems = []
        if not team_id == "new":
            self.id = int(team_id)
        else:
            db.insert('teams', ['name', 'ip', 'difficulty'],
                      (self.name, self.ip, self.difficulty))
            self.id = db.get(
                'teams', ['id'],
                where="name=%s and ip=%s",
                args=(self.name, self.ip))[0][0]

    def __str__(self):
        return ("Team %d: %s at %s.X", self.id, self.name, self.ip)

    def save(self):
        db.modify(
            'teams',
            set='name=%s, ip=%s, difficulty=%s',
            where='id=%s',
            args=(self.name, self.ip, str(self.difficulty), str(self.id)))


class System(object):
    def __init__(self,
                 sys_id,
                 sys_num,
                 sys_status,
                 sys_name,
                 sys_team_id,
                 sys_ip,
                 sys_os,
                 sys_flavor,
                 sys_vulns=()):
        self.num = int(sys_num)
        self.status = sys_status
        self.name = sys_name
        self.team_id = int(sys_team_id)
        self.ip = sys_ip
        self.last_octet = self.ip.split('.')[3]
        self.os = sys_os
        self.flavor = sys_flavor
        self.root_shells = 0
        self.user_shells = 0
        self.unpriv_shells = 0
        self.access = 0
        self.vulns = []
        if not sys_id == "new":
            self.id = int(sys_id)
        else:
            db.insert('systems',
                   ['num', 'status', 'name', 'team_id', 'ip', 'os', 'flavor'],
                   (sys_num, self.status, self.name, self.team_id,
                    str(self.ip), self.os, self.flavor))
            self.id = db.get(
                'systems', ['id'],
                where="num=%s and team_id=%s",
                args=(self.num, self.team_id))[0][0]
                # [0][0]
        for vuln in sys_vulns:
            self.vulns.append(Vuln("new", self.id, vuln[0], vuln[1]))

    def __str__(self):
        return ("system " + self.name + " (team " + str(self.team_id) + ") (" +
                self.ip + ")")

    def save(self):
        db.modify(
            'systems',
            set=
            'num=%s, status=%s, name=%s, team_id=%s, ip=%s, os=%s, flavor=%s',
            where='id=%s',
            args=(self.num, self.status, self.name, self.team_id, self.ip,
                  self.os, self.flavor, self.id))

    def save_status(self):
        db.modify(
            'systems',
            set='status=%s',
            where='id=%s',
            args=(self.status, self.id))


class Module(object):
    def __init__(self, mod_name, mod_os, mod_flavor, mod_type, mod_lang,
                 mod_destructive, mod_scannable, mod_difficulty,
                 mod_priv_required):
        db.insert('modules', [
            'name', 'os', 'flavor', 'mod_type', 'mod_lang', 'destructive',
            'scannable', 'difficulty', 'priv_required'
        ], (mod_name, mod_os, mod_flavor, mod_type, mod_lang, mod_destructive,
            mod_scannable, mod_difficulty, mod_priv_required))


class Vuln(object):
    def __init__(self, v_id, v_sys_id, mod_name, mod_info, access=""):
        self.system_id = int(v_sys_id)
        self.mod_name = mod_name
        self.mod_info = ast.literal_eval(mod_info)
        self.access = access
        if not v_id == "new":
            self.id = int(v_id)
        else:
            store_mod_info = '\"' + str(self.mod_info) + '\"'
            db.insert('vulns', ['system_id', 'mod_name', 'mod_info'], \
                (self.system_id, self.mod_name, store_mod_info))
            self.id = db.get(
                'vulns', ['id'],
                where="system_id=%s and mod_name=%s and mod_info=%s",
                args=(self.system_id, self.mod_name, store_mod_info))[0][0]

    def __str__(self):
        return ("Vuln " + str(self.id) + " " + self.mod_name +
                " for system id " + str(self.system_id))

    def save(self):
        store_mod_info = '\"' + str(self.mod_info) + '\"'
        db.modify('vulns', set='system_id=%s, mod_name=%s, mod_info=%s', where='id=%s', \
            args=(self.system_id, self.mod_name, store_mod_info, self.id))


class Access(object):
    """
    Current access information for a system.

    """

    def __init__(self, system_id, vuln_id, session, tries, level):
        self.system_id = int(system_id)
        self.vuln_id = int(vuln_id)
        self.session = session
        self.tries = int(tries)
        self.level = level

    def __str__(self):
        return ("Current access " + str(self.id) + " for vuln " + str(
            self.vuln_id))


class Session(object):
    """
    Session information.

    """

    def __init__(self, session_data, msf):
        self.id = int(session_data[0])
        self.shell_type = session_data[1][b'type']
        self.msf = msf

    def __str__(self):
        return ("Current session " + str(self.id))

    def close(self):
        # todo
        pass
