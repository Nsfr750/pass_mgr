"""View toggle component for switching between grid and list views."""
from PySide6.QtWidgets import QToolButton, QWidget, QHBoxLayout, QButtonGroup, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

class ViewToggle(QWidget):
    """View toggle component for switching between grid and list views."""
    
    # Signal emitted when the view mode changes
    view_mode_changed = Signal(str)  # 'grid' or 'list'
    
    def __init__(self, parent=None):
        """Initialize the view toggle."""
        super().__init__(parent)
        self.current_mode = 'list'  # Default to list view
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Create a button group for exclusive toggle
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # List view button
        self.list_btn = QToolButton()
        self.list_btn.setCheckable(True)
        self.list_btn.setIcon(QIcon(":/icons/list-view.png"))
        self.list_btn.setToolTip("List View")
        self.list_btn.setStatusTip("Switch to list view")
        self.list_btn.clicked.connect(lambda: self._on_button_clicked('list'))
        
        # Grid view button
        self.grid_btn = QToolButton()
        self.grid_btn.setCheckable(True)
        self.grid_btn.setIcon(QIcon(":/icons/grid-view.png"))
        self.grid_btn.setToolTip("Grid View")
        self.grid_btn.setStatusTip("Switch to grid view")
        self.grid_btn.clicked.connect(lambda: self._on_button_clicked('grid'))
        
        # Add buttons to button group
        self.button_group.addButton(self.list_btn, 0)
        self.button_group.addButton(self.grid_btn, 1)
        
        # Add buttons to layout
        layout.addWidget(self.list_btn)
        layout.addWidget(self.grid_btn)
        
        # Set initial state
        self.list_btn.setChecked(True)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Apply styles
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 3px;
                margin: 0 1px;
                background: #f0f0f0;
            }
            QToolButton:checked {
                background: #d0d0d0;
            }
            QToolButton:hover {
                background: #e0e0e0;
            }
        """)
    
    def _on_button_clicked(self, mode):
        """Handle button click events.
        
        Args:
            mode: 'grid' or 'list' depending on which button was clicked
        """
        if mode not in ['grid', 'list']:
            return
            
        self.current_mode = mode
        self.view_mode_changed.emit(mode)
    
    def set_mode(self, mode):
        """Set the current view mode.
        
        Args:
            mode: 'grid' or 'list'
        """
        if mode not in ['grid', 'list']:
            raise ValueError("Mode must be 'grid' or 'list'")
            
        self.current_mode = mode
        
        # Update button states
        if mode == 'list':
            self.list_btn.setChecked(True)
        else:
            self.grid_btn.setChecked(True)
    
    def get_mode(self):
        """Get the current view mode.
        
        Returns:
            str: The current view mode ('grid' or 'list')
        """
        return self.current_mode
    
    def toggle_view_mode(self):
        """Toggle between grid and list views."""
        new_mode = 'grid' if self.current_mode == 'list' else 'list'
        self.set_mode(new_mode)
        self.view_mode_changed.emit(new_mode)
