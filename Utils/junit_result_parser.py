#!/usr/bin/env ipython

from __future__ import print_function

# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=too-many-lines
# pylint: disable=bare-except
# pylint: disable=global-statement
# pylint: disable=global-variable-not-assigned
# pylint: disable=too-many-statements

import sys
import os
import re
import xml.dom.minidom as dom
from pprint import pprint as pp
from optparse import OptionParser
import shutil
import urllib


css1 = '''
<style type="text/css">
table.params {
    font-family: verdana,arial,sans-serif;
    font-size:11px;
    color:#333333;
    border-width: 1px;
    border-color: #666666;
    border-collapse: collapse;
}
table.params th {
    border-width: 1px;
    padding: 4px;
    border-style: solid;
    border-color: #666666;
    background-color: #dedede;
    text-align:left ;

}
table.params td {
    border-width: 1px;
    padding: 4px;
    border-style: solid;
    border-color: #666666;
    background-color: #E5D692;
    text-align:left ;

}

table.testcase {
    font-family: verdana,arial,sans-serif;
    font-size:11px;
    color:#333333;
    border-width: 1px;
    border-color: #666666;
    border-collapse: collapse;
}
table.testcase th {
    border-width: 1px;
    padding: 4px;
    border-style: solid;
    border-color: #666666;
    background-color: #719FB1;
    text-align:left ;

}
table.testcase td {
    border-width: 1px;
    padding: 4px;
    border-style: solid;
    border-color: #666666;
    background-color: #ffffff;
    text-align:left ;
    max-width: 400px;
    word-wrap:break-word;

}


h1 {
    background-color:#CCCCCC;
    border: 1px solid;
    text-align: center;
    }

h2 {
  color: blue;
  text-align: left;
}

.ERROR {
background-color: #FF99FF;
    padding: 2px;

}

.FAIL {
background-color: #FF99FF;
    padding: 2px;

}

.SKIP {
background-color: #58D3F7;
    padding: 2px;

}

.ABORT {
background-color: #FF99FF;
    padding: 2px;

}
.PASS {
background-color: #66FF99;
    padding: 2px;

}

.TOTAL {
color: black;
    padding: 2px;

}

.img {
    position: relative;
}
.img span {
    position: absolute;
    right: 10px;
    top: 10px;
}


</style>
'''

RES_STAT = {}
mList = []


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


def parse_param_file(pfile, mytt):
    tb = {}
    for line in [line.strip() for line in open(pfile, 'r')]:
        if "<BREAK>=:" in line:
            continue
        try:
            key, value = re.split("=:", line)
            tb[key] = value
        except:
            print("waring : parsing errors with (%s), delimiter '=:' " % line)

    mystr = "<table class='params'>"
    mystr += "<tr> <th> %s </th> <td> %s </td> </tr>" % ('Result Summary', mytt['summary'])

    # pylint: disable=consider-iterating-dictionary
    for key in sorted(tb.keys()):
        mystr += "<tr> <th> %s </th> <td> %s </td> </tr>" % (key, tb[key])

    mystr += "</table>"
    mystr += "\n"

    return mystr


def _color_log(logData):

    mystr = ''
    for line in logData.split('\n'):
        line = line.strip()
        if 'sending key ' in line:
            line = "<mystrong style='color:blue'>" + line + "</mystrong>"
        elif "HTTP_REQ" in line:
            o = re.search(r'(HTTP_REQ\d+) ', line)
            if o:
                req = o.groups()[0]
                line = line.replace(req, "<a href='%s.json'>%s</a>" % (req, req))
            line = "<mystrong style='color:blue'>" + line + "</mystrong>"

        elif "TC_WRAPPER BEGIN" in line:
            line = "<mystrong style='color:purple ; text-decoration:underline;'>" + line + "</mystrong>"
        elif "RESULT" in line:
            if "RESULT False" in line:
                line = "<mystrong style='color:#FE2E2E'>" + line + "</mystrong>"
            else:
                # True and everything else are true
                line = "<mystrong style='color:green '>" + line + "</mystrong>"
        mystr += line + "\n"

    return mystr


# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
def parse_xml(inDir):
    global RES_STAT, mList

    RESULT = []
    RES_STAT = {}
    mList = []

    tcLogDir = os.path.join(inDir, "tc_logs")

    if not os.path.exists(tcLogDir):
        os.makedirs(tcLogDir)
    else:
        print("tc_logs exists: %s " % tcLogDir)

    ec_link_base = os.getenv('ec_link_base')
    print("ec_link_base:", ec_link_base)

    # pylint: disable=too-many-nested-blocks
    for file1 in os.listdir(inDir):
        if not file1.endswith('.xml'):
            continue
        print("loading xml input file %s " % file1)

        inFile = os.path.join(inDir, file1)
        d = dom.parse(inFile)
        for node in d.getElementsByTagName('testcase'):
            classname = str(node.getAttribute('classname'))

            tcname = str(node.getAttribute('name'))
            tcName = filename_escape('encode', tcname)

            time = "%0.2f" % float(node.getAttribute('time'))
            if classname not in mList:
                mList.append(classname)
            # find docstr in system-out

            docstr = ""
            tcLink = ""
            tcaseDir = os.path.join(tcLogDir, "%s.%s" % (classname, tcName))
            tcLogFile = os.path.join(tcaseDir, 'log_pytest.txt')
            tcFile = os.path.join(tcaseDir, 'log_pytest.html')

            # logtext=""
            failtext = ""
            node.getElementsByTagName('system-out')
            result = 'PASS'
            failMsg = ''

            # tc status is fail
            failNodeList = node.getElementsByTagName('failure')
            errorNodeList = node.getElementsByTagName('error')
            skipNodeList = node.getElementsByTagName('skipped')

            # print errorNodeList
            if failNodeList != []:
                result = 'FAIL'
                for n in failNodeList:
                    failMsg = n.getAttribute('message')
                    for c in n.childNodes:
                        if c.nodeType == c.TEXT_NODE:
                            failtext = c.data

            elif errorNodeList != []:
                result = 'ERROR'
                for n in errorNodeList:
                    failMsg = n.getAttribute('message')
                    for c in n.childNodes:
                        if c.nodeType == c.TEXT_NODE:
                            failtext = c.data

                # for muti-assert fixtures
                errFile = os.path.join(tcaseDir, 'errMsg.txt')
                print("--errFile is %s" % errFile)
                if os.path.exists(errFile):
                    with open(errFile) as f:
                        errMsg = ''.join(f.readlines())
                    failMsg += "\n %s" % errMsg

            elif skipNodeList != []:
                result = 'SKIP'
                for n in skipNodeList:
                    failMsg = n.getAttribute('message')
                    failMsg += ": " + n.firstChild.nodeValue
                    for c in n.childNodes:
                        if c.nodeType == c.TEXT_NODE:
                            failtext = c.data

            # create log_pytest.html
            try:
                print("writting log_pytest.html", tcFile)
                #if not os.path.exists(os.path.dirname(tcFile)):
                #    os.makedirs(os.path.dirname(tcFile))
                f1 = open(tcFile, 'w')
                f1.write("<html><body>")

                # add snapshot
                pngFiles = []
                if os.path.exists(tcaseDir):
                    # pylint: disable=unused-variable
                    for subdir, dirs, files in os.walk(tcaseDir):
                        for file1 in files:
                            if file1.startswith('ASSERT') and file1.endswith('.png'):
                                imgfile = os.path.basename(file1)
                                pngFiles.append(imgfile)

                pngFiles = sorted(pngFiles)
                if os.path.exists(os.path.join(tcaseDir, 'begin.png')):
                    pngFiles.insert(0, 'begin.png')
                if os.path.exists(os.path.join(tcaseDir, 'end.png')):
                    pngFiles.append('end.png')

                if pngFiles != []:
                    f1.write("<table border=0> <tr>")
                    for imgfile in pngFiles:
                        f1.write("<td style=padding:0px><figure>")
                        f1.write("<img src='%s' alt='%s' width='192' height='128' border='2'>" % (imgfile, imgfile))
                        f1.write("<figcaption> %s </figcaption>" % imgfile.replace(".png", ''))
                        f1.write("</figure></td>")
                    f1.write("</tr></table>")

                f1.write("<h4> <a href='./'> All logs %s.%s  </a> </h4>" % (classname, tcName))
                f1.write("<pre>")

                # add pytest_log.txt
                if os.path.exists(tcLogFile):
                    # print "found %s" % tcLogFile
                    # f1.write("=" * 120 + "\nLOGGING BEGIN %s:%s \n" % (classname, tcName))
                    with open(tcLogFile, 'r') as f2:
                        logData = f2.read()
                    logData = _color_log(logData)
                    f1.write(logData)
                    # f1.write("=" * 120 + "\nLOGGING END\n")
                else:
                    print("Not found %s" % tcLogFile)

                # f1.write(logtext.encode('utf8'))
                if failtext:
                    f1.write("\n")
                    f1.write("<font color='red'>")
                    f1.write("=" * 120 + "\nFailed messages BEGIN\n")
                    f1.write(failtext)
                    f1.write("</font>")

                f1.write("</pre>")
                f1.write("</body></html>")
                f1.close()

                # create tcLink to log_pytest.html
                basefile = re.sub(r'^.*/tc_logs/', '', tcFile)
                if ec_link_base:
                    tcLink = "%s/tc_logs/%s" % (ec_link_base, basefile)
                else:
                    tcLink = "tc_logs/%s" % (basefile)
            except:
                print("warning : error 1 writing to %s : %s " % (tcFile, sys.exc_info()[1]))
                # f1.close()

            # add doc file
            try:
                doc_file = os.path.join(tcaseDir, 'doc.txt')
                with open(doc_file, 'r') as f1:
                    docstr = f1.read()
            except:
                pass

            try:
                RES_STAT[classname] += 1
            except:
                RES_STAT[classname] = 1

            try:
                key = classname + "." + result
                RES_STAT[key] += 1
            except:
                RES_STAT[key] = 1

            description = docstr.strip()
            failMsg = failMsg.strip()
            # print "tcName %s tcLink '%s' " %  ( tcName, tcLink)
            RESULT.append((classname, tcName, time, result, description, failMsg, tcLink))

    # pp(RESULT,indent=2)
    return RESULT


