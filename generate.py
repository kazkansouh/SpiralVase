#! /usr/bin/python3

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

import json
import sys
import shutil

from subprocess import run, DEVNULL
from os import makedirs
from argparse import ArgumentParser, FileType

def loadspecs(f) :
    'load specifications of vases from file'
    try :
        specs = json.loads(f.read())
        if type(specs) == dict :
            for k in specs :
                if type(specs[k]) != dict :
                    print(k + ' is an invalid vase specification, should be'
                            + ' a JSON object.')
                    return None
            return specs
        else :
            print("Not a JSON object.")
            return None
    except json.JSONDecodeError :
        print("Not valid json.")
        return None

def loadparams() :
    'get parameters from command line'
    args = ArgumentParser(description='Generates pre-configured spiral'
                                    + ' vases that are stored in a json file.')
    args.add_argument('filename',
                      type=FileType('r'),
                      metavar='FILENAME',
                      help='File containing JSON description of vases. The'
                         + ' format of the file is a JSON object, with each'
                         + ' member being the name of a vase. The values of'
                         + ' these members are further objects that directly'
                         + ' define the command line arguments to be passed'
                         + ' to the sincircle.py script. E.g. {\'vase1\':{},'
                         + ' \'vase2\':{\'slices\':\'100\'}} defines two vases.'
                         + ' See the sincircle.py for information on what'
                         + ' command line arguments to supply. However, output'
                         + ' arguments that define stl/png exports are managed'
                         + ' by this script.'
                         + ' [type: %(type)s]')

    args.add_argument('--dont-generate-stl',
                      action='store_false',
                      dest='stl',
                      help='Do not generate stl files.')

    args.add_argument('--dont-generate-png',
                      action='store_false',
                      dest='png',
                      help='Do not generate png preview files.')

    args.add_argument('--stl-dir',
                      type=str,
                      default=".",
                      dest='stl_dir',
                      metavar='S',
                      help='Output directory for stl files.'
                         + ' [type: %(type)s, default: %(default)s]')

    args.add_argument('--png-dir',
                      type=str,
                      default=".",
                      dest='png_dir',
                      metavar='S',
                      help='Output directory for png files.'
                         + ' [type: %(type)s, default: %(default)s]')

    return args.parse_args()

def checkblender() :
    "check blender is in path"
    if shutil.which("blender") is None :
        print("Could not find blender on path.")
        return False
    return True

def runblender(args, name, vase) :
    'Execute Blender on a given vase.'
    print("Starting vase: {}".format(name))
    cmd = ['blender', '-b', '--python', 'sincircle.py', '--', '++close']
    for param in vase :
        cmd.append('++{}'.format(param))
        if type(vase[param]) == list :
            for p in vase[param] :
                cmd.append(p)
        else :
            cmd.append(vase[param])
    if args.stl :
        cmd.append('++outputstl')
        cmd.append('{}/{}.stl'.format(args.stl_dir, name))
    if args.png :
        cmd.append('++outputpng')
        cmd.append('{}/{}.png'.format(args.png_dir, name))
    try :
        print("> {}".format(" ".join(cmd)))
        run(cmd, stdout=DEVNULL, check=True)
    except :
        print("Failed: {}".format(name))
        return False
    print("Finished: {}".format(name))
    return True

def main() :
    'main function'
    args = loadparams()
    specs = loadspecs(args.filename)
    if specs == None or not checkblender() :
        sys.exit(1)
    if args.stl :
        makedirs(args.stl_dir, exist_ok=True)
    if args.png :
        makedirs(args.png_dir, exist_ok=True)

    for vase in specs :
        if not runblender(args, vase, specs[vase]) :
            sys.exit(1)

if __name__ == "__main__" :
    main()
