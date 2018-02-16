from functools import wraps
import errno
import os
import sys
import re
import time
import signal
#import subprocess
import collections
import urllib
import logging
import termcolor
logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


assertCnt = 0


def myassert(result, message):
    global assertCnt
    assertCnt += 1
    msg1 = "(ASSERT%s RESULT %s) %s" % (assertCnt, result, message)

    if result:
        color = 'green'
    else:
        color = 'red'
    if os.sys.stdout.isatty():
        print(termcolor.colored(msg1, color))

    logger.info(msg1)
    if not result:
        if os.environ.get('TC_LOGGER_CURR_DIR') and os.environ.get('MULTI_ASSERT') == 'true':
            tc_err_file = os.path.join(os.environ['TC_LOGGER_CURR_DIR'], 'errMsg.txt')
            if os.path.exists(tc_err_file):
                # multi_assert fixure is used
                with open(tc_err_file, 'a') as f:
                    f.write(msg1 + "\n")
        else:
            # no mulit_assert. just abort
            assert result, message


def get_tc_log_dir():
    '''
    must be used together with 'tc_logger' fixture
    '''
    return os.environ.get('TC_LOGGER_CURR_DIR')


def write_tc_log_file(filename, content, msg=""):
    '''
    save 'content' to 'a file under tclogdir
    putil=write_tc_log_file('myfile.txt','test1')
    '''

    cprint("-Create tc_log file '%s' %s" % (filename, msg), color='blue')
    filepath = os.path.join(get_tc_log_dir(), filename)
    with open(filepath, 'w') as f:
        f.write(content)
    logger.info("Wote <a href='%s'>%s</a> : %s" % (filename, filename, msg))


def cprint(msg, color='blue'):
    if os.sys.stdout.isatty():
        print(termcolor.colored(msg, color))
    logger.info(msg)


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    '''
    timeout command used for function decortor
    '''
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator


@timeout(300)
def exec_cmd(cmd):
    '''
    This command is to execute system command and return the output as string. default is 300 secs timeout
    variable timeout is not working yet.
    ex:
    import putil
    out=putil.exec_cmd("ls -l")
    print out
    '''
    logger.info("putil:exec_cmd:", cmd)
    out = os.popen(cmd).read()
    return out



def run_subprocess(cmd,stderr=False,verbose=True):
    '''
    putils.run_cmd("helm ls | grep xxx") ==> return False
    putils.run_cmd("helm ls | grep kafka") ==> return True without output
    '''
    import shlex
    from subprocess import Popen, PIPE

    logger.info(cmd)
    process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    # execute it, the output goes to the stdout
    (out, err) = process.communicate()
    exit_code = process.wait()    # when finished, get the exit code
    if exit_code == 0:
        res=True
        output=out
    else:
        res=False
        output=err
    # to support python3
    output=output.decode("utf-8").strip()
    if stderr:
        output += err.decode("utf-8").strip()

    if verbose:
        print(output)
  
    # print does not show in gitalb console
    #print("\n"+output)
    return (res,output)


# def run_subprocess(command, realTime=True):
#     '''
#     examples:
#     http://stackoverflow.com/questions/1606795/catching-stdout-in-realtime-from-subprocess
#     putil.subprocess('ps ax')
#     output=putil.run_subprocess('ps ax',readTime=False)



#     '''
#     logger.info("run_subprocess: (%s)" % command)
#     cmdList = command.split()
#     p = subprocess.Popen(cmdList,
#                          stdout=subprocess.PIPE,
#                          stderr=subprocess.STDOUT
#                          )
#     if realTime:
#         output = ""
#         for line in iter(p.stdout.readline, b''):
#             #this line needed for python3
#             line=line.decode("utf-8")
#             logger.info(line.rstrip())
#             output += line
#         return output
#     else:
#         output = p.stdout.readlines()
#         return "".join(output)




def _flatten(structure, key="", path="", flattened=None, seperator=".", strify=True):
    '''
    A utils to to flatten a json data structure.
    return a one layer dictionary
    examples:
    data='{ "id":   "BOOKING_JOB_ID",  "duration":  "DURATION", "content":  {"id":   "EVENT_LOCATOR"}}'
    j=json.loads(data)
    d=putil.flatten(j)  --> d is a dictionary
    {u'..content.id': u'EVENT_LOCATOR',
    u'..duration': u'DURATION',
    u'..id': u'BOOKING_JOB_ID'}
    '''
    if flattened is None:
        flattened = {}
    if type(structure) not in(dict, list):
        flattened[((path + seperator) if path else "") + key] = structure
    elif isinstance(structure, list):
        for i, item in enumerate(structure):
            _flatten(item, "%d" % i, path + seperator + key, flattened)
    else:
        for new_key, value in structure.items():
            if strify:
                new_key = str(new_key)
                value = str(value)
            _flatten(value, new_key, path + seperator + key, flattened)
    return flattened


