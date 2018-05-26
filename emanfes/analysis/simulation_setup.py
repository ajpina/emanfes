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



class Simulation:

    def __init__(self, analysis_settings):
        self.solver = analysis_settings['solver']
        self.solve_bemf = analysis_settings['noload'].get('bemf', False)
        self.noload_speed = analysis_settings['noload'].get('speed', 1000)
        self.solve_cogging = analysis_settings['noload'].get('cogging', False)
        self.solve_noload_pressure = analysis_settings['noload'].get('pressure', False)
        self.solve_ripple = analysis_settings['load'].get('ripple', False)
        self.load_speed = analysis_settings['load'].get('speed', 1000)
        self.load_current = analysis_settings['load'].get('current', 100)
        self.load_voltage = analysis_settings['load'].get('voltage', None)
        self.load_gamma = analysis_settings['load'].get('gamma', 0)
        self.solve_load_losses = analysis_settings['load'].get('losses', False)
        self.solve_load_pressure = analysis_settings['load'].get('pressure', False)
        self.inductance_max_current = analysis_settings['inductance'].get('max_current', 10)
        self.inductance_steps = analysis_settings['inductance'].get('steps', 5)
        self.torque_vs_load_max_current = analysis_settings['torque_vs_load'].get('max_current', 100)
        self.torque_vs_load_max_voltage = analysis_settings['torque_vs_load'].get('max_voltage', 20)
        self.torque_vs_load_steps = analysis_settings['torque_vs_load'].get('steps', 5)
        self.torque_vs_load_gamma = analysis_settings['torque_vs_load'].get('gamma', 0.0)
        self.torque_vs_speed_max_speed = analysis_settings['torque_vs_speed'].get('max_speed', 5000)
        self.torque_vs_speed_max_power = analysis_settings['torque_vs_speed'].get('max_power', 1000)
        self.torque_vs_speed_max_current = analysis_settings['torque_vs_speed'].get('max_current', 100)
        self.torque_vs_speed_max_voltage = analysis_settings['torque_vs_speed'].get('max_voltage', 20)
        self.torque_vs_speed_init_gamma = analysis_settings['torque_vs_speed'].get('init_gamma', 0.0)
        self.torque_vs_speed_with_FW = analysis_settings['torque_vs_speed'].get('flux_weakening', False)
        self.solve_efficiency_map = analysis_settings['torque_vs_speed'].get('efficiency_map', False)
        self.solve_winding_function = analysis_settings['winding'].get('winding_function', False)
        self.solve_winding_harmonics = analysis_settings['winding'].get('winding_harmonics', False)
        self.solve_winding_factors = analysis_settings['winding'].get('winding_factors', False)





