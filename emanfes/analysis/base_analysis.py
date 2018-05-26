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


class Analysis:

    def __init__(self, analysis_settings, rotating_machine):
        from emanfes.analysis import Simulation
        sim = Simulation( analysis_settings )
        if sim.solver == 'elmer':
            from emanfes.elmer import ElmerSolver
            self.solver_instance = ElmerSolver(sim, rotating_machine)
        elif sim.solver == 'getdp':
            from emanfes.getdp import GetDPSolver
            self.solver_instance = GetDPSolver(sim, rotating_machine)
        else:
            from emanfes.elmer import ElmerSolver
            self.solver_instance = ElmerSolver(sim, rotating_machine)


    def create_model(self):
        return self.solver_instance.create()

    def mesh_model(self):
        return self.solver_instance.mesh()

    def solve_model(self):
        return self.solver_instance.solve()

    def post_processing(self):
        return self.solver_instance.post_processing()




