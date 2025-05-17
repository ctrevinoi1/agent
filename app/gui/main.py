import sys
import os
import asyncio
import json
import websockets
from datetime import datetime
from threading import Thread

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QTabWidget,
    QSplitter, QGroupBox, QStatusBar, QProgressBar
)
from PySide6.QtCore import Qt, QObject, Signal, Slot, QUrl
from PySide6.QtGui import QIcon, QFont, QTextCursor, QDesktopServices
from app.logging_config import logger

class WebSocketThread(QObject):
    """Thread to handle WebSocket communication."""
    message_received = Signal(str)
    status_update = Signal(str)
    report_received = Signal(str)
    connection_error = Signal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.websocket = None
        self.running = False
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.url)
            self.running = True
            self.status_update.emit("Connected to OSINT server")
            
            # Listen for messages
            while self.running:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if "status" in data:
                    self.status_update.emit(data["status"])
                
                if "report" in data:
                    self.report_received.emit(data["report"])
                
                self.message_received.emit(message)
                
        except Exception as e:
            self.connection_error.emit(f"WebSocket error: {str(e)}")
            self.running = False
    
    async def send_message(self, message):
        """Send a message to the WebSocket server."""
        if self.websocket and self.running:
            await self.websocket.send(message)
    
    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            self.running = False
            await self.websocket.close()

class OsintGUI(QMainWindow):
    """Main GUI for the OSINT Analysis System."""
    
    def __init__(self):
        super().__init__()
        logger.info("Launching OSINT Analysis System GUI.")
        self.setWindowTitle("OSINT Analysis System")
        self.setMinimumSize(1000, 700)
        
        # WebSocket thread
        self.ws_thread = None
        self.ws_url = "ws://localhost:8000/ws"
        
        # Create the event loop for asyncio
        self.loop = asyncio.new_event_loop()
        
        # Initialize UI
        self.init_ui()
        
        # Connect to server
        self.connect_to_server()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Splitter to divide query input from results
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Top part: Query input
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        
        # Query label and explanation
        query_header = QLabel("OSINT Query")
        query_header.setFont(QFont("Arial", 14, QFont.Bold))
        query_layout.addWidget(query_header)
        
        query_explanation = QLabel(
            "Enter your OSINT query below. The system will collect, verify, and analyze "
            "open-source information to create a comprehensive report."
        )
        query_explanation.setWordWrap(True)
        query_layout.addWidget(query_explanation)
        
        # Query input box
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("e.g., Investigate the alleged bombing of Al-Shifa Hospital in Gaza in October 2023")
        self.query_input.setMinimumHeight(80)
        query_layout.addWidget(self.query_input)
        
        # Submit button
        query_button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit Query")
        self.submit_button.clicked.connect(self.submit_query)
        query_button_layout.addStretch()
        query_button_layout.addWidget(self.submit_button)
        query_layout.addLayout(query_button_layout)
        
        # Add query widget to splitter
        splitter.addWidget(query_widget)
        
        # Bottom part: Results display with tabs
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # Results header
        results_header = QLabel("Analysis Results")
        results_header.setFont(QFont("Arial", 14, QFont.Bold))
        results_layout.addWidget(results_header)
        
        # Tabs for different views
        self.tabs = QTabWidget()
        
        # Report tab
        self.report_tab = QTextEdit()
        self.report_tab.setReadOnly(True)
        self.tabs.addTab(self.report_tab, "Report")
        
        # Status tab
        self.status_tab = QTextEdit()
        self.status_tab.setReadOnly(True)
        self.tabs.addTab(self.status_tab, "Status Log")
        
        # Sources tab (for future implementation)
        self.sources_tab = QTextEdit()
        self.sources_tab.setReadOnly(True)
        self.tabs.addTab(self.sources_tab, "Sources")
        
        # Add tabs to results layout
        results_layout.addWidget(self.tabs)
        
        # Add results widget to splitter
        splitter.addWidget(results_widget)
        
        # Set initial sizes for the splitter
        splitter.setSizes([200, 500])
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(100)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Status message
        self.status_message = QLabel("Ready")
        self.status_bar.addWidget(self.status_message)
    
    def connect_to_server(self):
        """Connect to the WebSocket server."""
        self.ws_thread = WebSocketThread(self.ws_url)
        
        # Connect signals
        self.ws_thread.status_update.connect(self.update_status)
        self.ws_thread.report_received.connect(self.display_report)
        self.ws_thread.connection_error.connect(self.handle_connection_error)
        
        # Start the thread
        self.asyncio_thread = Thread(target=self.run_asyncio_loop)
        self.asyncio_thread.daemon = True
        self.asyncio_thread.start()
    
    def run_asyncio_loop(self):
        """Run the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.ws_thread.connect())
    
    @Slot()
    def submit_query(self):
        """Submit a query to the server."""
        query = self.query_input.toPlainText().strip()
        if not query:
            self.status_message.setText("Please enter a query")
            return
        logger.info(f"User submitted query via GUI: {query}")
        
        # Clear previous results
        self.report_tab.clear()
        self.status_tab.clear()
        
        # Update UI
        self.status_message.setText("Processing query...")
        self.progress_bar.setValue(10)
        self.submit_button.setEnabled(False)
        
        # Add query to status log
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_text = f"[{timestamp}] Submitting query: {query}\n"
        self.status_tab.append(status_text)
        
        # Send query to server
        query_data = json.dumps({"query": query})
        asyncio.run_coroutine_threadsafe(self.ws_thread.send_message(query_data), self.loop)
    
    @Slot(str)
    def update_status(self, status):
        """Update the status log with a new status message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_text = f"[{timestamp}] {status}\n"
        self.status_tab.append(status_text)
        self.status_message.setText(status)
        
        # Update progress bar based on status messages
        if "Starting data collection" in status:
            self.progress_bar.setValue(20)
        elif "Collection complete" in status:
            self.progress_bar.setValue(40)
        elif "Starting verification" in status:
            self.progress_bar.setValue(50)
        elif "Verification complete" in status:
            self.progress_bar.setValue(70)
        elif "Generating report" in status:
            self.progress_bar.setValue(80)
        elif "Applying ethical filter" in status:
            self.progress_bar.setValue(90)
        elif "Report complete" in status:
            self.progress_bar.setValue(100)
            self.submit_button.setEnabled(True)
    
    @Slot(str)
    def display_report(self, report):
        """Display the final report."""
        # Set report content
        self.report_tab.setMarkdown(report)
        
        # Scroll to top
        cursor = self.report_tab.textCursor()
        cursor.setPosition(0)
        self.report_tab.setTextCursor(cursor)
        
        # Switch to report tab
        self.tabs.setCurrentIndex(0)
        
        # Update status
        self.status_message.setText("Report generation complete")
        self.progress_bar.setValue(100)
        self.submit_button.setEnabled(True)
    
    @Slot(str)
    def handle_connection_error(self, error):
        """Handle WebSocket connection errors."""
        self.status_message.setText(error)
        self.status_tab.append(f"ERROR: {error}\n")
    
    def closeEvent(self, event):
        """Handle the window close event."""
        # Close the WebSocket connection
        if self.ws_thread and self.ws_thread.running:
            asyncio.run_coroutine_threadsafe(self.ws_thread.close(), self.loop)
        
        # Accept the close event
        event.accept()

def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    window = OsintGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 