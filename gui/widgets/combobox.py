# Module Name: gui.widgets
# Description: Custom combobox widget with fixed item height and icon support.

# PySide6 (Python/Qt)
from PySide6 import QtGui
from PySide6 import QtCore
from PySide6 import QtWidgets

# QtAwesome
from qtawesome import icon as qta_icon


class FixedHeightDelegate(QtWidgets.QStyledItemDelegate):
    """
    Item delegate for combobox items with fixed height.

    Overrides the size hint to enforce a consistent item height regardless of content.
    """

    def __init__(self, height: int, parent=None):
        """
        Initialize the fixed height delegate.

        Args:
            height: The fixed height for all items in pixels.
            parent: Parent widget (optional).
        """
        super().__init__(parent)
        self._height = int(height)

    def sizeHint(
        self, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex
    ) -> QtCore.QSize:
        """
        Return the fixed size hint for combo box items.

        Args:
            option: The style option containing display settings.
            index: The model index of the item.

        Returns:
            A QSize with the original width and fixed height.
        """
        base = super().sizeHint(option, index)
        return QtCore.QSize(base.width(), self._height)


class ComboBox(QtWidgets.QComboBox):
    """
    Custom combo box widget with enhanced styling and icon support.
    """

    sig_item_added = QtCore.Signal(str)  # Emitted when a new item is added

    def __init__(self, parent=None, **kwargs):
        """
        Initialize the custom combo box widget.

        Configures the combo box with fixed item height, custom styling, and support for icon-label pairs.

        Args:
            parent: Parent widget (optional).
            **kwargs: Configuration options:
                - iconSize: QSize for combo box icon size (default: 16x16)
                - editable: Whether the combo box is editable (default: False)
                - items: List of items or (icon, label) tuples to add
        """

        # Remove the item-list from kwargs and store it separately
        items = kwargs.pop("items", [])

        # Call super().__init__ with the remaining kwargs
        super().__init__(
            parent,
            iconSize=kwargs.get("iconSize", QtCore.QSize(16, 16)),
            editable=kwargs.get("editable", False),
        )

        # Configure the list view with fixed item height and spacing
        view = QtWidgets.QListView(self)
        view.setItemDelegate(FixedHeightDelegate(20, view))
        view.setSpacing(2)

        # Apply the custom view
        self.setView(view)

        # Populate initial items from kwargs
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:
                icon, label = item
                self.addItem(qta_icon(icon, color="lightgray"), label)
            else:
                self.addItem(item)

        # Track item count to detect new additions
        self._item_count = self.count()

        # Connect the editor's signal
        if editor := self.lineEdit():
            editor.returnPressed.connect(self._confirm_addition)

        self.currentIndexChanged.connect(lambda: self.clearFocus())

    def _confirm_addition(self):
        """Shows a visual confirmation when a new item is added to an editable combo box."""

        if not self.isEditable():
            return

        editor = self.lineEdit()
        string = editor.text().strip()

        # Check if item count increased (Qt added a new item)
        if self.count() > self._item_count:
            # Show visual confirmation
            action = QtGui.QAction(qta_icon("mdi.check-bold", color="cyan"), "", self)
            editor.addAction(
                action, QtWidgets.QLineEdit.ActionPosition.TrailingPosition
            )

            # Remove the action after 1 second and remove focus
            QtCore.QTimer.singleShot(1000, action.deleteLater)
            QtCore.QTimer.singleShot(1000, lambda: editor.clearFocus())

            # Emit signal only when item is actually new
            self.sig_item_added.emit(string)

        # Update the count for next time
        self._item_count = self.count()
