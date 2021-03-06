#!/usr/bin/env python3

import math
import os
import sys

# load parent path of KicadModTree
sys.path.append(os.path.join(sys.path[0], "..", ".."))

from KicadModTree import *

def bga(args):
    footprint_name = args["name"]
    desc = args["description"]

    pkgWidth = args["pkg_width"]
    pkgHeight = args["pkg_height"]

    pitch = args["pitch"]
    padDiameter = args["pad_diameter"]
    pasteRatio = args["paste_ratio"]
    pasteDiameter = args["paste_diameter"]
    layoutX = args["layout_x"]
    layoutY = args["layout_y"]
    rowNames = args["row_names"]
    rowSkips = args["row_skips"]

    f = Footprint(footprint_name)
    f.setDescription(desc)
    f.setAttribute("smd")
    # If this looks like a CSP footprint, use the CSP 3dshapes library
    if 'BGA' not in footprint_name and 'CSP' in footprint_name:
        f.append(Model(filename="${{KISYS3DMOD}}/Package_CSP.3dshapes"
                                "/{}.wrl".format(footprint_name),
                       at=[0.0, 0.0, 0.0],
                       scale=[1.0, 1.0, 1.0],
                       rotate=[0.0, 0.0, 0.0]))
    else:
        f.append(Model(filename="${{KISYS3DMOD}}/Package_BGA.3dshapes"
                                "/{}.wrl".format(footprint_name),
                       at=[0.0, 0.0, 0.0],
                       scale=[1.0, 1.0, 1.0],
                       rotate=[0.0, 0.0, 0.0]))

    s1 = [1.0, 1.0]
    s2 = [min(1.0, round(pkgWidth / 4.3, 2))] * 2

    t1 = 0.15 * s1[0]
    t2 = 0.15 * s2[0]

    padShape = Pad.SHAPE_CIRCLE

    chamfer = min(1.0, min(pkgWidth, pkgHeight)*0.25)
    silkOffset = 0.125
    crtYd = 1.0

    if pasteDiameter:
        pasteRatio = (pasteDiameter / padDiameter - 1) / 2

    def crtYdRound(x):
        # Round away from zero for proper courtyard calculation
        neg = x < 0
        if neg:
            x = -x
        x = math.ceil(x * 100) / 100
        if neg:
            x = -x
        return x

    xCenter = 0.0
    xLeftFab = xCenter - pkgWidth / 2
    xRightFab = xCenter + pkgWidth / 2
    xChamferFab = xLeftFab + chamfer
    xPadLeft = xCenter - pitch * ((layoutX - 1) / 2)
    xPadRight = xCenter + pitch * ((layoutX - 1) / 2)
    xLeftCrtYd = crtYdRound(xCenter - (pkgWidth / 2 + crtYd))
    xRightCrtYd = crtYdRound(xCenter + (pkgWidth / 2 + crtYd))

    yCenter = 0.0
    yTopFab = yCenter - pkgHeight / 2
    yBottomFab = yCenter + pkgHeight / 2
    yChamferFab = yTopFab + chamfer
    yPadTop = yCenter - pitch * ((layoutY - 1) / 2)
    yPadBottom = yCenter + pitch * ((layoutY - 1) / 2)
    yTopCrtYd = crtYdRound(yCenter - (pkgHeight / 2 + crtYd))
    yBottomCrtYd = crtYdRound(yCenter + (pkgHeight / 2 + crtYd))
    yRef = yTopFab - 1.0
    yValue = yBottomFab + 1.0

    xLeftSilk = xLeftFab - silkOffset
    xRightSilk = xRightFab + silkOffset
    xChamferSilk = xLeftSilk + chamfer
    yTopSilk = yTopFab - silkOffset
    yBottomSilk = yBottomFab + silkOffset
    yChamferSilk = yTopSilk + chamfer

    wFab = 0.10
    wCrtYd = 0.05
    wSilkS = 0.12

    # Text
    f.append(Text(type="reference", text="REF**", at=[xCenter, yRef],
                  layer="F.SilkS", size=s1, thickness=t1))
    f.append(Text(type="value", text=footprint_name, at=[xCenter, yValue],
                  layer="F.Fab", size=s1, thickness=t1))
    f.append(Text(type="user", text="%R", at=[xCenter, yCenter],
                  layer="F.Fab", size=s2, thickness=t2))

    # Fab
    f.append(PolygoneLine(polygone=[[xRightFab, yBottomFab],
                                    [xLeftFab, yBottomFab],
                                    [xLeftFab, yChamferFab],
                                    [xChamferFab, yTopFab],
                                    [xRightFab, yTopFab],
                                    [xRightFab, yBottomFab]],
                          layer="F.Fab", width=wFab))

    # Courtyard
    f.append(RectLine(start=[xLeftCrtYd, yTopCrtYd],
                      end=[xRightCrtYd, yBottomCrtYd],
                      layer="F.CrtYd", width=wCrtYd))

    # Silk
    f.append(PolygoneLine(polygone=[[xChamferSilk, yTopSilk],
                                    [xRightSilk, yTopSilk],
                                    [xRightSilk, yBottomSilk],
                                    [xLeftSilk, yBottomSilk],
                                    [xLeftSilk, yChamferSilk]],
                          layer="F.SilkS", width=wSilkS))

    # Pads
    balls = layoutX * layoutY
    if rowSkips == []:
        for _ in range(layoutY):
            rowSkips.append([])
    for rowNum, row in zip(range(layoutY), rowNames):
        rowSet = set(range(1, layoutX + 1))
        for item in rowSkips[rowNum]:
            try:
                # If item is a range, remove that range
                rowSet -= set(range(*item))
                balls -= item[1] - item[0]
            except TypeError:
                # If item is an int, remove that int
                rowSet -= {item}
                balls -= 1
        for col in rowSet:
            f.append(Pad(number="{}{}".format(row, col), type=Pad.TYPE_SMT,
                         shape=padShape,
                         at=[xPadLeft + (col-1) * pitch, yPadTop + rowNum * pitch],
                         size=[padDiameter, padDiameter],
                         layers=Pad.LAYERS_SMT,
                         solder_paste_margin_ratio=pasteRatio))

    f.setTags("BGA {} {}".format(balls, pitch))

    file_handler = KicadFileHandler(f)
    file_handler.writeFile(footprint_name + ".kicad_mod")

if __name__ == '__main__':
    parser = ModArgparser(bga)
    # the root node of .yml files is parsed as name
    parser.add_parameter("name", type=str, required=True)
    parser.add_parameter("description", type=str, required=True)
    parser.add_parameter("pkg_width", type=float, required=True)
    parser.add_parameter("pkg_height", type=float, required=True)
    parser.add_parameter("pitch", type=float, required=True)
    parser.add_parameter("pad_diameter", type=float, required=True)
    parser.add_parameter("paste_ratio", type=float, required=False, default=0)
    parser.add_parameter("paste_diameter", type=float, required=False, default=0)
    parser.add_parameter("layout_x", type=int, required=True)
    parser.add_parameter("layout_y", type=int, required=True)
    parser.add_parameter("row_names", type=list, required=False, default=[
        "A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P",
        "R", "T", "U"])
    parser.add_parameter("row_skips", type=list, required=False, default=[])

    # now run our script which handles the whole part of parsing the files
    parser.run()