def caculate_summary():

    global mList, RES_STAT, summaryFile

    # make stat table
    FINAL_RESULT = "PASS"
    tt_pass_cnt = 0
    tt_skip_cnt = 0
    tt_fail_cnt = 0
    tt_error_cnt = 0
    tt_abort_cnt = 0
    tt_cnt = 0
    for m in mList:
        tt_cnt += RES_STAT[m]
        try:
            pass_cnt = RES_STAT[m + '.PASS']
            tt_pass_cnt += pass_cnt
        except:
            RES_STAT[m + '.PASS'] = 0
            pass_cnt = 0

        try:
            skip_cnt = RES_STAT[m + '.SKIP']
            tt_skip_cnt += skip_cnt
        except:
            RES_STAT[m + '.SKIP'] = 0
            skip_cnt = 0

        try:
            fail_cnt = RES_STAT[m + '.FAIL']
            tt_fail_cnt += fail_cnt
        except:
            RES_STAT[m + '.FAIL'] = 0
            fail_cnt = 0

        try:
            error_cnt = RES_STAT[m + '.ERROR']
            tt_error_cnt += error_cnt
        except:
            RES_STAT[m + '.ERROR'] = 0
            error_cnt = 0

        try:
            abort_cnt = RES_STAT[m + '.ABORT']
            tt_abort_cnt += abort_cnt
        except:
            RES_STAT[m + '.ABORT'] = 0
            abort_cnt = 0

    if tt_pass_cnt == 0 or tt_fail_cnt > 0 or tt_error_cnt > 0 or tt_abort_cnt > 0:
        FINAL_RESULT = "FAIL"

    tt = {}
    tt['FINAL_RESULT'] = FINAL_RESULT
    tt['tt_pass_cnt'] = tt_pass_cnt
    tt['tt_fail_cnt'] = tt_fail_cnt
    tt['tt_error_cnt'] = tt_error_cnt
    tt['tt_abort_cnt'] = tt_abort_cnt
    tt['tt_skip_cnt'] = tt_skip_cnt
    tt['tt_cnt'] = tt_cnt
    tt['summary'] = "%s:T %s,P %s,F %s ,E %s ,A %s ,S %s\n" % (FINAL_RESULT, tt_cnt, tt_pass_cnt, tt_fail_cnt, tt_error_cnt, tt_abort_cnt, tt_skip_cnt)

    # write summary line
    with open(summaryFile, 'w') as f:
        f.write(tt['summary'])

    return tt


