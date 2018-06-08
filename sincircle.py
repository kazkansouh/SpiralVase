# Copyright (C) 2018 Karim Kanso. All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# nothing in this script is applicable when not __main__
if __name__ != "__main__" :
    exit

import bpy
import bmesh
from math import cos, sin, radians
import sys
from argparse import ArgumentParser, SUPPRESS

argv = sys.argv
while len(argv) > 0 :
    x = argv[0]
    argv = argv[1:]
    if x == "--" :
        break

args = ArgumentParser(prog='blender --python ' + __file__ + ' --',
                      description="Generate Blender models that are based"
                          + " on repeated extrusion, scaling and rotation of "
                          + "a circle. All transformation heavily rely on "
                          + "sinusoids, and as a result can produce a range "
                          + "of vase-like objects that are capable of being 3D"
                          + " printed. To avoid clash with Blender, the "
                          + "argument prefix char is changed from '-' to '+'.",
                      prefix_chars='+')

args.add_argument('++outputstl',
                  type=str,
                  default=SUPPRESS,
                  dest='file',
                  metavar='S',
                  help='Output stl file name.'
                    + ' [type: %(type)s, default: none]')

args.add_argument('++outputpng',
                  type=str,
                  default=SUPPRESS,
                  dest='png',
                  metavar='S',
                  help='Output png file name.'
                    + ' [type: %(type)s, default: none]')

args.add_argument('++close',
                  action='store_true',
                  dest='close',
                  help='Close Blender when finished.')

args.add_argument('++slices',
                  type=int,
                  default=200,
                  dest='layers',
                  metavar='I',
                  help='Number of slices (or layers) generated in the model.'
                    + ' [type: %(type)s, default: %(default)s]')

args.add_argument('++slice-height',
                  type=float,
                  default=0.2,
                  dest='layer_height',
                  metavar='F',
                  help='Height of each slice.'
                    + ' [type: %(type)s, default: %(default)s]')

args.add_argument('++slice-samples',
                  type=int,
                  default=800,
                  metavar='I',
                  dest='samples',
                  help='Number of samples taken on the edge of each slice.'
                    + ' [type: %(type)s, default: %(default)s]')

args.add_argument('++vase-radius',
                  type=float,
                  default=7,
                  dest='major_radius',
                  metavar='F',
                  help='Base radius of each slice before scalling is applied.'
                    + ' [type: %(type)s, default: %(default)s]')

args.add_argument('++slice-scale-wave',
                  type=float,
                  nargs=3,
                  default=[0,335,0.6],
                  metavar='F',
                  dest='slice_scale',
                  help='Controls the scaling of each slice, when set'
                    + ' to [0 0 1] no scaling is performed. The slice scaling'
                    + ' is calculated by a sine wave running vertically, where'
                    + ' the first and second arguments are used to linearly '
                    + ' interpolate (for each slice) a value in the domain of'
                    + ' the sine function (in degrees). The final argument'
                    + ' defines the amplitude of the sine wave.'
                    + ' [type: %(type)s, default: %(default)s]')

args.add_argument('++slice-rotate-wave',
                  type=float,
                  nargs=3,
                  default=[0,360,30],
                  metavar='F',
                  dest='slice_rotate',
                  help='Controls the rotation of each slice, when set'
                    + ' to [0 0 1] no rotation is performed. The slice rotation'
                    + ' is calculated by a sine wave running vertically, where'
                    + ' the first and second arguments are used to linearly '
                    + ' interpolate (for each slice) a value in the domain of'
                    + ' the sine function (in degrees). The final argument'
                    + ' defines the amplitude of the sine wave.'
                    + ' [type: %(type)s, default: %(default)s]')

args.add_argument('++slice-wave-amplitude',
                  type=float,
                  default=1,
                  metavar='F',
                  dest='minor_radius',
                  help='Each slice starts as a circle, and then has its'
                    + ' edge transformed into a sine wave. This value sets the'
                    + ' amplitude of the sine wave. To have each slice remain'
                    + ' as a circle, set this value to 0.'
                    + ' [type: %(type)s, default: %(default)s]')

