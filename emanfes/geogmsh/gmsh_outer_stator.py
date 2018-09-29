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
        if rotating_machine.get_machine_type() == "SPM":
            self.Ror = rotating_machine.rotor.outer_radius + rotating_machine.rotor.magnets[0].length
        else:
            self.Ror = rotating_machine.rotor.outer_radius
        self.Ns = rotating_machine.stator.slots_number
        self.conn_matrix = rotating_machine.stator.winding.conn_matrix
        self.LayersType = rotating_machine.stator.winding.conductors.get_type()

        self.slot_opening_points, self.slot_opening_lines = rotating_machine.stator.get_slot_opening_geometry()
        self.slot_opening_mesh_size = self._get_mesh_size( self.slot_opening_points, div=2.0)

        self.slot_wedge_points, self.slot_wedge_lines = rotating_machine.stator.get_slot_wedge_geometry()
        self.slot_wedge_mesh_size = self._get_mesh_size(self.slot_wedge_points, div=2.0)
        if self.slot_wedge_mesh_size == 0:
            self.slot_wedge_mesh_size = self.slot_opening_mesh_size

        self.conductors_list = rotating_machine.stator.get_conductors_geometry()
        self.conductors_mesh_size = self._get_mesh_size(self.conductors_list[0][0], div=4.0)

        self.coil_area_points, self.coil_area_lines = rotating_machine.stator.get_coil_area_geometry()
        self.coil_area_mesh_size = self._get_mesh_size(self.coil_area_points, div=2.0)
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
        self.toothtip_mesh_size = self._get_mesh_size(self.toothtip_points, div=10.0)
        if self.toothtip_mesh_size == 0:
            self.toothtip_mesh_size = self.slot_opening_mesh_size

        airgap_lenght = (self.Sir - self.Ror)
        airgap_radius_1 = self.Ror + (2.0/3.0) * airgap_lenght
        airgap_radius_2 = self.Ror + (1.0/3.0) * airgap_lenght
        self.stator_airgap_points, self.stator_airgap_lines = rotating_machine.stator.get_stator_airgap_geometry( airgap_radius_1 )
        self.stator_airgap_mesh_size = self._get_mesh_size(self.stator_airgap_points, div=40.0)
        if self.stator_airgap_mesh_size == 0:
            self.stator_airgap_mesh_size = self.slot_opening_mesh_size / 2.0

        self.sliding_airgap_points, self.sliding_airgap_lines = rotating_machine.stator.get_sliding_airgap_geometry( airgap_radius_2)
        self.sliding_airgap_mesh_size = self._get_mesh_size(self.sliding_airgap_points, div=40.0)
        if self.sliding_airgap_mesh_size == 0:
            self.sliding_airgap_mesh_size = self.slot_opening_mesh_size / 2.0

        self.outer_stator_boundary = rotating_machine.stator.get_outer_stator_boundary()
        self.stator_master_boundary = rotating_machine.stator.get_master_boundary()
        self.stator_sliding_boundary = rotating_machine.stator.get_sliding_boundary()
        self.stator_airgap_arc = rotating_machine.stator.get_airgap_arc()

        self.pp = rotating_machine.rotor.pp
        self.nCopies = int(self.Ns / GCD(self.Ns, 2 * self.pp))

    def get_fractions_drawn(self):
        return int(self.Ns / self.nCopies)

    def _get_mesh_size(self, points, div=1.0):
        if points is None:
            return 0
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
        if points is None and lines is None:
            return None

        if points is not None:
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
        surface.append(np.array([[2, model.geo.addPlaneSurface([line_loop])]], dtype=np.int32))
        return surface

    def _get_surface_with_holes(self, lines, holes, model):
        wire = []
        for line in lines:
            l = int(line)
            lp = lines[line]
            if len(lp) == 1:
                pass
            elif len(lp) == 2:
                p1 = lp[0]
                p2 = lp[1]
                print(p1, p2, l)
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
        surface = []
        surface.append(np.array([[2, model.geo.addPlaneSurface(surf_and_holes)]], dtype=np.int32))
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

    def _copy_and_rotate_coil_surfaces(self, surface, conn_matrix, amount, pitch, model):
        slots_a_plus = conn_matrix[0,:] > 0
        slots_a_minus = conn_matrix[0,:] < 0
        slots_b_plus = conn_matrix[1, :] > 0
        slots_b_minus = conn_matrix[1, :] < 0
        slots_c_plus = conn_matrix[2, :] > 0
        slots_c_minus = conn_matrix[2, :] < 0
        tmp_surface = surface[0][0]
        a_plus_surf = []
        a_minus_surf = []
        b_plus_surf = []
        b_minus_surf = []
        c_plus_surf = []
        c_minus_surf = []
        for i in range(1, amount):
            if slots_a_plus[i - 1]:
                a_plus_surf.append(tmp_surface)
            elif slots_a_minus[i - 1]:
                a_minus_surf.append(tmp_surface)
            elif slots_b_plus[i - 1]:
                b_plus_surf.append(tmp_surface)
            elif slots_b_minus[i - 1]:
                b_minus_surf.append(tmp_surface)
            elif slots_c_plus[i - 1]:
                c_plus_surf.append(tmp_surface)
            elif slots_c_minus[i - 1]:
                c_minus_surf.append(tmp_surface)

            tmp_surface = model.geo.copy(tmp_surface)
            model.geo.rotate(tmp_surface, 0, 0, 0, 0, 0, 1, pitch)

        if slots_a_plus[i]:
            a_plus_surf.append(tmp_surface)
        elif slots_a_minus[i]:
            a_minus_surf.append(tmp_surface)
        elif slots_b_plus[i]:
            b_plus_surf.append(tmp_surface)
        elif slots_b_minus[i]:
            b_minus_surf.append(tmp_surface)
        elif slots_c_plus[i]:
            c_plus_surf.append(tmp_surface)
        elif slots_c_minus[i]:
            c_minus_surf.append(tmp_surface)

        coil_surfaces = [a_plus_surf, a_minus_surf,
                         b_plus_surf, b_minus_surf,
                         c_plus_surf, c_minus_surf]

        return coil_surfaces


    def _create_physical_coils(self, coil_surfaces, model):
        a_plus_surf = coil_surfaces[0]
        a_minus_surf = coil_surfaces[1]
        b_plus_surf = coil_surfaces[2]
        b_minus_surf = coil_surfaces[3]
        c_plus_surf = coil_surfaces[4]
        c_minus_surf = coil_surfaces[5]

        if len(a_plus_surf) > 0:
            group = [surf[0][1] for surf in a_plus_surf]
            model.addPhysicalGroup(2, group, 220)
            model.setPhysicalName(2, 220, "A_PLUS")
        if len(a_minus_surf) > 0:
            group = [surf[0][1] for surf in a_minus_surf]
            model.addPhysicalGroup(2, group, 221)
            model.setPhysicalName(2, 221, "A_MINUS")
        if len(b_plus_surf) > 0:
            group = [surf[0][1] for surf in b_plus_surf]
            model.addPhysicalGroup(2, group, 222)
            model.setPhysicalName(2, 222, "B_PLUS")
        if len(b_minus_surf) > 0:
            group = [surf[0][1] for surf in b_minus_surf]
            model.addPhysicalGroup(2, group, 223)
            model.setPhysicalName(2, 223, "B_MINUS")
        if len(c_plus_surf) > 0:
            group = [surf[0][1] for surf in c_plus_surf]
            model.addPhysicalGroup(2, group, 224)
            model.setPhysicalName(2, 224, "C_PLUS")
        if len(c_minus_surf) > 0:
            group = [surf[0][1] for surf in c_minus_surf]
            model.addPhysicalGroup(2, group, 225)
            model.setPhysicalName(2, 225, "C_MINUS")


    def _merge_copy_and_rotate_coil_surfaces(self, surface, surface_mirror, conn_matrix, amount, pitch, model):
        slots_a_plus = conn_matrix[0,:] > 0
        slots_a_minus = conn_matrix[0,:] < 0
        slots_b_plus = conn_matrix[1, :] > 0
        slots_b_minus = conn_matrix[1, :] < 0
        slots_c_plus = conn_matrix[2, :] > 0
        slots_c_minus = conn_matrix[2, :] < 0
        tmp_surface = surface[0][0]
        tmp_surface_mirror = surface_mirror[0][0]
        a_plus_surf = []
        a_minus_surf = []
        b_plus_surf = []
        b_minus_surf = []
        c_plus_surf = []
        c_minus_surf = []
        for i in range(1, amount):
            if slots_a_plus[i - 1]:
                a_plus_surf.append(tmp_surface)
                a_plus_surf.append(tmp_surface_mirror)
            elif slots_a_minus[i - 1]:
                a_minus_surf.append(tmp_surface)
                a_minus_surf.append(tmp_surface_mirror)
            elif slots_b_plus[i - 1]:
                b_plus_surf.append(tmp_surface)
                b_plus_surf.append(tmp_surface_mirror)
            elif slots_b_minus[i - 1]:
                b_minus_surf.append(tmp_surface)
                b_minus_surf.append(tmp_surface_mirror)
            elif slots_c_plus[i - 1]:
                c_plus_surf.append(tmp_surface)
                c_plus_surf.append(tmp_surface_mirror)
            elif slots_c_minus[i - 1]:
                c_minus_surf.append(tmp_surface)
                c_minus_surf.append(tmp_surface_mirror)

            tmp_surface = model.geo.copy(tmp_surface)
            model.geo.rotate(tmp_surface, 0, 0, 0, 0, 0, 1, pitch)
            tmp_surface_mirror = model.geo.copy(tmp_surface_mirror)
            model.geo.rotate(tmp_surface_mirror, 0, 0, 0, 0, 0, 1, pitch)

        if slots_a_plus[i]:
            a_plus_surf.append(tmp_surface)
            a_plus_surf.append(tmp_surface_mirror)
        elif slots_a_minus[i]:
            a_minus_surf.append(tmp_surface)
            a_minus_surf.append(tmp_surface_mirror)
        elif slots_b_plus[i]:
            b_plus_surf.append(tmp_surface)
            b_plus_surf.append(tmp_surface_mirror)
        elif slots_b_minus[i]:
            b_minus_surf.append(tmp_surface)
            b_minus_surf.append(tmp_surface_mirror)
        elif slots_c_plus[i]:
            c_plus_surf.append(tmp_surface)
            c_plus_surf.append(tmp_surface_mirror)
        elif slots_c_minus[i]:
            c_minus_surf.append(tmp_surface)
            c_minus_surf.append(tmp_surface_mirror)

        coil_surfaces = [a_plus_surf, a_minus_surf,
                         b_plus_surf, b_minus_surf,
                         c_plus_surf, c_minus_surf]

        return coil_surfaces



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
                                                 0, 0, 0, model, self.slot_opening_mesh_size)
        slot_wedge_surface = self._get_surface( self.slot_wedge_points, self.slot_wedge_lines,
                                               0, 0, 0, model, self.slot_wedge_mesh_size)



        conductor_surface = []
        for i in range(0,len(self.conductors_list)):
            conductor_surface.append( self._get_surface( self.conductors_list[i][0], self.conductors_list[i][1],
                                               0, 0, 0, model, self.conductors_mesh_size) )



        backiron_surface = self._get_surface(self.backiron_points, self.backiron_lines,
                                             0, 0, 0, model, self.backiron_mesh_size)



        tooth_surface = self._get_surface(self.tooth_points, self.tooth_lines,
                                            0, 0, 0, model, self.tooth_mesh_size)

        coil_area_surface = self._get_surface_with_holes(self.coil_area_lines, conductor_surface, model)


        toothtip_surface = self._get_surface(self.toothtip_points, self.toothtip_lines,
                                            0, 0, 0, model, self.toothtip_mesh_size)



        stator_airgap_surface = self._get_surface(self.stator_airgap_points, self.stator_airgap_lines,
                                             0, 0, 0, model, self.stator_airgap_mesh_size)
        sliding_airgap_surface = self._get_surface(self.sliding_airgap_points, self.sliding_airgap_lines,
                                                  0, 0, 0, model, self.sliding_airgap_mesh_size)


        slot_opening_surface_mirror = self._get_surface_mirror(slot_opening_surface[-1], model)
        conductor_surface_mirror = []
        for i in range(0,len(self.conductors_list)):
            conductor_surface_mirror.append( self._get_surface_mirror( conductor_surface[i], model ) )

        if slot_wedge_surface is not None:
            slot_wedge_surface_mirror = self._get_surface_mirror(slot_wedge_surface[-1], model)

        backiron_surface_mirror = self._get_surface_mirror(backiron_surface[-1], model)
        tooth_surface_mirror = self._get_surface_mirror(tooth_surface[-1], model)
        coil_area_surface_mirror = self._get_surface_mirror( coil_area_surface[-1], model )
        toothtip_surface_mirror = self._get_surface_mirror(toothtip_surface[-1], model)
        stator_airgap_surface_mirror = self._get_surface_mirror(stator_airgap_surface[-1], model)
        sliding_airgap_surface_mirror = self._get_surface_mirror(sliding_airgap_surface[-1], model)

        slot_pitch = 2 * PI / self.Ns

        self._get_boundary(self.outer_stator_boundary, self.nCopies, slot_pitch, 201, "OUTER_STATOR_BOUNDARY", model)
        self._get_master_slave_boundary(self.stator_master_boundary, GCD(self.Ns, 2 * self.pp), [202,203], ["STATOR_MASTER_BOUNDARY","STATOR_SLAVE_BOUNDARY"], model)
        self._get_boundary(self.stator_airgap_arc, self.nCopies, slot_pitch, 204, "STATOR_AIRGAP_ARC_BOUNDARY", model)
        self._get_boundary(self.stator_sliding_boundary, self.nCopies, slot_pitch, 205, "STATOR_SLIDING_BOUNDARY", model)

        # Delete duplicated instances before building surfaces
        gmsh.option.setNumber("Geometry.AutoCoherence", 1)

        self._copy_and_rotate_surfaces(slot_opening_surface, slot_opening_surface_mirror, self.nCopies, slot_pitch,
                                       206, "SLOT_OPENINGS", model)
        if slot_wedge_surface is not None:
            self._copy_and_rotate_surfaces(slot_wedge_surface, slot_wedge_surface_mirror, self.nCopies, slot_pitch,
                                       207, "SLOT_WEDGES", model)


        if self.LayersType == 'OneLayer':
            coil_surfaces = self._merge_copy_and_rotate_coil_surfaces(conductor_surface, conductor_surface_mirror, self.conn_matrix[:3,:],
                                                      self.nCopies, slot_pitch, model)
            coil_mirror_surfaces = []
        elif self.LayersType == 'DualLayer_SideBySide':
            coil_surfaces = self._copy_and_rotate_coil_surfaces(conductor_surface, self.conn_matrix[3:, :],
                                                                self.nCopies, slot_pitch, model)
            coil_mirror_surfaces = self._copy_and_rotate_coil_surfaces(conductor_surface_mirror, self.conn_matrix[:3, :],
                                                                self.nCopies, slot_pitch, model)


        elif self.LayersType == 'DualLayer_TopBottom':
            coil_surfaces = self._merge_copy_and_rotate_coil_surfaces([conductor_surface[0]], [conductor_surface_mirror[0]],
                                                      self.conn_matrix[:3, :], self.nCopies, slot_pitch, model)
            coil_mirror_surfaces = self._merge_copy_and_rotate_coil_surfaces([conductor_surface[1]], [conductor_surface_mirror[1]],
                                                    self.conn_matrix[3:, :], self.nCopies, slot_pitch, model)

        for i in range(0, 6):
            coil_surfaces[i].extend(coil_mirror_surfaces[i])

        self._create_physical_coils(coil_surfaces, model)

        self._copy_and_rotate_surfaces(coil_area_surface, coil_area_surface_mirror, self.nCopies, slot_pitch,
                                       208, "COIL_AREAS", model)
        self._copy_and_rotate_surfaces(backiron_surface, backiron_surface_mirror, self.nCopies, slot_pitch,
                                       209, "BACKIRONS", model)
        self._copy_and_rotate_surfaces(tooth_surface, tooth_surface_mirror, self.nCopies, slot_pitch,
                                       210, "TEETH", model)
        self._copy_and_rotate_surfaces(toothtip_surface, toothtip_surface_mirror, self.nCopies, slot_pitch,
                                       211, "TOOTHTIPS", model)
        self._copy_and_rotate_surfaces(stator_airgap_surface, stator_airgap_surface_mirror, self.nCopies, slot_pitch,
                                       212, "STATOR_AIRGAPS", model)
        self._copy_and_rotate_surfaces(sliding_airgap_surface, sliding_airgap_surface_mirror, self.nCopies, slot_pitch,
                                       213, "SLIDING_AIRGAPS", model)


        factory.synchronize()
        #gmsh.fltk.run()
        model.mesh.generate(2)
        #gmsh.fltk.run()
        gmsh.write("stator.msh")
        gmsh.finalize()

        return True