def write_tr(f, array, mytype='td'):
    f.write("<tr>")
    for el in array:
        f.write("<%s>%s</%s>" % (mytype, el, mytype))
    f.write("</tr>\n")


def make_html(recList, htmlFile, summaryFile, paramFile, tt):
    global mList, RES_STAT
    global title
    global css1, css2
    global options

    f = open(htmlFile, 'w')
    f.write("<!doctype html>\n")
    f.write("<head>\n")
    f.write("%s" % css1)
    f.write("</head>\n")
    f.write("<body>\n")

    if title:
        f.write("<h1> %s </h1>" % title)

    # make param table
    if paramFile and os.path.exists(paramFile):
        str1 = parse_param_file(paramFile, tt)
        f.write(str1)
        f.write("<br>")
        f.write("<hr>")

    # make stat table
    f.write("<h2> Test Result Summary</h2>")

    # testcase table
    f.write("<table class='testcase'>")
    f.write("<tr><th>Suite </th> <th>Total</th> <th>PASS</th><th>FAIL</th><th>ERROR</th><th>ABORT</th><th>SKIP</th></tr>")
    for m in mList:
        f.write('<tr>')
        f.write('<td> <a href=#%s> %s <a> </td>' % (m, m))
        f.write("<td><span style=color:black> %s </span></td>" % (RES_STAT[m]))
        f.write("<td><span style=color:green> %s </span></td>" % (RES_STAT[m + '.PASS']))
        f.write("<td><span style=color:red> %s </span></td>" % (RES_STAT[m + '.FAIL']))
        f.write("<td><span style=color:red> %s </span></td>" % (RES_STAT[m + '.ERROR']))
        f.write("<td><span style=color:red> %s </span></td>" % (RES_STAT[m + '.ABORT']))
        f.write("<td><span style=color:red> %s </span></td>" % (RES_STAT[m + '.SKIP']))

        f.write('</tr>')

    f.write('<tr>')
    f.write('<th> %s </th>' % ('Total'))
    f.write("<th><span style=color:black> %s </span></th>" % (tt['tt_cnt']))
    f.write("<th><span style=color:green> %s </span></th>" % (tt['tt_pass_cnt']))
    f.write("<th><span style=color:red> %s </span></th>" % (tt['tt_fail_cnt']))
    f.write("<th><span style=color:red> %s </span></th>" % (tt['tt_error_cnt']))
    f.write("<th><span style=color:red> %s </span></th>" % (tt['tt_abort_cnt']))
    f.write("<th><span style=color:red> %s </span></th>" % (tt['tt_skip_cnt']))
    f.write('</tr>')
    f.write("</table>")

    # f.write("<hr>")

    # make failed tc table
    if options.failcase:
        f.write("<h2>Failed testcases</h2>")
        make_testcase_table(recList, f, Fonly=True)

    f.write("<br><hr><br>")
    # ## make tc table

    f.write("<h2>Complete testcases </h2>")

    make_testcase_table(recList, f)

    f.write("</body>")
    f.write("</html>")
    f.close()