def flatten_json(structure, key="", path="", flattened=None, seperator="."):
    '''
    A utils to to flatten a json data structure.
    return a one layer dictionary
    examples:
    data='{ "id":   "BOOKING_JOB_ID",  "duration":  "DURATION", "content":  {"id":   "EVENT_LOCATOR"}}'
    j=json.loads(data)
    d=putil.flatten_json(j)  --> d is a dictionary
    {u'content.id': u'EVENT_LOCATOR',
    u'uration': u'DURATION',
    u'id': u'BOOKING_JOB_ID'}
    '''
    D1 = _flatten(structure, key=key, path=path, flattened=flattened, seperator=seperator)
    D2 = {}
    for key, val in D1.items():
        key = re.sub(r"^..", "", key)
        D2[key] = val
    return D2


def flatten_dict(d, parent_key='', sep='.'):
    '''
    putil.flatten_dict({'a': 1, 'c': {'a': 2, 'b': {'x': 5, 'y' : 10}}, 'd': [1, 2, 3]})
    {'a': 1, 'c.a': 2, 'c.b.x': 5, 'd': [1, 2, 3], 'c.b.y': 10}
    '''

    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def wait_until_true(duration, interval, fun, *args):
    '''
    ex: putil.wait_until_true(120 , 5 , putil.ping , '1.1.1.1')
    ex: putil.wait_until_true(120 , 5 , putil.ping , '1.1.1.1',3)
    '''
    logger.info("wait_until_true %d %d %s %s" % (duration, interval, fun.__name__, args))
    elasp = 0
    while elasp <= duration:
        res = fun(*args)
        if res:
            logger.info("+True.'%s' return True in %d secs..." % (fun.__name__, elasp))
            return True
        logger.info("-%d/%d secs (interval %d) : '%s' still return False..." % (elasp, duration, interval, fun.__name__))
        time.sleep(interval)
        elasp = elasp + interval

    logger.info("+False. '%s' return False in %d secs..." % (fun.__name__, elasp))
    return False


def wait_until_false(duration, interval, fun, *args):
    '''
    ex: putil.wait_until_false(120 , 5 , putil.ping , '1.1.1.1')
    '''
    # ctime=int(round(time.time()))
    logger.info("wait_until_false %d %d %s %s" % (duration, interval, fun.__name__, args))
    elasp = 0
    while elasp <= duration:
        res = fun(*args)
        if not res:
            logger.info("+True.'%s' return False in %d secs..." % (fun.__name__, elasp))
            return True
        logger.info("-%d/%d secs (interval %d) : '%s' still return True..." % (elasp, duration, interval, fun.__name__))
        time.sleep(interval)
        elasp = elasp + interval

    logger.info("+False. '%s' return True in %d secs..." % (fun.__name__, elasp))
    return False


def ping(ip, c=5):
    '''
    ex : putil.ping('1.1.1.1')
    return True or False
    '''
    command = os.system('ping -c %d %s' % (c, ip))
    if command == 0:
        return True
    else:
        return False


def sleep(secs, messages=""):
    '''
    In [37]: putil.sleep(2,"wait for something")
    ...Wait 2 secs for wait for something ....
    '''
    if secs != 0:
        logger.info("..Wait %s secs ,for %s ...." % (secs, messages))
        time.sleep(secs)


def swap(a, b):
    '''
    In [36]: putil.swap(2,3)
    Out[36]: (3, 2)
    In [39]: putil.swap(['x'],['y'])
    Out[39]: (['y'], ['x'])
    '''
    c = a
    a = b
    b = c
    return(a, b)


def isIp(str):
    '''
    In [34]: putil.isIp('rdk1')
    Out[34]: False

    In [35]: putil.isIp('1.1.1.1')
    Out[35]: True

    '''
    o = re.match(r'(\d+\.){3}\d+', str)
    if o:
        return True
    else:
        return False


def filename_escape(mode, name):
    '''
    To escape filename contains specail chars which will not work in http links
    ex:

    file='test_zaplist_channel_change[arrow_up-1]'
    In [9]:file1=filename_escape('encode',file)
    Out[9]: 'test_zaplist_channel_change$5Barrow_up-1$5D'

    In [14]: filename_escape('decode',file1)
    Out[14]: 'test_zaplist_channel_change[arrow_up-1]'


    '''
    if sys.version_info <= (3, 0):
        # pyton2
        if mode == "encode":
            name = urllib.quote_plus(name)
            name = re.sub(r'%', '$', name)
        else:
            name = re.sub(r'\$', '%', name)
            name = urllib.unquote_plus(name)

    else:
        # python3
        if mode == "encode":
            tb = str.maketrans('%', '$')  # pylint: disable=no-member
            name = urllib.parse.quote(name)  # pylint: disable=no-member
            name = name.translate(tb)
        else:
            tb = str.maketrans('$', '%')  # pylint: disable=no-member
            name = name.translate(tb)
            name = urllib.parse.unquote(name)  # pylint: disable=no-member
    return name


