import sched, time
import sys
import subprocess

s = sched.scheduler(time.time, time.sleep)

def cron():
    s.enter(5*60, 1, cron, [])
    command = '{} -m luigi --local-scheduler --module tasks Main'.format(sys.executable)
    output = subprocess.check_output(command.split(), shell= False)

s.enter(5, 1, cron, [])
s.run()