def make_testcase_table(recList, f, Fonly=False):
    global mList, RES_STAT

    classname_old = None
    f.write("<table class='testcase'>")
    tc_cnt = 0

    for line in recList:

        classname, tc, time, result, description, failMsg, tcLink = line

        tcname = filename_escape('decode', tc)

        if Fonly and result == "PASS":
            continue
        tc_cnt += 1
        if classname != classname_old:
            # tc_cnt=1
            f.write("</table>")
            # f.write("<br>")
            f.write("<a name=%s>" % classname)
            f.write("<h3>%s</h3>" % classname)
            f.write("<table class='testcase'>")

            f.write("<tr><th>Testcase</th><th>description</th><th>Result</th><th>Exec time</th><th>Failure messages</th></tr>")
            classname_old = classname

        f.write("<tr>")
        if not tcLink:
            f.write("<td> %d. %s.%s </td>" % (tc_cnt, classname, tcname))
        else:
            f.write("<td> <a href=%s> %d. %s.%s </a> </td>" % (tcLink, tc_cnt, classname, tcname))

        # description
        if len(description) > 200:
            description = description[:201] + "<a href=tc_logs/%s.%s/doc.txt> (full text) </a>" % (classname, tc)

        description = description.replace("BUG", "<strong style='color: red'>BUG</strong>")
        description = re.sub(r'(US\S+)', r"<strong style='color: purple'>.\1 </strong>", description, re.IGNORECASE)
        description = re.sub('\n', '<br/>\n', description)

        f.write("<td> <span class='.td_max'> %s </span> </td>" % (description))

        # result
        f.write("<td><span class=%s> %s </span></td>" % (result, result))

        # exec time
        f.write("<td>%s</td>" % time)

        failMsg = failMsg.replace("\n", "<br>")
        f.write("<td>%s</td>" % failMsg)
        f.write("</tr>")

    f.write("</table>")


##################
# main


usage = '%s <inputdir>' % sys.argv[0]
usage += "\n input directory contains the xml result files"


parser = OptionParser(usage=usage)
parser.add_option("-o", "--outdir", dest="outdir", default=None, help="copy input directroy to this directory")

parser.add_option("-t", "--title", dest="title", default=None, help="HTML report title")
parser.add_option("-p", "--paramFile", dest="paramFile", default=None, help="paramter file, format should be key:=vaules")
parser.add_option("-s", "--testFile", dest="testFile", default=None, help="location of the expected test suite list")

parser.add_option("-f", "--failcase", dest="failcase", action='store_true', help="show failed testcase section")

(options, args) = parser.parse_args()

# print("args", args)

if len(sys.argv) < 2:
    print(sys.argv)
    print("ERROR syntax: %s" % usage)
    sys.exit(-1)

indir = os.path.abspath(sys.argv[1])
if not os.path.exists(indir):
    print(sys.argv)
    print("%s indir not exists" % indir)
    sys.exit(-1)


outdir = options.outdir

htmlFile = os.path.join(indir, 'testcase.html')
summaryFile = os.path.join(indir, 'summary.txt')
paramFile = options.paramFile
title = options.title


print("-Parsing xml inputFile %s" % indir)

resultList = parse_xml(indir)
# pp(RES_STAT,indent=2)
# update tt list
tt = caculate_summary()
pp(tt, indent=2)

make_html(resultList, htmlFile, summaryFile, paramFile, tt)
print("+OK: html result created at %s" % htmlFile)

if outdir:
    try:
        shutil.rmtree(outdir)
    except:
        pass
    print("+OK: out results are copied to %s" % outdir)
    shutil.copytree(indir, outdir)


if tt['FINAL_RESULT'] == "PASS":
    exit_code = 0
else:
    exit_code = 1

with open(summaryFile, 'r') as f:
    summary = f.read()
print("Note: please use ec-proepry setSummary to parse the following line")
print("TEST_SUMMARY: %s" % summary)
print("FINAL results %s , exit code %s" % (tt['FINAL_RESULT'], exit_code))
sys.exit(exit_code)


# vim: syntax=python
# ;;; Local Variables: ***
# ;;; mode: python ***
# ;;; End: ***


#  LocalWords:  br