args.add_argument('++slice-wave-frequency',
                  type=int,
                  default=12,
                  metavar='I',
                  dest='minor_freq',
                  help='Each slice starts as a circle, and then has its'
                    + ' edge transformed into a sine wave. This value sets the '
                    + ' number of resulting sine waves. Only complete waves'
                    + ' are supported, thus this value must be an integer.'
                    + ' [type: %(type)s, default: %(default)s]')

args.add_argument('++slice-wave-magnitude-wave',
                  type=float,
                  nargs=3,
                  default=[0,90,20],
                  metavar='I',
                  dest='slice_wave',
                  help='Controls the magnitude of the sine wave applied on each'
                    + ' slice by running a second vertical sine wave, that is'
                    + ' multiplied against the wave on the edge of each slice.'
                    + ' This can be used to create a bumpy texture on the vase'
                    + ' or chamfer the base/top. The first two parameters'
                    + ' define the start and stop of the sine wave. E.g. values'
                    + ' of [0, 180, slices] would result in a round top and'
                    + ' bottom with the ridges graduated in and out. The final'
                    + ' parameter is a cut-off (in layers), so that its'
                    + ' possible to chamfer the base of the base into a circle,'
                    + ' i.e. the default value of [0,90,20] will start the base'
                    + ' with a round circle (as the first value is sin(0)=0)'
                    + ' and over the subsequent 20 layers graduate to the'
                    + ' maximum ridges as sin(90)=1.'
                    + ' [type: %(type)s, default: %(default)s]')

A = args.parse_args(argv)

layers = A.layers
layer_height = A.layer_height

# start and end angle for control of the scaling, set both to 0 to
# disable
layer_start_angle = A.slice_scale[0]
layer_end_angle = A.slice_scale[1]
# amplitude of sine wave defined by above start and stop
layer_amplitude = A.slice_scale[2]

# start and end angle for control of the rotation, set both to 0 to
# disable
layer_r_start_angle = A.slice_rotate[0]
layer_r_end_angle = A.slice_rotate[1]
# amout to rotate each layer by (amplitude)
layer_r = A.slice_rotate[2]

# radius of main circle
major_r = A.major_radius
# amplitude of sine wave on main circle
minor_r = A.minor_radius

# number of vertices/samples per layer (in principle)
major_steps = A.samples
# number of sine waves per layer
minor_rate = A.minor_freq

# the radius of minor_r can be mutated using a sine wave that runs
# vertically. it can be used to create a bumpy texture, graduate the
# minor_r in/out from the ends. these control the start and end angles
# of the sine wave.
minor_r_start = A.slice_wave[0]
minor_r_end = A.slice_wave[1]

# minor_r_cutout is used in conjunction with minor_r_start/end to
# limit the effect of the sine wave, so that any layer number above
# the value f minor_r_cutout will use minor_r_end value. this can be
# used to create a chamfer at the base.
minor_r_cutout = A.slice_wave[2]


def drange(start, stop, step):
    "range that supports floats"
    r = start
    while r < stop:
        yield r
        r += step

scene = bpy.context.scene

bpy.ops.object.mode_set(mode='OBJECT')

# delete objects, clean up ....
print("preparing environment")
for i in bpy.data.objects :
    i.select = True
    bpy.ops.object.delete()

# add camera
bpy.ops.object.camera_add()
scene.camera = bpy.context.active_object

# setup camera
scene.render.resolution_x = 1024
scene.render.resolution_y = 768
scene.camera.data.lens_unit = 'FOV'
scene.camera.data.angle = radians(10)
scene.camera.data.clip_end = 4000
scene.camera.rotation_euler[0] = radians(80)
scene.camera.rotation_euler[1] = 0
scene.camera.rotation_euler[2] = 0

