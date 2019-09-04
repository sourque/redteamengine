#!/usr/bin/env python

import msgpack
import http.client
import logging
from time import sleep


class Msfrpc:

    def __init__(self, mm):
        self.host = "127.0.0.1"
        self.port = 55553
        self.uri = "/api/"
        self.ssl = False
        self.authenticated = False
        self.token = False
        self.opts = []
        self.headers = {"Content-type": "binary/message-pack"}
        self.mm = mm

    def encode(self, data):
        return (msgpack.packb(data, use_bin_type=True))

    def decode(self, data):
        # Returns b'STRING'
        return (msgpack.unpackb(data, encoding='utf-8'))

    def call(self, meth, opts=[]):
        if opts:
            self.opts = opts
        if meth != "auth.login":
            if not self.authenticated:
                logging.warning("MSFRPC is not authenticated.")
            self.opts.insert(0, self.token)
        self.opts.insert(0, meth)
        params = self.encode(self.opts)
        while True:
            if not self.mm.thread_lock:
                self.mm.thread_lock = 1
                self.client.request("POST", self.uri, params, self.headers)
                resp = self.client.getresponse()
                self.mm.thread_lock = 0
                self.opts = []
                return self.decode(resp.read())

    def login(self, user, password):
        ret = self.call('auth.login', [user, password])
        if ret.get(b'result') == b'success':
            self.authenticated = True
            self.token = ret.get(b'token').decode('utf-8')
            return (True)
        else:
            return (False)

    def generate_token(self):
        ret = self.call('auth.token_generate', [])
        if ret.get(b'result') == b'success':
            self.token = ret.get(b'token').decode('utf-8')
            return (True)
        else:
            return (False)

    def start(self, pw):
        if self.ssl:
            self.client = http.client.HTTPSConnection(self.host, self.port)
        else:
            self.client = http.client.HTTPConnection(self.host, self.port)
        try:
            # Login to the msfmsg server
            if self.login('msf', pw):
                return (True)
        except:
            logging.warning("Failed to start pymsf object.")
            return (False)

    # TODO LOL
    def check(self, session_id):
        try:
            result = self.call('session.shell_write', [session_id, cmd + "\n"])
            data = self.call('session.shell_read', [session_id])
            return (data)
        except:
            logging.info("Failed to read/write to shell.")
            return (False)

    def create_con(self, pw):
        try:
            # Create console
            con = self.call('console.create', [])[b'id']
            # Get rid of banner input
            self.call('console.read', [con])
            # Return console number
            return (int(con))
        except:
            logging.warning("Failed to create console.")
            return (False)

    def input(self, con, cmd):
        try:  # Write to msf console
            ret = self.call('console.write', [con, cmd + '\r\n'])
            data = self.call('console.read', [con])[b'data'].decode('utf-8')
            return (data)
        except:
            logging.warning("Failed to write data to msf console.")
            return (False)

    def execute(self, category, mod, options):
        try:
            data = False
            data = self.call('module.execute', [category, mod, options])
            job_id = str(data[b'job_id'])
            uuid = data[b'uuid']
            return (job_id, uuid)
        except:
            logging.info("MSF module failed.")
            return (data, False)

    # find session based on dictionary key:value
    # should be a better way to do this
    def get_session(self, job_id, exploit_uuid):

        try:
            session = False
            sleep(3)

            for i in range(10):
                job_list = self.call('job.list')
                if not job_id in job_list:
                    session_list = self.call('session.list')
                    for session_search in session_list.items():
                        if session_search[1][b'exploit_uuid'] == exploit_uuid:
                            session = session_search
                            return (session)
                sleep(0.1)

            if job_id in job_list:
                # add it to the mm checker list
                logging.info("need to add this job to the checker list -- aka job id still exists")

        except:
            logging.info("Failed to get session.")
            return(False)

    def upgrade_session(self, session_id, lhost, lport):
        try:
            result = self.call('session.shell_upgrade', [session_id, lhost, lport])
            return (result[b'result'] == b'success')
        except:
            logging.info("Failed to upgrade session.")
            return (False)

    def meterpreter_input(self, session_id, lhost, lport):
        try:
            result = self.call('session.meterpreter_write', [session_id, cmd])
            if result[b'result'] == b'success':
                data = self.call('session.meterpreter_read', [session_id])
                return (data)
        except:
            logging.warning("Failed to read/write from meterpreter.")
            return (False)

    def shell_input(self, session_id, cmd):
        # try:
        result = self.call('session.shell_write', [session_id, cmd + "\n"])
        data = self.call('session.shell_read', [session_id])
        return (data)
        # except:
            # logging.warning("Failed to read/write to shell.")
            # return (False)
