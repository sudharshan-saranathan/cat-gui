# Encoding: utf-8
# Module Name: image
# Description: Animatable SVG-icon class for non-textual labeling.

from __future__ import annotations

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtSvg
from PySide6 import QtCore
from PySide6 import QtWidgets

# Default options:
ImageOpts = {
    "size": QtCore.QSize(20, 20),  # Size of the SVG icon.
    "anim": False,  # Whether to animate the icon on appearance.
}


# Class Icon:
class Image(QtWidgets.QGraphicsObject):

    # Default constructor:
    def __init__(
        self,
        buffer: str | QtGui.QIcon,
        parent: QtWidgets.QGraphicsObject | None = None,
        **kwargs,
    ):
        super().__init__(parent)

        # Set properties:
        self.setProperty("size", kwargs.get("size", ImageOpts["size"]))
        self.setProperty("anim", kwargs.get("anim", False))
        self.setProperty("buffer", buffer)

        # Render the buffer:
        if isinstance(buffer, str):
            self.renderer = QtSvg.QSvgRenderer(buffer)
        else:
            self.renderer = QtSvg.QSvgRenderer()

        # If the `movable` is set:
        if kwargs.get("movable", False):
            self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
            self.setFlag(
                QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
            )

    # Reimplementation of QGraphicsObject.boundingRect():
    def boundingRect(self) -> QtCore.QRectF:
        """
        Returns the bounding rectangle of the SVG icon.
        """
        return QtCore.QRectF(
            -self.property("size").width() / 2,
            -self.property("size").height() / 2,
            self.property("size").width(),
            self.property("size").height(),
        )

    # Reimplementation of QGraphicsObject.paint():
    def paint(self, painter, option, widget=None):
        """
        Paints the SVG icon using the QSvgRenderer.
        """
        if not hasattr(self, 'renderer') or self.renderer is None:
            return
        painter.save()
        self.renderer.render(painter, self.boundingRect())
        painter.restore()

    # Method to generate a QIcon:
    def to_icon(self):
        """
        Converts the SVG icon to a QIcon object.
        """
        from PySide6 import QtGui

        pixmap = QtGui.QPixmap(self.property("size"))
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QtGui.QPainter(pixmap)
        self.renderer.render(painter)
        painter.end()

        return QtGui.QIcon(pixmap)

    # Method to set a different SVG buffer:
    def set_buffer(self, buffer: str) -> None:
        """
        Sets a new SVG buffer for the icon.
        :param buffer: SVG data as a string or QIcon.
        """
        self.setProperty("buffer", buffer)
        self.renderer.load(buffer)
        self.update()