# add lamp
bpy.ops.object.lamp_add(type='SUN')
lamp = bpy.context.active_object
lamp.data.color = (0.228546, 0.271841, 1) # light blue
lamp.rotation_euler[0] = scene.camera.rotation_euler[0]
lamp.rotation_euler[1] = scene.camera.rotation_euler[1]
lamp.rotation_euler[2] = scene.camera.rotation_euler[2]

print("building object")
mesh = bpy.data.meshes.new("mesh")  # add a new mesh
# add a new object using the mesh
obj = bpy.data.objects.new("SpiralVase", mesh)

scene.objects.link(obj)  # put the object into the scene (link)
scene.objects.active = obj  # set as the active object in the scene
obj.select = True  # select object

mesh = bpy.context.object.data
bm = bmesh.new()

# util function
def interpolate(start,end,points,point) :
    "linear interpolate to find point of points between start and end"
    if point >= points :
        return end
    if point <= 0 :
        return start
    return ((end - start) / points) * point + start

print("calculating vertices")

old_layer_vs = None
for l in range(0,layers) :
    vs = []
    v1 = None
    for i in drange(0,360,360/major_steps) :
        r = (minor_r *
             sin(radians(i * minor_rate)) *
             sin(radians(interpolate(minor_r_start,
                                     minor_r_end,
                                     minor_r_cutout,
                                     l))))
        R = r + (major_r *
                 (sin(radians(interpolate(layer_start_angle,
                                          layer_end_angle,
                                          layers,
                                          l))) * layer_amplitude + 1))

        i += (layer_r *
              sin(radians(interpolate(layer_r_start_angle,
                                      layer_r_end_angle,
                                      layers,
                                      l))))

        base_v = (sin(radians(i)) * R, cos(radians(i)) * R, l*layer_height)
        v2 = bm.verts.new(base_v)
        vs.append(v2)

        # connect vertex to previous layer
        if l > 0 :
            bm.edges.new((old_layer_vs[len(vs)-1],v2))

        # connect vertex on same layer
        if v1 != None :
            bm.edges.new((v1,v2))

            # draw face
            if l > 0 :
                bm.faces.new((old_layer_vs[len(vs)-2],
                              old_layer_vs[len(vs)-1],
                              v2,
                              v1))
        else :
            v0 = v2
        v1 = v2

    # close the loop on the layer
    bm.edges.new((v0,v2))

    # draw last face on layer
    if l > 0 :
        bm.faces.new((old_layer_vs[0],old_layer_vs[len(vs)-1],v2,v0))

    # save the layer samples that were actually calculated (could vary
    # because of rounding issues from major_steps)
    if l == 0 :
        layer_samples = len(bm.verts)
        print("samples per layer " + str(layer_samples))

    # save easy access to the just calculated vertices for next layer
    old_layer_vs = vs

# bottom face
bm.faces.new(bm.verts[:layer_samples])

if layers > 0 :
    # top face
    bm.faces.new(bm.verts[-layer_samples:])

print("finalise")
# make the bmesh the object's mesh
bm.to_mesh(mesh)
bm.free()  # always do this when finished

# adjust view to whole object
for area in bpy.context.screen.areas :
    if area.type == 'VIEW_3D' :
        ctx = bpy.context.copy()
        ctx['area'] = area
        ctx['region'] = area.regions[-1]
        if area.spaces.active.region_3d.is_perspective :
            bpy.ops.view3d.view_persportho(ctx)
        bpy.ops.view3d.view_selected(ctx)
        bpy.ops.view3d.camera_to_view_selected(ctx)

# set lamp position to camera position
lamp.location[0] = scene.camera.location[0]
lamp.location[1] = scene.camera.location[1]
lamp.location[2] = scene.camera.location[2]

if 'png' in A :
    print("exporting image")
    bpy.context.scene.render.filepath = A.png
    bpy.ops.render.render(animation=False,write_still=True)

if 'file' in A :
    print("exporting to " + A.file)
    bpy.ops.export_mesh.stl(filepath=A.file)

if A.close :
    bpy.ops.wm.window_close()
