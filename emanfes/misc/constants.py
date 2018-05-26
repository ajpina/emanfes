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

import numpy as np
import fractions

EMANFES_VERSION__ = 0.1

LOG_CRITICAL = 0
LOG_ERROR = 1
LOG_WARN = 2
LOG_INFO = 3
LOG_ALL = 4


MU0 = np.pi*4e-7
DEG2RAD = np.pi / 180.0
RAD2DEG = 180.0 / np.pi
PI = np.pi
EL_STEPS = 90
THETA_e_DEG = np.linspace(0, 360, EL_STEPS)
THETA_e_RAD = THETA_e_DEG * DEG2RAD
PI_2by3 = 2.0 * np.pi / 3.0
K_QD = (2.0 / 3.0) * np.array(([[np.sin(THETA_e_DEG * DEG2RAD),
                                np.sin((THETA_e_DEG - 120) * DEG2RAD),
                                np.sin((THETA_e_DEG + 120) * DEG2RAD)],
                               [np.cos(THETA_e_DEG * DEG2RAD),
                                np.cos((THETA_e_DEG - 120) * DEG2RAD),
                                np.cos((THETA_e_DEG + 120) * DEG2RAD)]]))

IDX_BODY_NAME = 0
IDX_BODY_ID = 1
IDX_BODY_EQ = 2
IDX_BODY_MAT = 3
IDX_BODY_FORCE = 4
IDX_BODY_TQ_GRP = 5

BODIES = (  ('SLOT_OPENINGS',   '101',  '1',    '1',    '0',    '0'),
            ('SLOT_WEDGES',     '102',  '1',    '2',    '0',    '0'),
            ('COIL_AREAS',      '103',  '1',    '1',    '0',    '0'),
            ('BACKIRONS',       '104',  '1',    '3',    '0',    '0'),
            ('TEETH',           '105',  '1',    '3',    '0',    '0'),
            ('TOOTHTIPS',       '106',  '1',    '3',    '0',    '0'),
            ('STATOR_AIRGAPS',  '107',  '1',    '1',    '0',    '0'),
            ('SHAFTS',          '201',  '1',    '1',    '1',    '1'),
            ('ROTORCORES',      '202',  '1',    '4',    '1',    '1'),
            ('ROTOR_AIRGAPS',   '203',  '1',    '1',    '1',    '0'),
            ('MAGNETS1',        '210',  '1',    '5',    '1',    '1'),
            ('MAGNETS2',        '211',  '1',    '6',    '1',    '1'),
            ('MAGNETS3',        '212',  '1',    '7',    '1',    '1'),
            ('MAGNETS4',        '213',  '1',    '8',    '1',    '1'),
            ('MAGNETS5',        '214',  '1',    '9',    '1',    '1'),
            ('MAGNETS6',        '215',  '1',    '10',   '1',    '1'),
            ('MAGNETS7',        '216',  '1',    '11',   '1',    '1'),
            ('MAGNETS8',        '217',  '1',    '12',   '1',    '1'),
            ('MAGNETS9',        '218',  '1',    '13',   '1',    '1'),
            ('MAGNETS10',       '219',  '1',    '14',   '1',    '1'),
          )


def LCM(a,b):
    return abs(a * b) / fractions.gcd(a, b) if a and b else 0

def GCD(a,b):
    return fractions.gcd(a, b)

