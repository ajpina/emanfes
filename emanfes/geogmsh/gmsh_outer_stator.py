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
    Creates Gmsh Outer Stator.
"""

# ==========================================================================
# Program:   gmsh_outer_stator.py
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


class GmshOuterStator:

    def __init__(self, simulation, rotating_machine):
        self.Sir = rotating_machine.stator.inner_radius
        self.Sor = rotating_machine.stator.outer_radius
        self.Ror = rotating_machine.rotor.outer_radius + rotating_machine.rotor.magnets[0].length
        self.Ns = rotating_machine.stator.slots_number

        self.slot_opening_points, self.slot_opening_lines = rotating_machine.stator.get_slot_opening_geometry()
        self.slot_opening_mesh_size = self._get_mesh_size( self.slot_opening_points, div=2.0)

        self.slot_wedge_points, self.slot_wedge_lines = rotating_machine.stator.get_slot_wedge_geometry()
        self.slot_wedge_mesh_size = self._get_mesh_size(self.slot_wedge_points, div=2.0)
        if self.slot_wedge_mesh_size == 0:
            self.slot_wedge_mesh_size = self.slot_opening_mesh_size

        self.coil_area_points, self.coil_area_lines = rotating_machine.stator.get_coil_area_geometry()
        self.coil_area_mesh_size = self._get_mesh_size(self.coil_area_points, div=5.0)
        if self.coil_area_mesh_size == 0:
            self.coil_area_mesh_size = self.slot_wedge_mesh_size

        self.backiron_points, self.backiron_lines = rotating_machine.stator.get_backiron_geometry()
        self.backiron_mesh_size = self._get_mesh_size(self.backiron_points, div=5.0)
        if self.backiron_mesh_size == 0:
            self.backiron_mesh_size = self.coil_area_mesh_size

        self.tooth_points, self.tooth_lines = rotating_machine.stator.get_tooth_geometry()
        self.tooth_mesh_size = self._get_mesh_size(self.tooth_points, div=5.0)
        if self.tooth_mesh_size == 0:
            self.tooth_mesh_size = self.backiron_mesh_size

        self.toothtip_points, self.toothtip_lines = rotating_machine.stator.get_toothtip_geometry()
        self.toothtip_mesh_size = self._get_mesh_size(self.toothtip_points, div=5.0)
        if self.toothtip_mesh_size == 0:
            self.toothtip_mesh_size = self.tooth_mesh_size

        self.stator_airgap_points, self.stator_airgap_lines = rotating_machine.stator.get_stator_airgap_geometry( (self.Sir + self.Ror) / 2.0)
        self.stator_airgap_mesh_size = self._get_mesh_size(self.stator_airgap_points, div=40.0)
        if self.stator_airgap_mesh_size == 0:
            self.stator_airgap_mesh_size = self.slot_opening_mesh_size / 2.0

        self.outer_stator_boundary = rotating_machine.stator.get_outer_stator_boundary()
        self.stator_master_boundary = rotating_machine.stator.get_master_boundary()
        self.stator_sliding_boundary = rotating_machine.stator.get_sliding_boundary()


        self.pp = rotating_machine.rotor.pp
        self.nCopies = int(self.Ns / GCD(self.Ns, 2 * self.pp))

    def get_fractions_drawn(self):
        return int(self.Ns / self.nCopies)

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
        surface = []
        surface.append(np.array([[2, model.geo.addPlaneSurface([line_loop])]]))
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
        model.add("stator")
        factory.addPoint(0, 0, 0, 1e-1, 1)

        slot_opening_surface = self._get_surface( self.slot_opening_points, self.slot_opening_lines,
                                                 self.Sir, 0, 0, model, self.slot_opening_mesh_size)
        slot_wedge_surface = self._get_surface( self.slot_wedge_points, self.slot_wedge_lines,
                                               self.Sir, 0, 0, model, self.slot_wedge_mesh_size)
        coil_area_surface = self._get_surface(self.coil_area_points, self.coil_area_lines,
                                              self.Sir, 0, 0, model, self.coil_area_mesh_size)
        backiron_surface = self._get_surface(self.backiron_points, self.backiron_lines,
                                             0, 0, 0, model, self.backiron_mesh_size)
        tooth_surface = self._get_surface(self.tooth_points, self.tooth_lines,
                                            0, 0, 0, model, self.tooth_mesh_size)
        toothtip_surface = self._get_surface(self.toothtip_points, self.toothtip_lines,
                                            0, 0, 0, model, self.toothtip_mesh_size)
        stator_airgap_surface = self._get_surface(self.stator_airgap_points, self.stator_airgap_lines,
                                             0, 0, 0, model, self.stator_airgap_mesh_size)

        slot_opening_surface_mirror = self._get_surface_mirror(slot_opening_surface[-1], model)
        slot_wedge_surface_mirror = self._get_surface_mirror( slot_wedge_surface[-1], model )
        coil_area_surface_mirror = self._get_surface_mirror( coil_area_surface[-1], model )
        backiron_surface_mirror = self._get_surface_mirror(backiron_surface[-1], model)
        tooth_surface_mirror = self._get_surface_mirror(tooth_surface[-1], model)
        toothtip_surface_mirror = self._get_surface_mirror(toothtip_surface[-1], model)
        stator_airgap_surface_mirror = self._get_surface_mirror(stator_airgap_surface[-1], model)

        slot_pitch = 2 * PI / self.Ns

        self._get_boundary(self.outer_stator_boundary, self.nCopies, slot_pitch, 201, "OUTER_STATOR_BOUNDARY", model)
        self._get_master_slave_boundary(self.stator_master_boundary, GCD(self.Ns, 2 * self.pp), [202,203], ["STATOR_MASTER_BOUNDARY","STATOR_SLAVE_BOUNDARY"], model)
        self._get_boundary(self.stator_sliding_boundary, self.nCopies, slot_pitch, 204, "STATOR_SLIDING_BOUNDARY", model)

        # Delete duplicated instances before building surfaces
        gmsh.option.setNumber("Geometry.AutoCoherence", 1)

        self._copy_and_rotate_surfaces(slot_opening_surface, slot_opening_surface_mirror, self.nCopies, slot_pitch,
                                       205, "SLOT_OPENINGS", model)
        self._copy_and_rotate_surfaces(slot_wedge_surface, slot_wedge_surface_mirror, self.nCopies, slot_pitch,
                                       206, "SLOT_WEDGES", model)
        self._copy_and_rotate_surfaces(coil_area_surface, coil_area_surface_mirror, self.nCopies, slot_pitch,
                                       207, "COIL_AREAS", model)
        self._copy_and_rotate_surfaces(backiron_surface, backiron_surface_mirror, self.nCopies, slot_pitch,
                                       208, "BACKIRONS", model)
        self._copy_and_rotate_surfaces(tooth_surface, tooth_surface_mirror, self.nCopies, slot_pitch,
                                       209, "TEETH", model)
        self._copy_and_rotate_surfaces(toothtip_surface, toothtip_surface_mirror, self.nCopies, slot_pitch,
                                       210, "TOOTHTIPS", model)
        self._copy_and_rotate_surfaces(stator_airgap_surface, stator_airgap_surface_mirror, self.nCopies, slot_pitch,
                                       211, "STATOR_AIRGAPS", model)


        factory.synchronize()
        model.mesh.generate(2)
        gmsh.write("stator.msh")
        gmsh.finalize()



