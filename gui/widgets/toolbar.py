# Module Name: gui.widgets.toolbar
# Description: Custom toolbar widget with action management.

import logging
from dataclasses import dataclass
from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

logger = logging.getLogger(__name__)


class ToolBar(QtWidgets.QToolBar):
    """
    Custom toolbar with configurable actions and layout.

    Supports icon-based actions with optional text labels, customizable spacing,
    and trailing/leading action alignment relative to a spacer.
    """

    sig_action_triggered = QtCore.Signal(str)

    @dataclass
    class Appearance:
        qss: str

    @dataclass
    class Behavior:
        trailing: bool
        enable_counting: bool

    def __init__(self, parent=None, **kwargs):
        """
        Initialize the toolbar with actions and styling.

        Args:
            parent: Parent widget (optional).
            **kwargs: Configuration options:
                - iconSize: QSize for toolbar icons (default: 16x16)
                - floatable: Whether the toolbar can float (default: False)
                - trailing: Whether the toolbar's actions trail a spacer item (default: True)
                - movable: Whether the toolbar can be moved (default: False)
                - orientation: Toolbar orientation (default: Horizontal)
                - toolButtonStyle: Button style (default: IconOnly)
                - enable_counting: Enable counter on actions (default: False)
                - style: Custom stylesheet (default: "")
                - actions: List of (icon, label, callback) tuples (default: [])
        """

        # 1. Extract the custom behavioral flags from `kwargs` before passing it to the base-class constructor.
        #    Otherwise, the base-class initializer will throw an error
        self._behavior = ToolBar.Behavior(
            kwargs.pop("trailing", True),
            kwargs.pop("enable_counting", False),
        )

        self._appearance = ToolBar.Appearance(kwargs.pop("style", ""))
        self._actions = kwargs.pop("actions", [])

        # 2. Initialize the base-class (QToolBar) and pass additional attribute(s) via `kwargs`
        super().__init__(parent, **kwargs)

        # 3. Initialize the storage counter and extract configuration
        self._action_counters = {}
        self._action_labels = {}

        # 4. Create and add the spacer and actions
        spacer = QtWidgets.QFrame()
        spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        if self._behavior.trailing:
            self.addWidget(spacer)
            self.add_actions(self._actions)

        else:
            self.add_actions(self._actions)
            self.addWidget(spacer)

        self.setStyleSheet(self._appearance.qss)

    def add_actions(self, actions: list) -> None:
        """
        Add actions to the toolbar.

        Each action is created from a tuple of (icon, label, callback).
        Emits sig_action_triggered with the action label when triggered.

        Args:
            actions: List of (icon, label, callback) tuples where:
                - icon: QIcon object for the action
                - label: Text label for the action
                - callback: Callable invoked when action is triggered (can be None)
        """

        try:
            for icon, label, callback in actions:

                # Create action and configure based on mode
                action = self.addAction(icon, label)

                if self._behavior.enable_counting:
                    self._action_labels[action] = label
                    self._action_counters[action] = 0
                    self._update_action_text(action)

                    action.triggered.connect(
                        lambda _, act=action: self._on_action_increment(act)
                    )
                else:
                    action.triggered.connect(
                        lambda _, lbl=label: self.sig_action_triggered.emit(lbl)
                    )

                if callback:
                    action.triggered.connect(callback)
        except (RuntimeError, IndexError, ValueError) as e:
            logger.error(f"Error adding actions to toolbar: {e}")

    def _on_action_increment(self, action: QtGui.QAction) -> None:
        """
        Increment counter for an action and update its text.
        """

        self._action_counters[action] += 1
        self._update_action_text(action)
        self.sig_action_triggered.emit(self._action_labels[action])

    def _update_action_text(self, action: QtGui.QAction) -> None:
        """
        Update action text to show counter.
        """

        original_label = self._action_labels[action]
        count = self._action_counters[action]
        action.setText(f"{original_label}\n(x{count})")
