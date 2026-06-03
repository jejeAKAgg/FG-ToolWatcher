# WEB/Viewer.py
import os
import logging
import threading

from http.server import HTTPServer, SimpleHTTPRequestHandler

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from CORE.Services.setup import PROJECT_ROOT, RESULTS_SUBFOLDER



# ======= LOGGING SYSTEM ========
LOG = logging.getLogger(__name__)
# ===============================

class ViewerService:

    """
    Local HTTP server that serves the entire project root as static files.
    viewer.html stays in WEB/ and fetches the CSV from USER/RESULTS/ relatively.

    URL: http://localhost:8765/WEB/viewer.html
    CSV: fetched at runtime via relative path ../USER/RESULTS/FG-ToolWatcher_RESULTS.csv

    """

    PORT = 8765

    def __init__(self):
        self._server: HTTPServer | None = None
        self._running = False

    def start(self) -> None:

        """
        Starts the HTTP server in a background daemon thread.
        Serves PROJECT_ROOT as the document root.
        Safe to call multiple times — only starts once.

        """

        if self._running:
            return

        try:
            root = PROJECT_ROOT

            results_folder = RESULTS_SUBFOLDER

            class SilentHandler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=root, **kwargs)

                def log_message(self, format, *args):
                    pass

                def do_GET(self):
                    # API endpoint — reads CSV fresh from disk, no cache
                    if self.path.startswith('/api/results'):
                        csv_path = os.path.join(results_folder, 'FG-ToolWatcher_RESULTS.csv')
                        if os.path.exists(csv_path):
                            with open(csv_path, 'rb') as f:
                                data = f.read()
                            self.send_response(200)
                            self.send_header('Content-Type', 'text/csv; charset=utf-8-sig')
                            self.send_header('Cache-Control', 'no-store, no-cache')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(data)
                        else:
                            self.send_response(404)
                            self.end_headers()
                        return
                    # Static files (HTML, CSS, JS) — no cache
                    super().do_GET()

                def end_headers(self):
                    self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    super().end_headers()

            self._server = HTTPServer(("localhost", self.PORT), SilentHandler)
            self._running = True

            thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
                name="ViewerService"
            )
            thread.start()

            LOG.info(f"[ViewerService] Server started — serving {root} on http://localhost:{self.PORT}")

        except OSError as e:
            if e.errno == 98:
                LOG.warning(f"[ViewerService] Port {self.PORT} already in use — viewer may already be running.")
                self._running = True
            else:
                LOG.exception(f"[ViewerService] Failed to start server: {e}")

    def open(self) -> None:

        """
        Opens the viewer in the user's default browser.
        Starts the server first if not already running.

        """

        if not self._running:
            self.start()

        url = QUrl(f"http://localhost:{self.PORT}/WEB/viewer.html")
        QDesktopServices.openUrl(url)
        LOG.debug(f"[ViewerService] Opening viewer: {url.toString()}")

    def stop(self) -> None:

        """
        Stops the HTTP server gracefully.

        """

        if self._server:
            self._server.shutdown()
            self._server = None
            self._running = False
            LOG.info("[ViewerService] Server stopped.")
