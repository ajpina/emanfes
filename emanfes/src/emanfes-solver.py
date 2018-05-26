#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# ==========================================================================
# Copyright (C) 2016 Dr. Alejandro Pina Ortega
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==========================================================================

"""
    Creates a geometry and call a solver.
"""

# ==========================================================================
# Program:   emanfes-solver.py
# Author:    ajpina
# Date:      12/23/17
# Version:   0.1.1
#
# Revision History:
#      Date     Version  Author    Description
#  - 12/23/17:  0.1.1              Call Elmer Solver
#
# ==========================================================================

import getopt
import json
import logging
import sys
import time

from emanfes.analysis import Analysis
from emanfes.misc.constants import *
from uffema.machines import RotatingMachine


#from database import db_connector as db


class Usage(Exception):
    def __init__(self, msg):
        self.msg = "[Error]: %s" % ( msg )


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hd:m:a:l:o:ps:e:", ["help","dir","machine","analysis","log","ouput","plot","save","execute"])
        except getopt.GetoptError as msg:
             raise Usage(msg)
        loglevel = LOG_ALL
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print ('emanfes.py -d [dir_name] -m [machine_file] -a [analysis_file] -l [level] -o [output_file] -p -s [database_file] -e [execute]')
                sys.exit()
            elif opt in ("-d", "--dir"):
                dir = arg
            elif opt in ("-m", "--machine"):
                machine_file = arg
            elif opt in ("-a", "--analysis"):
                analysis_file = arg
            elif opt in ("-l", "--log"):
                loglevel = int(arg)
            elif opt in ("-o", "--output"):
                output_file = arg
            elif opt in ("-p", "--plot"):
                plot = True
            elif opt in ("-s", "--save"):
                db_file = arg
            elif opt in ("-e", "--execute"):
                meshing = False
                solving = False
                postprocessing = False
                if arg == "all" or arg == "mesh":
                    meshing = True
                if arg == "all" or arg == "solve":
                    solving = True
                if arg == "all" or arg == "post_process":
                    postprocessing = True



    except Usage as err:
        print (err.msg, file=sys.stderr)
        print("for help use --help", file=sys.stderr)
        return 2

    analysis_filename = "%s/%s" % (dir, analysis_file)
    machine_filename = "%s/%s" % (dir, machine_file)

    start1 = time.clock()
    with open(analysis_filename) as analysis_file:
        analysis_settings = json.load(analysis_file)

    with open(machine_filename) as machine_file:
        machine_settings = json.load(machine_file)

    logfile = "%s/%s.log" % (dir, 'emanfes0')

    if loglevel >= LOG_ALL:
        loglevel = LOG_ALL
        logging.basicConfig(filename=logfile, level=logging.DEBUG,
                            format='%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
    elif loglevel == LOG_INFO:
        logging.basicConfig(filename=logfile, level=logging.INFO,
                            format='%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
    elif loglevel == LOG_WARN:
        logging.basicConfig(filename=logfile, level=logging.WARNING,
                            format='%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
    elif loglevel == LOG_ERROR:
        logging.basicConfig(filename=logfile, level=logging.ERROR,
                            format='%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
    elif loglevel == LOG_CRITICAL:
        logging.basicConfig(filename=logfile, level=logging.CRITICAL,
                            format='%(asctime)s - [%(name)s] %(levelname)s: %(message)s')

    machine = RotatingMachine.create(machine_settings['machine'])
    analysis = Analysis(analysis_settings['analysis'], machine)
    if meshing:
        created = analysis.create_model()
        if created:
            meshed = analysis.mesh_model()
            if not meshed:
                print('Not Meshed')
                return False
        else:
            print ('Not Created')
            return False
    if solving:
        solved = analysis.solve_model()
        if not solved:
            print('Not Solved')
            return False

    if postprocessing:
        res = analysis.post_processing()

        if plot:
            import matplotlib.pyplot as plt
            plt.figure(1)
            plt.title('Air Gap Flux Density')
            plt.subplot(211)
            plt.plot(res.nl_Bg_theta, res.nl_Bg_r[0], label='No Load')
            #plt.plot(res.nl_Bg_theta, res.ol_Bg_r, label='On Load')
            plt.legend()
            plt.subplot(212)
            plt.plot(res.nl_Bg_theta, res.nl_Bg_t[0], label='No Load')
            #plt.plot(res.nl_Bg_theta, res.ol_Bg_t, label='On Load')

            plt.figure(2)
            plt.plot(res.cogging_torque_mst_x, res.cogging_torque_mst_y, '-o', label='MST')
            plt.plot(res.cogging_torque_x, res.cogging_torque_y, '-o', label='AKKIO')
            #plt.plot(res.cogging_torque_2_x, res.cogging_torque_2_y, label='AG')
            plt.legend()
            plt.show()
    else:
        print ('Something went wrong')
        return False

    finish = time.clock()

    log_msg = "[AA_SPM] Total time is %fsec" % (finish - start1)
    logging.info(log_msg)


    logging.shutdown()
    return True


if __name__ == '__main__':
    sys.exit(main())