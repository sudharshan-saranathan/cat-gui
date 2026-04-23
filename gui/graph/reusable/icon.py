# Filename: icon.py
# Module name: graph
# Description: A reusable QGraphicsSimpleTextItem subclass for displaying icons.

from __future__ import annotations
import qtawesome as qta
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets


class QtaItem(QtWidgets.QGraphicsSimpleTextItem):
    """
    Custom QGraphicsSimpleTextItem that shows QtAwesome icons. The icon is rendered as a font glyph for use in a
    QGraphicsScene.
    """

    def __init__(
        self,
        label: str,  # This label is a qt-awesome icon name, e.g., 'mdi.home'
        width: int = 16,  # Size of the icon
        parent: QtWidgets.QGraphicsObject | None = None,
        **kwargs,  # Additional keyword arguments for the QtAwesome icon function (e.g., color).
    ) -> None:

        super().__init__(parent)
        super().setAcceptHoverEvents(True)

        self._width = width
        self._color = kwargs.get("color", "#efefef")

        self.render_icon(label)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setAcceptedMouseButtons(
            kwargs.get("acceptedMouseButtons", QtCore.Qt.MouseButton.NoButton)
        )

    # Method to render the icon
    def render_icon(self, label: str, color: str | None = None) -> None:

        if "." not in label:
            raise ValueError(
                f"Icon name '{label}' must have a prefix (e.g., 'mdi.icon-name'). "
                f"See the docstring for supported prefixes."
            )

        prefix = label.split(".")[0].lower()
        if prefix not in ("mdi", "ph", "fa5", "fa6", "fa5s", "fa6s", "ri"):
            raise ValueError(f"Unsupported icon prefix: '{prefix}'")

        # Get character from name and create a text item:
        char = qta.charmap(label)
        self.setText(char)

        # Set font and color:
        self.setFont(qta.font(prefix, self._width))
        self.setBrush(QtGui.QBrush(color or self._color))

    # Reimplement boundingRect to center the icon at its origin:
    def boundingRect(self) -> QtCore.QRectF:
        parent_rect = super().boundingRect()

        # Center the rect around (0, 0) instead of starting at top-left
        w = parent_rect.width()
        h = parent_rect.height()
        return QtCore.QRectF(-w / 2, -h / 2, w, h)

    # Override paint to center the text within the bounds:
    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionGraphicsItem,
        widget: QtWidgets.QWidget = None,
    ) -> None:
        painter.save()

        # Get the parent's bounding rect (uncentered)
        parent_rect = super().boundingRect()

        # Translate painter to center the text at origin
        painter.translate(-parent_rect.width() / 2, -parent_rect.height() / 2)
        super().paint(painter, option, widget)
        painter.restore()

    @QtCore.Property(int)
    def size(self) -> int:
        return self._width
