from time import sleep
from engine import db, model
from threading import Thread, local
from random import randint
import logging, random, threading, sys, os
import time, datetime, random, subprocess, timeout_decorator
import modules


class PentestingCycle():
    def start(self, mm):
        mm.cycles = 0
        self.launch_msfrpc(mm)
        while True:
            if mm.run:
                mm.cycles += 1
                logging.info("Beginning cycle #" + str(mm.cycles) + ".")
                for team in mm.teams:
                    for system in team.systems:  # For each system, spawn a master thread
                        if system.status == "Inactive":
                            runner = Thread(target=self.master,
                                            args=(mm, team, system))
                            runner.name = "Team" + str(team.id) + "Sys" + str(
                                system.num)
                            runner.start()
                        else:
                            logging.warning("Not running " + str(system) +
                                            " due to being active.")

                self.housekeeping(mm)
            else:
                logging.info("Not running pentesting cycle.")

            logging.info("Sleeping for 20 seconds.")
            time.sleep(20)

    def master(self, mm, team, system):
        logging.info("Thread spawned for " + str(system))
        try:
            system.status = "Entering"
            # TODO msf = mm.getmsf() random proxy
            self.entry(team, system, mm.msf)
        except SystemError:
            logging.warning("Entry timed out for " + str(system))

        try:
            system.status = "Persisting"
            self.persist(team, system)
        except SystemError:
            logging.warning("Persisting timed out for " + str(system))

        try:
            system.status = "Annoying"
            self.annoy(mm, team, system)
        except SystemError:
            logging.warning("Annoying timed out for " + str(system))
        try:
            system.status = "Scanning"
            self.scan(team, system)
        except SystemError:
            logging.warning("Scanning timed out for " + str(system))
        system.status = "Inactive"

    # timeout_decorator.timeout(40, use_signals=False, timeout_exception=SystemError)
    def entry(self, team, system, msf):

        required_roots = 1
        if team.difficulty > 4:
            requred_roots = team.difficulty - 4
        acquired_roots = loops = 0

        for vuln in system.vulns:
            if acquired_roots < required_roots:
                if not vuln.access:
                    session = False
                    session, access_level = getattr(modules,
                                                    vuln.mod_name).handle(
                                                        system, vuln, msf)
                    if session:
                        logging.info("Gained " + access_level + " on " +
                                     str(system) + " with " + vuln.mod_name)
                        vuln.access = model.Access(system.id, vuln.id, session,
                                                   3, access_level)
                        if access_level == 'root':
                            acquired_roots += 1
                            system.root_shells += 1
                            team.root_shells += 1
                        elif access_level == 'user':
                            system.user_shells += 1
                            team.user_shells += 1
                        else:
                            system.unpriv_shells += 1
                            team.unpriv_shells += 1
                    else:
                        logging.info("Exploit failed for " + vuln.mod_name +
                                     " on " + str(system))
            else:
                break

        random.shuffle(system.vulns)

    # timeout_decorator.timeout(40, use_signals=False, timeout_exception=SystemError)
    def persist(self, team, system):
        mod_required = team.difficulty + 3
        mod_ran = access = 0
        vuln, access, priv_string, priv_arr = self.pick_access(team, system)
        if access:
            system.access = 1
            mod_pool = db.get('modules', ['*'],
                              where=priv_string + '\
                os=%s or os=%s and flavor=%s or flavor=%s \
                and difficulty<=%s and mod_type=%s',
                              args=(*priv_arr, 'any', system.os, system.flavor,
                                    'any', str(team.difficulty), 'post'))
            mod_pool = list(mod_pool)
            while mod_required > mod_ran and mod_pool:
                mod = mod_pool.pop(random.randrange(len(mod_pool)))
                success, newvuln = getattr(modules, mod[1]).handle(
                    system, access.session)
                if success:
                    logging.info("Persistence/post succeeded for " +
                                 vuln.mod_name + " on " + str(system))
                    if newvuln:
                        system.vulns.append(Vuln("new", system.id, *vuln))
                else:
                    logging.info("Peristence/post failed for " +
                                 vuln.mod_name + " on " + str(system))
        else:
            system.access = 0

    # timeout_decorator.timeout(40, use_signals=False, timeout_exception=SystemError)
    def annoy(self, mm, team, system):
        mod_required = random.randint(0, team.difficulty)
        mod_ran = access = vulnobj = 0
        if mm.dest:
            destruction = 'True'
        else:
            destruction = 'False'
        vuln, access, priv_string, priv_arr = self.pick_access(team, system)
        if access:
            mod_pool = db.get('modules', ['*'],
                              where=priv_string + '\
                os=%s or os=%s and flavor=%s or flavor=%s \
                and difficulty<=%s and mod_type=%s and destructive=%s',
                              args=(*priv_arr, 'any', system.os, system.flavor,
                                    'any', str(team.difficulty), 'annoy',
                                    destruction))
            mod_pool = list(mod_pool)
            while mod_required > mod_ran and mod_pool:
                mod = mod_pool.pop(random.randrange(len(mod_pool)))
                success = getattr(modules,
                                  mod[1]).handle(system, access.session)
                if success:
                    logging.info("Annoying succeeded for " + vuln.mod_name +
                                 " on " + str(system))
                    access.tries = 3

                if not success:
                    logging.info("Annoying failed for " + vuln.mod_name +
                                 " on " + str(system) +
                                 ". Reducing tries or deleting.")
                    if access.tries > 0:
                        access.tries -= 1
                    else:
                        if vuln.access.level == 'root':
                            system.root_shells -= 1
                        elif vuln.access.level == 'user':
                            system.user_shells -= 1
                        else:
                            system.unpriv_shells -= 1
                        vuln.access = []


    # timeout_decorator.timeout(40, use_signals=False, timeout_exception=SystemError))
    def scan(self, team, system):

        # todo
        # if not system.scannable: pick all modules in db for this os that are scannable
        # assign to system object
        # pick random amount based on difficulty to scan
        # pop when scanning (scan only once)

        pass
        # todo

        # for vulns in vulns:
        # if module in db is scannable:

        # success, access = module.scan
        # any_scan = True

        # if any_scan:
        #logging.info("Scanning on " + str(system))

    def pick_access(self, team, system):
        vulnobj = access = priv_string = priv_arr = False
        for vuln in system.vulns:
            if vuln.access:
                if vuln.access.level == 'root':
                    vulnobj = vuln
                    access = vuln.access
                    priv_string = 'priv_required=%s and ' * 3
                    priv_arr = ['root', 'user', 'unpriv']
                    break
                elif vuln.access.level == 'user':
                    vulnobj = vuln
                    access = vuln.access
                    priv_string = 'priv_required=%s and ' * 2
                    priv_arr = ['user', 'unpriv']
                elif vuln.access:
                    if not access:
                        vulnobj = vuln
                        access = vuln.access
                        priv_string = 'priv_required=%s and '
                    priv_arr = ['unpriv']
        return vulnobj, access, priv_string, priv_arr

    def housekeeping(self, mm):
        for team in mm.teams:
            shells = team.root_shells + team.user_shells + team.unpriv_shells
            db.insert('access_log', ['cycle', 'team_id', 'shells'],
                      (str(mm.cycles), str(team.id), str(shells)))
        for job in mm.jobs:
            pass
            # todo check on passive modules to see if they got a callback -- if so, add to access

        # remove access modules (kill sessions) depending on difficulty (lower difficulty, fewer sessions)

        # check each msf session is working

    def launch_msfrpc(self, mm):
        print("Launching MSFRPC...")
        subprocess.call(["msfrpcd -S -P " + mm.msf_pw], shell=True)
        print("MSFRPC is binding to port...")
        sleep(8) # this is terrible, just try to make msf object until it works
        mm.create_msf()

        mm.msfrpc_loaded = 1
        if mm.autostart:
            mm.run = 1
            mm.autostart = 0