def parse_top(file, processList='default'):
    '''
    c.parse_top(top_output)
    return top data in dict
    '''

    if processList == "default":
        processList = ['nxserver', 'cgmi-daemon-1.0', 'rmfStreamer', 'epgapp', 'vgdrmprocess']

    data_array = []

    data = ""
    with open(file) as f:
        for line in f.readlines():
            if data != "":
                top_dict = _parse_a_top(data)
                data_array.append(top_dict)
            if line.startswith('Cpu'):
                data = ""
            data += line

    # caculate sum
    top = {}
    top['cpu_%'] = {}
    top['cpu_%']['used'] = 0
    top['cpu_%']['free'] = 0
    top['mem_k'] = {}
    top['mem_k']['used'] = 0
    top['mem_k']['free'] = 0
    top['task'] = {}
    for pname in processList:
        top['task'][pname] = {}
        top['task'][pname]['cpu_%'] = 0
        top['task'][pname]['mem_%'] = 0
        top['task'][pname]['virt'] = 0

    for item in data_array:
        top['cpu_%']['used'] += item['cpu_%']['used']
        top['cpu_%']['free'] += item['cpu_%']['free']
        top['mem_k']['used'] += item['mem_k']['used']
        top['mem_k']['free'] += item['mem_k']['free']
        for pname in processList:
            top['task'][pname]['cpu_%'] += item['task'][pname]['cpu_%']
            top['task'][pname]['mem_%'] += item['task'][pname]['mem_%']
            top['task'][pname]['virt'] += item['task'][pname]['virt']

    # caculate avg
    if len(data_array) > 0:
        top['cpu_%']['used'] = top['cpu_%']['used'] / len(data_array)
        top['cpu_%']['free'] = top['cpu_%']['free'] / len(data_array)
        top['mem_k']['used'] = top['mem_k']['used'] / len(data_array)
        top['mem_k']['free'] = top['mem_k']['free'] / len(data_array)
        for pname in processList:
            top['task'][pname]['cpu_%'] = top['task'][pname]['cpu_%'] / len(data_array)
            top['task'][pname]['mem_%'] = top['task'][pname]['mem_%'] / len(data_array)
            top['task'][pname]['virt'] = top['task'][pname]['virt'] / len(data_array)

    # pp(top,indent=2)
    return top


def _parse_a_top(out, processList='default'):

    if processList == "default":
        processList = ['nxserver', 'cgmi-daemon-1.0', 'rmfStreamer', 'epgapp', 'vgdrmprocess']

    pname_start = False
    top = {}
    top['cpu_%'] = {}
    top['cpu_%']['used'] = 0
    top['cpu_%']['free'] = 0
    top['mem_k'] = {}
    top['mem_k']['used'] = 0
    top['mem_k']['free'] = 0
    top['task'] = {}
    for pname in processList:
        top['task'][pname] = {}
        top['task'][pname]['cpu_%'] = 0
        top['task'][pname]['mem_%'] = 0
        top['task'][pname]['virt'] = 0

    for line in out.split('\n'):
        if line.startswith('Cpu'):
            o = re.search(r'([.0-9]+)%us,\s+([.0-9]+)%sy,\s+([.0-9]+)%ni,\s+([.0-9]+)%id,', line)
            if o:
                us, sy, ni, idle = o.groups()
                top['cpu_%']['used'] = int(float(us) + float(sy))
                top['cpu_%']['free'] = int(float(idle))
                continue
        if line.startswith('Mem'):
            o = re.search(r'(\d+)k used,\s+(\d+)k free,', line)
            if o:
                used, free = o.groups()
                top['mem_k']['used'] = int(used)
                top['mem_k']['free'] = int(free)
            continue
        if "PID USER" in line:
            pname_start = True
            continue
        # pp(top,indent=2)
        if pname_start:
            # pname_line = line.strip()
            o = re.search(r'(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.*)', line)
            if o:
                # print "parsed %s" % line
                pid, user, pr, ni, virt, res, shr, s, cpu, mem, time, command = o.groups()
                if virt.endswith('m'):
                    virt = virt.replace('m', '000')
                for pname in processList:
                    if pname in command:
                        top['task'][pname]['cpu_%'] = int(float(cpu))
                        top['task'][pname]['mem_%'] = int(float(mem))
                        top['task'][pname]['virt'] = int(float(virt))

    return top


def get_sub_dict(dict, key_list=[]):
    '''
    return a subset of of dictionary
    In [2]: x={1:2 , 3:4 , 5:6}
    In [13]: get_sub_dict(x,[1,5])
    Out[13]: {1: 2, 5: 6}
    for key does not found in the orgianl dict. the entry added with value 'None'
    '''
    temp = {}
    for key in key_list:
        try:
            temp[key] = dict[key]
        except:
            temp[key] = None
    return temp


if __name__ == '__main__':

    cprint("Testing putil")
    file = 'test_zaplist_channel_change[arrow_up-1]'
    print("orginal file", file)
    file1 = filename_escape('encode', file)
    print("encode file", file1)
    file2 = filename_escape('encode', file1)
    print("DEcode file", file2)
