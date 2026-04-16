from panda3d.core import NodePath, Point3, LineSegs
from direct.interval.IntervalGlobal import Sequence

class VisualMarkersManager:
    def __init__(self, game):
        self.game = game

    def create_cross_marker(self, position):
        marker_node = NodePath("hit_marker")
        marker_node.reparentTo(self.game.render)
        marker_node.setPos(position)

        segs = LineSegs()
        segs.setColor(1, 0, 0, 1)
        segs.setThickness(1.5)

        size = 0.1

        center = Point3(0, 0, 0)

        segs.moveTo(center + Point3(-size, 0, 0))
        segs.drawTo(center + Point3(size, 0, 0))

        segs.moveTo(center + Point3(0, -size, 0))
        segs.drawTo(center + Point3(0, size, 0))

        segs.moveTo(center + Point3(0, 0, -size))
        segs.drawTo(center + Point3(0, 0, size))

        cross_lines = segs.create()
        cross_node = NodePath(cross_lines)
        cross_node.reparentTo(marker_node)

        marker_node.setBillboardPointEye()

        return marker_node

    def create_hit_marker(self, position):
        segs = LineSegs()
        segs.setColor(1, 0, 0, 1)
        segs.setThickness(2.0)

        size = 0.2

        segs.moveTo(position + Point3(-size, 0, 0))
        segs.drawTo(position + Point3(size, 0, 0))

        segs.moveTo(position + Point3(0, 0, -size))
        segs.drawTo(position + Point3(0, 0, size))

        marker_node = self.game.render.attachNewNode(segs.create())

        scale_sequence = Sequence(
            marker_node.scaleInterval(0.1, 1.5),
            marker_node.scaleInterval(0.1, 1.0)
        )
        scale_sequence.start()

        return marker_node
