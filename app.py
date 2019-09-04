from flask import Flask, render_template, request
from functools import wraps
from engine import cycle, model, db
from threading import Thread
from hashlib import sha256
import logging, os, subprocess, sys, random

# Flask information
app = Flask(__name__)
app.secret_key = 'this is a secret :-)wrjiafih'

# Logging config
logging.basicConfig(filename='app.log', format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s', \
    datefmt='%I:%M:%S %p', level=logging.INFO)

# Logging pretty colors
logging.addLevelName(
    logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(
    logging.WARNING,
    "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.WARNING))

# "Parse" command line arguments
if len(sys.argv) > 2:
    print("Usage: ./app.py [autostart]")

# Load data model
mm = model.MetaModel()
if 'autostart' in sys.argv:

    mm.autostart = 1

@app.route('/login', methods=['GET', 'POST'])
def login():

    failure = "yes"
    # login function here
    return render_template('login.html', failure=failure)


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    access_data = db.getall('access_log')
    labels = []
    values = []

    for team in mm.teams:
        values.append([
            'Team ' + str(team.id), 'rgb(' + str(random.randint(0, 256)) +
            ',' + str(random.randint(0, 256)) + ',' +
            str(random.randint(0, 256)) + ',' + '1)', []
        ])

    # add cap on data lol?
    cycles = int(len(access_data) / len(mm.teams))
    for x in range(cycles):
        labels.append(str(x))

    for data in access_data:
        values[int(data[2]) - 1][2].append(data[3])

    return render_template('dashboard.html',
                           r=mm.run,
                           d=mm.dest,
                           labels=labels,
                           values=values)

@app.route('/teams', methods=['GET', 'POST'])
def teams():

    success = error = team = 0  # Set false/none

    if 'view' in request.args:
        try:
            team_id = int(request.args['view'])
        except:
            error = "Invalid team ID."
        try:
            team = mm.teams[int(team_id) - 1]
        except:
            error = "Team ID doesn't exist."
        if error:
            return render_template('teams.html',r=mm.run,
                           d=mm.dest, teams=mm.teams, error=error)
        if request.method == 'GET':
            return render_template('team_details.html', r=mm.run, d=mm.dest, team=team)

    if request.method == 'POST':

        if 'action' in request.form:
            if request.form['action'] == 'edit' or request.form['action'] == 'add':
                return render_template('team_edit.html', r=mm.run, d=mm.dest, team=team)

            if request.form['action'] == 'cancel':
                if team:
                    return render_template('team_details.html', r=mm.run, d=mm.dest, team=team)
                else:
                    return render_template('teams.html', r=mm.run, d=mm.dest)


            if request.form['action'] == 'save':
                    try:
                        if request.form['name'] != "":
                            name = request.form['name']
                        # character whitelist here
                    except:
                        error = "Invalid characters in team name."
                    try:
                        if request.form['ip'] != "":
                            ip = request.form['ip']
                        # regex matching here
                    except:
                        error = "Invalid IP address format."
                    try:
                        difficulty = request.form['difficulty']
                        # diffiulty integer within range test here
                    except:
                        error = "Invalid difficulty."
                    if not error:
                        success = 1
                        if team == 0:
                            team_info = (name, ip, difficulty)
                            mm.write_team(team_info)
                            return render_template('teams.html', r=mm.run, d=mm.dest, teams=mm.teams, success=success)
                        else:
                            team.save()
                            return render_template('team_details.html', r=mm.run, d=mm.dest, team=team, success=success)

    return render_template('teams.html', r=mm.run, d=mm.dest, teams=mm.teams, error=error)


@app.route('/systems', methods=['GET', 'POST'])
def systems():

    success = error = system = 0  # Set false/none

    if 'view' in request.args:
        try:
            system_num = int(request.args['view'])
            system = mm.teams[0].systems[system_num - 1]
        except:
            error = "Invalid system number."
            return render_template('systems.html', r=mm.run, d=mm.dest, systems=mm.teams[0].systems, error=error)
        if request.method == 'GET':
            if 'team' in request.args:
                try:
                    team_id = int(request.args['team'])
                    team = mm.teams[team_id - 1]
                    system = team.systems[system_num - 1]
                except:
                    error = "Invalid team ID."
                    return render_template('systems.html', r=mm.run, d=mm.dest, systems=mm.teams[0].systems, error=error)
                return render_template('system_team_details.html', r=mm.run, d=mm.dest, system=system, team=team)
            for team in mm.teams:
                systems.append(team.systems[system_num - 1])
            return render_template('system_details.html', r=mm.run, d=mm.dest, systems=systems)

    if request.method == 'POST':

        if 'action' in request.form:
            if request.form['action'] == 'edit' or request.form['action'] == 'add':
                return render_template('system_edit.html', r=mm.run, d=mm.dest, system=system)

            if request.form['action'] == 'cancel':
                return render_template('system_team_details.html', r=mm.run, d=mm.dest, system=system)

            if request.form['action'] == 'save':
                try:
                    if request.form['name'] != "":
                        name = request.form['name']
                    # character whitelist here
                except:
                    error = "Invalid characters in system name."
                    name = ""
                try:
                    if request.form['os'] != "":
                        os = request.form['os']
                    # regex matching here
                except:
                    error = "Invalid operating system."
                    os = ""
                try:
                    if request.form['flavor'] != "":
                        flavor = request.form['flavor']
                    # regex matching here
                except:
                    error = "Invalid flavor."
                    flavor = ""
                try:
                    if request.form['ip'] != "":
                        ip = request.form['ip']
                    # diffiulty integer within range test here
                except:
                    error = "Invalid IP Address."
                    ip = ""
                if not error:
                    if system == 0:
                        if name and os and flavor and ip:
                            success = 1
                            for team in mm.teams:
                                system_info = (sys_num, "Inactive", name, team.id, team.ip + str(ip), os, flavor, sys_vulns)
                                team.systems.append(System("new", *system_info))
                        else:
                            error = "All forms must be filled."
                    else:
                        for team in mm.teams:
                            system = team[system_num - 1]
                            system.name = name
                            system.os = os
                            system.flavor = flavor
                            system.ip = ip
                            system.save()
                    return render_template('systems.html', r=mm.run, d=mm.dest,  system=system, success=success, error=error)

    return render_template('systems.html', r=mm.run, d=mm.dest, systems=mm.teams[0].systems, error=error)


@app.route('/modules', methods=['GET', 'POST'])
def modules():
    modules = db.getall('modules')
    return render_template('modules.html', r=mm.run, d=mm.dest, modules=modules)

@app.route('/engine', methods=['GET', 'POST'])
def engine():

    error = ""
    if request.method == 'POST':
        if request.form['action'] == 'start':
            if mm.msfrpc_loaded:
                mm.run = 1
            else:
                error = "MSFRPC isn't done initializing yet, sorry :("
        elif request.form['action'] == 'stop':
            mm.run = 0
        elif request.form['action'] == 'enable_destruction':
            mm.dest = 1
        elif request.form['action'] == 'disable_destruction':
            mm.dest = 0
        elif request.form['action'] == 'export':
            return ("config")

    proc = subprocess.Popen(['tail', '-n', '10', 'app.log'],
                            stdout=subprocess.PIPE)
    log_data = proc.stdout.readlines()
    log_data = [log.decode('utf-8').split(' ')[5:] for log in log_data]
    log_data = [" ".join(log) for log in log_data]
    return render_template('engine.html',
                           r=mm.run,
                           d=mm.dest,
                           cyc=mm.cycles,
                           log_data=log_data[::-1],
                           error=error,
                           autostart=mm.autostart)


@app.route('/workshop', methods=['GET', 'POST'])
def workshop():

    return render_template('workshop.html', r=mm.run, d=mm.dest)


# Spawn cycler process
logging.info("Spawning pentesting cycle.")
PenCycle = cycle.PentestingCycle()
cycle = Thread(target=PenCycle.start, args=(mm, ))
cycle.name = "Cycler"
cycle.start()

# Launch web server
logging.info("Running web server.")
app.run(debug=True, use_reloader=False, host= '0.0.0.0')
