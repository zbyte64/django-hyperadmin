#!/usr/bin/env python

import logging
import subprocess
import os

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class LogStream(object):
    def __init__(self, log_func):
        self.log_func = log_func
    
    def log_line(self, line):
        self.log_func(line)
    
    def writelines(self, sequence):
        for line in sequence:
            self.log_line(line)
    
    def write(self, string):
        self.log_line(string)

class TaskLogger(logging.Logger):
    def __init__(self, *args, **kwargs):
        logging.Logger.__init__(self, *args, **kwargs)
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.addHandler(handler)
    
    def read_log(self):
        return self.log_stream.getvalue()
    
    def get_stdout_object(self):
        return LogStream(self.info)
    
    def get_stderr_object(self):
        return LogStream(self.error)

class CommandResponse(object):
    def __init__(self, session, cmd, popen, block, logger):
        self.session = session
        self.cmd = cmd
        self.popen = popen
        self.joined = False
        self.logger = logger
        if block:
            self.join()
    
    def join(self):
        if self.joined:
            return
        self.joined = True
        self.stdout, self.stderr = self.popen.communicate()
        if self.stdout:
            self.logger.info(self.stdout)
        if self.stderr:
            self.logger.error(self.stderr)
        self.logger.debug('Return Code: %s' % self.returncode)
    
    @property
    def returncode(self):
        return self.popen.returncode

class CommandFailure(Exception):
    pass

class ShellSession(object):
    def __init__(self, logger, cwd=None, **popen_kwargs):
        self.popen_kwargs = {
            'cwd': cwd or os.getcwd(),
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
        }
        self.popen_kwargs.update(popen_kwargs)
        self.logger = logger

    def run(self, cmd, block=True):
        kwargs = dict(self.popen_kwargs)
        if isinstance(cmd, basestring):
            kwargs['shell'] = True
        self.logger.info(cmd)
        result = subprocess.Popen(cmd, **kwargs)
        return CommandResponse(self, cmd, result, block, self.logger)
    
    def run_with_retries(self, cmd, retries=3):
        attempts = list()
        while retries:
            response = self.run(cmd)
            if response.returncode:
                retries -= 1
                attempts.append(response)
            else:
                return response
        raise CommandFailure('Failed to run command, # of attempts: %s' % len(attempts), attempts)

    def cd(self, directory):
        if directory.startswith('/'):
            self.popen_kwargs['cwd'] = directory
        else:
            self.popen_kwargs['cwd'] = os.path.join(self.popen_kwargs['cwd'], directory)
        self.logger.info('cd %s' % self.popen_kwargs['cwd'])

if __name__ == '__main__':
    import sys
    logger = TaskLogger('docbuilder')
    shell = ShellSession(logger, stdout=sys.stdout, stderr=sys.stderr)
    shell.run('virtualenv --system-site-packages .')
    shell.run_with_retries('bin/pip install -q -r doc_requirements.txt')
    shell.run_with_retries('bin/pip install -q Sphinx')
    shell.run('bin/python setup.py build_sphinx -E')

