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
    Creates Gmsh Geometry.
"""

# ==========================================================================
# Program:   geometry_gmsh.py
# Author:    ajpina
# Date:      12/23/17
# Version:   0.1.1
#
# Revision History:
#      Date     Version  Author    Description
#  - 12/23/17:  0.1.1              Uses Gmsh python API
#
# ==========================================================================




class GeometryGmsh:

    def __init__(self, simulation, rotating_machine):
        from emanfes.geogmsh import GmshOuterStator
        self.stator = GmshOuterStator(simulation, rotating_machine)
        if rotating_machine.get_machine_type() == "SPM":
            from emanfes.geogmsh import GmshSPMInnerRotor
            self.rotor = GmshSPMInnerRotor(simulation, rotating_machine)
        elif rotating_machine.get_machine_type() == "IPM":
            from emanfes.geogmsh import GmshIPMInnerRotor
            self.rotor = GmshIPMInnerRotor(simulation, rotating_machine)
        else:
            from emanfes.geogmsh import GmshIPMInnerRotor
            self.rotor = GmshIPMInnerRotor(simulation, rotating_machine)

    def create(self):
        sf = self.stator.create()
        rf = self.rotor.create()
        return sf and rf

    def get_fractions_drawn(self):
        sf = self.stator.get_fractions_drawn()
        rf = self.rotor.get_fractions_drawn()
        if sf == rf:
            return sf
        else:
            return 1.0


    def mesh(self):
        pass


