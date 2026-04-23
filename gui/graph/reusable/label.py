# Filename: label.py
# Module name: graph.reusable
# Description: A QGraphicsTextItem subclass with customizable options.

# Imports (standard)
from __future__ import annotations


from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QTextCursor, QPen, QFont
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QStyle

LabelOpts = {
    "const": False,  # Whether the string is immutable.
    "round": 4,  # Radius for rounded corners.
    "coord": QPointF(0, 0),  # Default position of the label with respect to its parent.
    "style": {
        "border": Qt.GlobalColor.transparent,
        "background": Qt.GlobalColor.transparent,
    },
    "label": {
        "font": QFont("Trebuchet MS", 7),  # Default text font.
        "color": Qt.GlobalColor.black,  # Default text color.
        "align": Qt.AlignmentFlag.AlignCenter,  # Default text alignment.
        "width": 80,  # Default text width.
    },
}


# Class String: A custom-QGraphicsTextItem
class Label(QGraphicsTextItem):

    # Signals:
    sig_text_changed = Signal(str, name="String.sig_text_changed")

    # Initializer:
    def __init__(self, label: str, parent: QGraphicsItem | None = None, **kwargs):

        # Initialize base-class:
        super().__init__(label, parent)
        super().setAcceptHoverEvents(True)

        # Retrieve keywords:
        self.setProperty("const", kwargs.get("const", LabelOpts["const"]))
        self.setProperty("round", kwargs.get("round", LabelOpts["round"]))
        self.setProperty("style", kwargs.get("style", LabelOpts["style"]))
        self.setProperty("pos", kwargs.get("pos", QPointF(0, 0)))

        # Text properties:
        self.setProperty("text-color", kwargs.get("color", LabelOpts["label"]["color"]))
        self.setProperty("text-width", kwargs.get("width", LabelOpts["label"]["width"]))
        self.setProperty("text-align", kwargs.get("align", LabelOpts["label"]["align"]))
        self.setProperty("text-font", kwargs.get("font", LabelOpts["label"]["font"]))

        # Customize attribute(s):
        self.setTextWidth(self.property("text-width"))
        self.setDefaultTextColor(self.property("text-color"))
        # Start with no interaction - enable on hover
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        # Set text-alignment:
        option = self.document().defaultTextOption()
        option.setAlignment(self.property("text-align"))
        self.document().setDefaultTextOption(option)

    # Reimplementation of QGraphicsTextItem.paint():
    def paint(self, painter, option, widget):

        # Reset the state-flag to prevent the dashed-line selection style.
        option.state = QStyle.StateFlag.State_None

        # Paint the border and background:
        painter.setPen(QPen(self.property("style")["border"], 0.75))
        painter.setBrush(self.property("style")["background"])
        painter.drawRoundedRect(
            self.boundingRect(), self.property("round"), self.property("round")
        )

        # Invoke base-class implementation to paint the text:
        super().paint(painter, option, widget)

    # Edit text:
    def edit(self):

        # If the item is immutable, return immediately:
        if self.property("const"):
            return

        # Make label edit:
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)

        # Highlight text:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(
            QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor
        )
        self.setTextCursor(cursor)

    # Reimplementation of QGraphicsTextItem.keyPressEvent():
    def keyPressEvent(self, event):
        """
        Handles key press events for the text item.
        :param event:
        :return:
        """

        # If the key pressed is `Return`, finish editing and clear focus:
        if event.key() == Qt.Key.Key_Return:
            self.clearFocus()
            event.accept()
            return

        # Otherwise, call super-class implementation:
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Accept mouse press to prevent propagation to items below."""
        super().mousePressEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        """Accept mouse release to prevent propagation to items below."""
        super().mouseReleaseEvent(event)
        event.accept()

    # Reimplementation of QGraphicsTextItem.focusInEvent():
    def focusInEvent(self, event):
        """
        This method is called when the text item gains focus.
        :param event:
        :return:
        """

        # If the item is immutable, return immediately:
        if self.property("const"):
            return

        # Super-class implementation:
        super().focusInEvent(event)

    # Reimplementation of QGraphicsTextItem.focusOutEvent():
    def focusOutEvent(self, event):

        # Clear text-selection and emit signal:
        string = self.toPlainText().strip()  # Get the text and strip whitespace
        self.sig_text_changed.emit(string)  # Emit signal with new text as the argument
        self.textCursor().clearSelection()  # Clear text-selection

        # Super-class implementation:
        super().focusOutEvent(event)

    # Reimplementation of QGraphicsTextItem.hoverEnterEvent():
    def hoverEnterEvent(self, event):
        """
        Handles the hover enter event to change the cursor shape.
        :param event: QGraphicsSceneHoverEvent
        """

        if not self.property("const"):
            self.setCursor(Qt.CursorShape.IBeamCursor)
            self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
            self.update()

        super().hoverEnterEvent(event)
        event.accept()

    # Reimplementation of QGraphicsTextItem.hoverLeaveEvent():
    def hoverLeaveEvent(self, event):
        """
        Handles the hover leave event to reset the cursor shape.
        """

        if not self.property("const"):
            self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self.unsetCursor()
        self.update()

        super().hoverLeaveEvent(event)
        event.accept()

    @property
    def const(self):
        return self.property("const")

    @const.setter
    def const(self, value: bool):
        """
        Set the const property of the string.
        :param value: bool
        """
        self.setProperty("const", value)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
            if value
            else Qt.TextInteractionFlag.TextEditorInteraction
        )
        self.update()
