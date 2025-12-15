from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QPainterPath, QPen, QBrush
from typing import Optional

from ..components.node_visual import NodeVisual, NodeVisualState
from ..components.edge_visual import EdgeVisual
from ..managers.graph_manager import GraphManager
from entities import Entity, ENTITY_TYPES
from entities.event import Event
from ..dialogs.timeline_editor import TimelineEvent

class GraphView(QGraphicsView):
    scaleChanged = Signal(float)
    
    # Zoom limits
    MIN_ZOOM = 0.1
    MAX_ZOOM = 5.0
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self._setup_view()
        self._is_panning = False
        self._last_pan_point = None
        self._rubber_band_origin = None
        self._rubber_band_rect = None
        
        # Set a very large scene rect for infinite panning
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        
        # Initialize graph manager
        self.graph_manager = GraphManager(self)
        
        # Connect selection changed signal
        self.scene.selectionChanged.connect(self.handle_selection_changed)
        
        # Enable strong focus to receive keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def _setup_view(self):
        """Setup view properties"""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # Set dark theme background
        self.setBackgroundBrush(QColor(30, 30, 30))
        
    def sync_event_to_timeline(self, entity: Event):
        """Sync an event entity with the timeline"""
        if not hasattr(self.window(), 'timeline_manager'):
            return
            
        timeline_manager = self.window().timeline_manager
        
        # Create timeline event if dates are set
        if entity.start_date and entity.end_date:
            timeline_event = TimelineEvent(
                name=entity.name,
                description=entity.description or "",
                start_time=entity.start_date,
                end_time=entity.end_date,
                color=QColor(entity.color)
            )
            
            # Remove any existing events for this entity
            existing_events = [e for e in timeline_manager.get_events() 
                             if getattr(e, 'source_entity_id', None) == entity.id]
            for event in existing_events:
                timeline_manager.timeline_widget.delete_event(event)
            
            # Add new event with source reference
            timeline_event.source_entity_id = entity.id
            timeline_manager.add_event(timeline_event)

    def handle_selection_changed(self):
        """Handle selection changes in the scene"""
        selected_items = self.scene.selectedItems()
        
        # Reset all node states first
        for item in self.scene.items():
            if isinstance(item, NodeVisual):
                if item not in selected_items:
                    item.set_state(NodeVisualState.NORMAL)
                    # Remove the callback when deselected
                    if isinstance(item.node, Event):
                        item.node.on_properties_changed = None
                else:
                    item.set_state(NodeVisualState.SELECTED)
                    # Set up the callback only if it's not already set
                    if isinstance(item.node, Event) and not hasattr(item.node, 'on_properties_changed'):
                        item.node.on_properties_changed = lambda: self.sync_event_to_timeline(item.node)
                    
        # Update connected nodes for selected edges
        for item in selected_items:
            if isinstance(item, EdgeVisual):
                item.source.set_state(NodeVisualState.HIGHLIGHTED)
                item.target.set_state(NodeVisualState.HIGHLIGHTED)
                
        # Update transforms list in main window if available
        if hasattr(self.parent(), "update_transforms_list"):
            selected_node = None
            for item in selected_items:
                if isinstance(item, NodeVisual):
                    selected_node = item.node
                    break
            self.parent().update_transforms_list(selected_node)

    def drawForeground(self, painter: QPainter, rect: QRectF):
        """Draw rubber band selection"""
        if self._rubber_band_rect and not self._rubber_band_rect.isEmpty():
            rubber_band_color = QColor("#2196F3")  # Material Blue
            rubber_band_color.setAlpha(50)
            
            painter.setPen(QPen(rubber_band_color.darker(150), 1, Qt.PenStyle.SolidLine))
            painter.setBrush(QBrush(rubber_band_color))
            
            view_rect = self._rubber_band_rect.toRect()
            scene_rect = QRectF(
                self.mapToScene(view_rect.topLeft()),
                self.mapToScene(view_rect.bottomRight())
            )
            painter.drawRect(scene_rect)

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.RightButton:
            item = self.itemAt(event.pos())
            if item is None or isinstance(item, EdgeVisual):
                self._start_panning(event)
            else:
                super().mousePressEvent(event)
        else:
            item = self.itemAt(event.pos())
            if not item:
                self._rubber_band_origin = event.pos()
                self._rubber_band_rect = QRectF()
                self.scene.clearSelection()
                if hasattr(self.parent(), "update_transforms_list"):
                    self.parent().update_transforms_list(None)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self._is_panning and self._last_pan_point is not None:
            delta = event.pos() - self._last_pan_point
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self._last_pan_point = event.pos()
            event.accept()
        elif self._rubber_band_origin is not None:
            origin_point = QPointF(self._rubber_band_origin)
            current_point = QPointF(event.pos())
            self._rubber_band_rect = QRectF(origin_point, current_point).normalized()
            
            scene_rect = QRectF(
                self.mapToScene(self._rubber_band_rect.toRect().topLeft()),
                self.mapToScene(self._rubber_band_rect.toRect().bottomRight())
            )
            
            path = QPainterPath()
            path.addRect(scene_rect)
            
            self.scene.setSelectionArea(path, self.viewportTransform())
            self.viewport().update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.RightButton and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        elif self._rubber_band_origin is not None:
            self._rubber_band_origin = None
            self._rubber_band_rect = None
            self.viewport().update()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Handle zoom with mouse wheel - IMPROVED VERSION"""
        # Get current zoom level
        current_zoom = self.transform().m11()
        
        # Calculate zoom factor
        zoom_factor = 1.15
        
        # Determine if zooming in or out
        if event.angleDelta().y() > 0:
            # Zoom in
            new_zoom = current_zoom * zoom_factor
            if new_zoom > self.MAX_ZOOM:
                return  # Don't zoom beyond max
            factor = zoom_factor
        else:
            # Zoom out
            new_zoom = current_zoom / zoom_factor
            if new_zoom < self.MIN_ZOOM:
                return  # Don't zoom beyond min
            factor = 1.0 / zoom_factor
        
        # Apply zoom with smooth scaling
        self.scale(factor, factor)
        
        # Emit scale changed signal for UI updates
        self.scaleChanged.emit(self.transform().m11())
        
        event.accept()

    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasFormat("application/x-entity"):
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event):
        """Handle drag move events"""
        if event.mimeData().hasFormat("application/x-entity"):
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """Handle drop events"""
        if event.mimeData().hasFormat("application/x-entity"):
            # Get the entity type
            entity_name = event.mimeData().data("application/x-entity").data().decode()
            
            # Create entity at drop position
            pos = self.mapToScene(event.position().toPoint())
            
            if entity_name in ENTITY_TYPES:
                entity_class = ENTITY_TYPES[entity_name]
                entity = entity_class(label=f"{entity_name}")
                self.graph_manager.add_node(entity, pos)
            
            event.acceptProposedAction()

    def _start_panning(self, event):
        """Start panning the view"""
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self._is_panning = True
        self._last_pan_point = event.pos()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def keyPressEvent(self, event):
        """Handle key press events - WITH ZOOM SHORTCUTS"""
        if event.key() == Qt.Key.Key_Delete:
            self._delete_selected_nodes()
        elif event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            # Zoom in with Cmd/Ctrl + '+'
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
                self.zoom_in()
        elif event.key() in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore):
            # Zoom out with Cmd/Ctrl + '-'
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
                self.zoom_out()
        elif event.key() == Qt.Key.Key_0:
            # Reset zoom with Cmd/Ctrl + '0'
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
                self.reset_zoom()
        elif event.key() == Qt.Key.Key_F:
            # Fit view to selection or all items with 'F'
            self.fit_in_view()
        else:
            super().keyPressEvent(event)
    
    def zoom_in(self):
        """Zoom in programmatically"""
        zoom_factor = 1.15
        current_zoom = self.transform().m11()
        if current_zoom * zoom_factor <= self.MAX_ZOOM:
            self.scale(zoom_factor, zoom_factor)
            self.scaleChanged.emit(self.transform().m11())
    
    def zoom_out(self):
        """Zoom out programmatically"""
        zoom_factor = 1.15
        current_zoom = self.transform().m11()
        if current_zoom / zoom_factor >= self.MIN_ZOOM:
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)
            self.scaleChanged.emit(self.transform().m11())
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.resetTransform()
        self.scaleChanged.emit(1.0)
    
    def fit_in_view(self):
        """Fit all items or selected items in view"""
        # Get selected items or all items
        items = self.scene.selectedItems()
        if not items:
            items = [item for item in self.scene.items() 
                    if isinstance(item, (NodeVisual, EdgeVisual))]
        
        if not items:
            return
        
        # Get bounding rect of all items
        rect = items[0].sceneBoundingRect()
        for item in items[1:]:
            rect = rect.united(item.sceneBoundingRect())
        
        # Add padding
        padding = 50
        rect.adjust(-padding, -padding, padding, padding)
        
        # Fit in view with aspect ratio
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Ensure we don't exceed zoom limits
        current_zoom = self.transform().m11()
        if current_zoom > self.MAX_ZOOM:
            self.resetTransform()
            self.scale(self.MAX_ZOOM, self.MAX_ZOOM)
        elif current_zoom < self.MIN_ZOOM:
            self.resetTransform()
            self.scale(self.MIN_ZOOM, self.MIN_ZOOM)
        
        self.scaleChanged.emit(self.transform().m11())
            
    def _delete_selected_nodes(self):
        """Delete all selected nodes"""
        selected_nodes = [item for item in self.scene.selectedItems() 
                         if isinstance(item, NodeVisual)]
        
        if not selected_nodes:
            return
            
        # Delete all selected nodes
        for node in selected_nodes:
            if hasattr(self, 'graph_manager'):
                self.graph_manager.remove_node(node.node.id)

    def add_node(self, entity: Entity, pos: Optional[QPointF] = None) -> Optional[NodeVisual]:
        """Add a node to the graph"""
        node = self.graph_manager.add_node(entity, pos)
        
        # If it's an event with dates, add it to the timeline
        if isinstance(entity, Event):
            self.sync_event_to_timeline(entity)
        
        return node