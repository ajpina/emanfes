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
    Creates Gmsh Inner Rotor.
"""

# ==========================================================================
# Program:   gmsh_spm_inner_rotor.py
# Author:    ajpina
# Date:      12/23/17
# Version:   0.1.1
#
# Revision History:
#      Date     Version  Author    Description
#  - 12/23/17:  0.1.1              Uses Gmsh python API
#
# ==========================================================================

import gmsh

from emanfes.misc.constants import *


class GmshIPMInnerRotor:

    def __init__(self, simulation, rotating_machine):
        self.Sir = rotating_machine.stator.inner_radius
        self.Rir = rotating_machine.rotor.inner_radius
        self.Ror = rotating_machine.rotor.outer_radius
        self.Ns = rotating_machine.stator.slots_number
        self.pp = rotating_machine.rotor.pp
        self.nCopies = int( 2 * self.pp / GCD(self.Ns, 2 * self.pp) )

        self.shaft_points, self.shaft_lines = rotating_machine.rotor.get_shaft_geometry()
        self.shaft_mesh_size = self._get_mesh_size(self.shaft_points, div=2.0)

        self.magnet_points, self.magnet_lines = rotating_machine.rotor.get_magnet_geometry()
        self.magnet_mesh_size = self._get_mesh_size(self.magnet_points, div=10.0)
        if self.magnet_mesh_size == 0:
            self.magnet_mesh_size = self.shaft_mesh_size / 2.0

        self.pocket_points, self.pocket_lines = rotating_machine.rotor.get_pocket_geometry()
        self.pocket_mesh_size = self._get_mesh_size(self.pocket_points, div=10.0)
        if self.pocket_mesh_size == 0:
            self.pocket_mesh_size = self.magnet_mesh_size / 2.0

        self.rotor_core_points, self.rotor_core_lines = rotating_machine.rotor.get_core_geometry()
        self.rotor_core_mesh_size = self._get_mesh_size(self.rotor_core_points, div=10.0)
        if self.rotor_core_mesh_size == 0:
            self.rotor_core_mesh_size = self.shaft_mesh_size / 2.0

        airgap_lenght = (self.Sir - self.Ror)
        airgap_radius_1 = self.Ror + (2.0 / 3.0) * airgap_lenght
        airgap_radius_2 = self.Ror + (1.0 / 3.0) * airgap_lenght
        self.rotor_airgap_points, self.rotor_airgap_lines = rotating_machine.rotor.get_rotor_airgap_geometry( airgap_radius_2)
        self.rotor_airgap_mesh_size = self._get_mesh_size(self.rotor_airgap_points, div=40.0)
        if self.rotor_airgap_mesh_size == 0:
            self.rotor_airgap_mesh_size = self.magnet_mesh_size / 20.0

        self.rotor_master_boundary = rotating_machine.rotor.get_master_boundary()
        self.rotor_sliding_boundary = rotating_machine.rotor.get_sliding_boundary()


    def get_fractions_drawn(self):
        return int(2 * self.pp / self.nCopies)

    def _get_mesh_size(self, points, div=1.0):
        x_max = -1e20
        x_min = 1e20
        y_max = -1e20
        y_min = 1e20
        for p in points:
            x = points[p][0]
            y = points[p][1]
            if x > x_max:
                x_max = x
            if x < x_min:
                x_min = x
            if y > y_max:
                y_max = y
            if y < y_min:
                y_min = y
        mesh_size_x = (x_max - x_min) / div
        mesh_size_y = (y_max - y_min) / div
        if mesh_size_x > mesh_size_y:
            return mesh_size_x
        else:
            return mesh_size_y


    def _get_surface(self, points, lines, dx, dy, dz, model, mesh_size=1):
        for point in points:
            p = int(point)
            x = points[point][0] + dx
            y = points[point][1] + dy
            z = points[point][2] + dz
            model.geo.addPoint(x, y, z, meshSize=mesh_size, tag=p )


        wire = []
        for line in lines:
            l = int(line)
            lp = lines[line]
            if len(lp) == 1:
                pass
            elif len(lp) == 2:
                p1 = lp[0]
                p2 = lp[1]
                model.geo.addLine(p1, p2, l)
            elif len(lp) == 3:
                p1 = lp[0]
                p2 = lp[1]
                p3 = lp[2]
                model.geo.addCircleArc(p1, p2, p3, l)
            else:
                return False
            wire.append(l)


        line_loop = model.geo.addCurveLoop(wire)
        surface = []
        surface.append(np.array([[2, model.geo.addPlaneSurface([line_loop])]]))
        return surface


    def _get_surface_with_holes(self, points, lines, dx, dy, dz, holes, model, mesh_size=1):
        for point in points:
            p = int(point)
            x = points[point][0] + dx
            y = points[point][1] + dy
            z = points[point][2] + dz
            model.geo.addPoint(x, y, z, meshSize=mesh_size, tag=p)

        wire = []
        for line in lines:
            l = int(line)
            lp = lines[line]
            if len(lp) == 1:
                pass
            elif len(lp) == 2:
                p1 = lp[0]
                p2 = lp[1]
                model.geo.addLine(p1, p2, l)
            elif len(lp) == 3:
                p1 = lp[0]
                p2 = lp[1]
                p3 = lp[2]
                model.geo.addCircleArc(p1, p2, p3, l)
            else:
                return False
            wire.append(l)

        line_loop = model.geo.addCurveLoop(wire)
        surf_and_holes = [surf[0][0][1] for surf in holes]
        surf_and_holes.insert(0, line_loop)
        print("surface and holes",surf_and_holes)
        surface = []
        surface.append(np.array([[2, model.geo.addPlaneSurface(surf_and_holes)]], dtype=np.int32))
        print(surface)
        return surface


    def _get_surface_mirror(self, surface, model):
        surface_mirror = []
        surface_mirror.append(model.geo.copy(surface))
        model.geo.symmetry(surface_mirror, 0, 1, 0, 0)
        return surface_mirror


    def _copy_and_rotate_surfaces(self, surface, surface_mirror, amount, pitch, id, name, model):
        for i in range(1, amount):
            surface.append(model.geo.copy(surface[-1]))
            model.geo.rotate( surface[-1], 0, 0, 0, 0, 0, 1, pitch)
            surface_mirror.append( model.geo.copy(surface_mirror[-1]))
            model.geo.rotate(surface_mirror[-1], 0, 0, 0, 0, 0, 1, pitch)

        group = [surf[0][1] for surf in surface ]
        group.extend( [surf[0][1] for surf in surface_mirror] )
        model.addPhysicalGroup(2, group, id)
        model.setPhysicalName(2, id, name)

    def _rotate_surfaces_with_new_name(self, surface, surface_mirror, amount, pitch, id, name, model):
        group = [surface[0][0][1],  surface_mirror[0][0][1]]
        model.addPhysicalGroup(2, group, id[0])
        model.setPhysicalName(2, id[0], name[0])
        for i in range(1, amount):
            new_surface = model.geo.copy(surface[-1])
            model.geo.rotate( new_surface[-1], 0, 0, 0, 0, 0, 1, i*pitch)
            new_surface_mirror = model.geo.copy(surface_mirror[-1])
            model.geo.rotate(new_surface_mirror[-1], 0, 0, 0, 0, 0, 1, i*pitch)
            group = [new_surface[0][1], new_surface_mirror[0][1]]
            model.addPhysicalGroup(2, group, id[i])
            model.setPhysicalName(2, id[i], name[i])

    def _get_boundary(self, lines, amount, pitch, id, name, model):
        initial_lines = [np.array([[1, l]]) for l in lines]
        lines_mirror = []
        lines_mirror.append( model.geo.copy(initial_lines))
        model.geo.symmetry( lines_mirror, 0, 1, 0, 0)
        for i in range(1, amount):
            initial_lines.append(model.geo.copy(initial_lines[-1]))
            model.geo.rotate( initial_lines[-1], 0, 0, 0, 0, 0, 1, pitch)
            lines_mirror.append( model.geo.copy( lines_mirror[-1] ))
            model.geo.rotate(lines_mirror[-1], 0, 0, 0, 0, 0, 1, pitch)

        group = [line[0][1] for line in initial_lines ]
        group.extend( [line[0][1] for line in lines_mirror] )
        model.addPhysicalGroup(1, group, id)
        model.setPhysicalName(1, id, name)
        

    def _get_master_slave_boundary(self, lines, periodicity, id, name, model):
        angle = 2 * PI / periodicity
        master_lines = [np.array([[1, l]]) for l in lines]
        slave_lines = model.geo.copy( master_lines)
        model.geo.rotate( slave_lines, 0, 0, 0, 0, 0, 1, angle)
        master_group = [line[0][1] for line in master_lines]
        model.addPhysicalGroup(1, master_group, id[0])
        model.setPhysicalName(1, id[0], name[0])
        slave_group = [line[1] for line in slave_lines]
        model.addPhysicalGroup(1, slave_group, id[1])
        model.setPhysicalName(1, id[1], name[1])



    def create(self):
        gmsh.initialize('', False)
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("Geometry.AutoCoherence", 0)
        gmsh.option.setNumber("Mesh.Algorithm", 5)
        model = gmsh.model
        factory = model.geo
        model.add("rotor")



        shaft_surface = self._get_surface( self.shaft_points, self.shaft_lines,
                                                  0, 0, 0, model, self.shaft_mesh_size)
        magnet_surface = self._get_surface( self.magnet_points, self.magnet_lines,
                                                0, 0, 0, model, self.magnet_mesh_size)
        pocket_surface = self._get_surface( self.pocket_points, self.pocket_lines,
                                                0, 0, 0, model, self.pocket_mesh_size)
        rotor_core_surface = self._get_surface_with_holes(self.rotor_core_points, self.rotor_core_lines,
                                               0, 0, 0, [magnet_surface, pocket_surface], model, self.rotor_core_mesh_size)

        rotor_airgap_surface = self._get_surface(self.rotor_airgap_points, self.rotor_airgap_lines,
                                              0, 0, 0, model, self.rotor_airgap_mesh_size)

        shaft_surface_mirror = self._get_surface_mirror(shaft_surface[-1], model)
        magnet_surface_mirror = self._get_surface_mirror( magnet_surface[-1], model )
        pocket_surface_mirror = self._get_surface_mirror( pocket_surface[-1], model )
        rotor_core_surface_mirror = self._get_surface_mirror( rotor_core_surface[-1], model )
        rotor_airgap_surface_mirror = self._get_surface_mirror(rotor_airgap_surface[-1], model)

        pole_pitch = PI / self.pp

        self._get_master_slave_boundary(self.rotor_master_boundary, GCD(self.Ns, 2 * self.pp), [101,102], ["ROTOR_MASTER_BOUNDARY","ROTOR_SLAVE_BOUNDARY"], model)
        self._get_boundary(self.rotor_sliding_boundary, self.nCopies, pole_pitch, 103, "ROTOR_SLIDING_BOUNDARY", model)

        # # Delete duplicated instances before building surfaces
        gmsh.option.setNumber("Geometry.AutoCoherence", 1)
        #
        self._copy_and_rotate_surfaces(shaft_surface, shaft_surface_mirror, self.nCopies, pole_pitch,
                                        104, "SHAFTS", model)

        self._copy_and_rotate_surfaces(rotor_core_surface, rotor_core_surface_mirror, self.nCopies, pole_pitch,
                                        105, "ROTORCORES", model)
        self._copy_and_rotate_surfaces(pocket_surface, pocket_surface_mirror, self.nCopies, pole_pitch,
                                        106, "ROTORPOCKETS", model)
        self._copy_and_rotate_surfaces(rotor_airgap_surface, rotor_airgap_surface_mirror, self.nCopies, pole_pitch,
                                        107, "ROTOR_AIRGAPS", model)
        magnets_id = [108]
        magnets_name = ["MAGNETS1"]
        for i in range(2, self.nCopies + 1):
            magnets_id.append(int(107 + i))
            label = "MAGNETS%d" % i
            magnets_name.append(label)
        self._rotate_surfaces_with_new_name(magnet_surface, magnet_surface_mirror, self.nCopies, pole_pitch,
                                            magnets_id, magnets_name, model)


        factory.synchronize()
        model.mesh.generate(2)
        gmsh.write("rotor.msh")
        #gmsh.fltk.run()
        gmsh.finalize()

        return True



