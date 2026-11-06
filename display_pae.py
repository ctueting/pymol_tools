"""AlphaFold 3 PAE viewer for PyMOL 3 (NumPy + PyMOL Qt only).

Use inside PyMOL:
    run /path/to/load_af.py
    display_pae("fold_example_4_full_data_0.json")

The matrix is rasterized, but PDF/SVG axes, text, and colorbar are
rendered with QPainter. PAE token mapping requires token_chain_ids and
 token_res_ids in the confidence JSON.
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from pymol.Qt import QtWidgets, QtGui, QtCore

from pymol.Qt import PYQT_NAME
import importlib

QtSvg = importlib.import_module(f"{PYQT_NAME}.QtSvg")

# When executed using PyMOL's `run`, `cmd` is normally available.
# Import explicitly as well, so the module also works when imported.
try:
    cmd
except NameError:
    from pymol import cmd


_image_windows = []
VMIN, VMAX = 0.0, 31.0
FIG_W, FIG_H = 1100, 1000   # Common logical dimensions for every exporter
FIGURE_WIDTH_MM = 200.0
PNG_DPI = 300
CHAIN_BOUNDARY_COLOR = "#333333"
CHAIN_BOUNDARY_WIDTH = 1.1  # logical px in exported figure
COLORBAR_STEPS = 256

PALETTES = {
    # Dark green for small PAE; off-white for large PAE (ColorBrewer Greens_r).
    "AlphaFold (Greens_r)": [
        "#00441B", "#006D2C", "#238B45", "#41AB5D", "#74C476",
        "#A1D99B", "#C7E9C0", "#E5F5E0", "#F7FCF5"
    ],
    "Grayscale": ["#000000", "#FFFFFF"],
    "Viridis": ["#440154", "#3B528B", "#21918C", "#5EC962", "#FDE725"],
    "Magma": ["#000004", "#51127C", "#B73779", "#FC8961", "#FCFDBF"],
    "Plasma": ["#0D0887", "#7E03A8", "#CC4778", "#F89540", "#F0F921"],
    "Turbo": ["#30123B", "#4662D7", "#1AC7C2", "#A4FC3C", "#FCA50A", "#7A0403"],
    "Blue-White-Red": ["#2166AC", "#FFFFFF", "#B2182B"],
}


def colorize(array, palette_name):
    """Map actual PAE values onto the fixed [0, 31] Å color scale."""
    stops = PALETTES[palette_name]
    colors = np.asarray([
        [int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in stops
    ], dtype=float)
    v = np.nan_to_num(np.asarray(array, dtype=float),
                      nan=VMAX, posinf=VMAX, neginf=VMIN)
    v = np.clip((v - VMIN) / (VMAX - VMIN), 0, 1)
    anchors = np.linspace(0, 1, len(colors))
    rgb = np.stack([np.interp(v, anchors, colors[:, i]) for i in range(3)], axis=-1)
    return np.ascontiguousarray(np.rint(rgb).astype(np.uint8))


def token_atom_mapping(object_name, chain_ids, res_ids, n_tokens):
    """Map AlphaFold tokens onto atom indices of a PyMOL molecular object.

    Compare label_asym_id (PyMOL 'segi') and author chain ID ('chain'),
    and allow for a uniform 0/1-based residue-numbering offset.
    A poor mapping is refused rather than guessed.

    Returns: (token_to_atom_indices, original_atom_colors, mapping_summary)
    """
    if chain_ids is None or res_ids is None:
        raise ValueError("JSON lacks token_chain_ids/token_res_ids: cannot map PAE to atoms.")
    if len(chain_ids) != n_tokens or len(res_ids) != n_tokens:
        raise ValueError("Token metadata dimensions do not match the PAE matrix.")

    # PyMOL's get_model() Atom objects do not reliably expose `color`.
    # cmd.iterate() makes the per-atom color index available explicitly,
    # together with the atom index and residue identifiers. Capture them
    # in one pass so the saved colors match exactly the mapping's indices.
    atom_records = []
    cmd.iterate(
        "(%" + object_name + ")",
        "records.append((index, segi, chain, resi, color))",
        space={"records": atom_records},
    )
    if not atom_records:
        raise ValueError("The selected object contains no atoms.")

    keymaps = {"segi": defaultdict(list), "chain": defaultdict(list)}
    colors = {}
    for idx, segi, chain, resid, color_id in atom_records:
        idx, resid = int(idx), str(resid)
        colors[idx] = int(color_id)
        keymaps["segi"][(str(segi), resid)].append(idx)
        keymaps["chain"][(str(chain), resid)].append(idx)

    try:
        tokens = [(str(ch), int(res)) for ch, res in zip(chain_ids, res_ids)]
    except (TypeError, ValueError) as exc:
        raise ValueError("JSON token_res_ids must be integer residue indices.") from exc

    # Prefer exact label-based numbering in ties; do not infer arbitrary offsets.
    candidates = []
    for mode in ("segi", "chain"):
        for offset in (0, 1, -1):
            mapping = keymaps[mode]
            count = sum(bool(mapping.get((ch, str(res + offset)))) for ch, res in tokens)
            candidates.append((count, mode, offset))

    matched, mode, offset = max(candidates, key=lambda item: item[0])
    coverage = matched / n_tokens
    if coverage < 0.90:
        raise ValueError(
            f"Only {matched}/{n_tokens} tokens matched ({coverage:.0%}). "
            "Check that the model belongs to this prediction, and its "
            "mmCIF chain/residue numbering. Nothing was recolored."
        )

    chosen_map = keymaps[mode]
    mapped = [chosen_map.get((ch, str(res + offset)), [])
              for ch, res in tokens]
    summary = f"{matched}/{n_tokens} tokens ({coverage:.1%}); {mode}, offset {offset:+d}"
    return mapped, colors, summary


class PAECanvas(QtWidgets.QWidget):
    def __init__(self, array, chain_ids=None):
        super().__init__()
        self.array = np.asarray(array, dtype=float)
        self.palette_name = "AlphaFold (Greens_r)"
        self.show_chain_boundaries = True
        self.chain_boundaries = []
        if chain_ids is not None:
            if len(chain_ids) != self.array.shape[0]:
                raise ValueError("token_chain_ids length does not match PAE dimensions")
            # A separator is placed BETWEEN consecutive token runs, not on a residue.
            self.chain_boundaries = [
                i for i in range(1, len(chain_ids))
                if str(chain_ids[i]) != str(chain_ids[i - 1])
            ]
        self.on_region_selected = None
        self.drag_start = None
        self.region = None  # inclusive: (x0, x1, y0, y1), 0-based
        self.setMinimumSize(510, 490)
        self.setMouseTracking(True)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.update_image()

    def update_image(self):
        pixels = colorize(self.array, self.palette_name)
        h, w = pixels.shape[:2]
        self.image = QtGui.QImage(
            pixels.data, w, h, pixels.strides[0], QtGui.QImage.Format_RGB888
        ).copy()  # Qt owns the memory, independent of temporary NumPy array.
        # Build exactly the same color scale for the vector colorbar.
        # Draw it as solid strips instead of a QLinearGradient: Qt's PDF
        # backend can omit gradient brush fills despite drawing the outline.
        self.colorbar_rgb = colorize(
            np.linspace(VMAX, VMIN, COLORBAR_STEPS)[:, None],
            self.palette_name
        )[:, 0, :]
        self.update()

    def set_chain_boundaries(self, enabled):
        self.show_chain_boundaries = bool(enabled)
        self.update()

    def set_palette(self, name):
        self.palette_name = name
        self.update_image()

    @staticmethod
    def plot_geometry(width, height):
        left, top, right, bottom = 140, 35, 180, 115
        free_w = max(1, width - left - right)
        free_h = max(1, height - top - bottom)
        size = min(free_w, free_h)
        x = left + (free_w - size) / 2
        y = top + (free_h - size) / 2
        return x, y, size

    def coordinate_to_token(self, pos, clamp=False):
        x, y, size = self.plot_geometry(self.width(), self.height())
        px, py = pos.x(), pos.y()
        if not clamp and not (x <= px < x + size and y <= py < y + size):
            return None
        fx = min(max((px - x) / size, 0.0), 1.0 - 1e-12)
        fy = min(max((py - y) / size, 0.0), 1.0 - 1e-12)
        n_rows, n_cols = self.array.shape
        return int(fx * n_cols), int(fy * n_rows)

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        point = self.coordinate_to_token(event.pos())
        if point is not None:
            self.drag_start = point
            self.region = (point[0], point[0], point[1], point[1])
            self.update()

    def mouseMoveEvent(self, event):
        if self.drag_start is None:
            return
        point = self.coordinate_to_token(event.pos(), clamp=True)
        x0, y0 = self.drag_start
        x1, y1 = point
        self.region = (min(x0, x1), max(x0, x1),
                       min(y0, y1), max(y0, y1))
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton or self.drag_start is None:
            return
        self.mouseMoveEvent(event)
        self.drag_start = None
        if self.on_region_selected is not None:
            self.on_region_selected(self.region)

    def render_plot(self, painter, width, height, draw_selection=True):
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        painter.fillRect(QtCore.QRectF(0, 0, width, height), QtGui.QColor("white"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#252525"), 1))

        x, y, size = self.plot_geometry(width, height)
        rect = QtCore.QRectF(x, y, size, size)
        painter.drawImage(rect, self.image)
        painter.drawRect(rect)

        # AlphaFold-style separators across BOTH axes. Since the PAE
        # matrix is a token-by-token matrix, every chain transition is
        # at token boundary i / n, not (i - 1) / (n - 1).
        if self.show_chain_boundaries and self.chain_boundaries:
            painter.save()
            pen = QtGui.QPen(
                QtGui.QColor(CHAIN_BOUNDARY_COLOR), CHAIN_BOUNDARY_WIDTH
            )
            painter.setPen(pen)
            n = self.array.shape[0]
            for i in self.chain_boundaries:
                pos = size * i / n
                painter.drawLine(
                    QtCore.QPointF(x + pos, y),
                    QtCore.QPointF(x + pos, y + size)
                )
                painter.drawLine(
                    QtCore.QPointF(x, y + pos),
                    QtCore.QPointF(x + size, y + pos)
                )
            painter.restore()

        if draw_selection and self.region is not None:
            x0, x1, y0, y1 = self.region
            rows, cols = self.array.shape
            box = QtCore.QRectF(
                x + size * x0 / cols,
                y + size * y0 / rows,
                size * (x1 - x0 + 1) / cols,
                size * (y1 - y0 + 1) / rows
            )
            painter.fillRect(box, QtGui.QColor(255, 204, 0, 60))
            painter.save()
            pen = QtGui.QPen(QtGui.QColor("#ff9500"), 2)
            pen.setStyle(QtCore.Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(box)
            painter.restore()

        font = QtGui.QFont("Helvetica")
        font.setPixelSize(19)  # Stable under painter's PDF/SVG/PNG transform
        painter.setFont(font)
        painter.setPen(QtGui.QPen(QtGui.QColor("#252525"), 1))
        rows, cols = self.array.shape

        for i in range(5):
            f = i / 4.0
            px, py = x + f * size, y + f * size
            painter.drawLine(QtCore.QPointF(px, y + size),
                             QtCore.QPointF(px, y + size + 7))
            painter.drawLine(QtCore.QPointF(x - 7, py), QtCore.QPointF(x, py))
            painter.drawText(QtCore.QRectF(px - 45, y + size + 12, 90, 28),
                             QtCore.Qt.AlignCenter, str(round(f * (cols - 1))))
            painter.drawText(QtCore.QRectF(x - 100, py - 14, 84, 28),
                             QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                             str(round(f * (rows - 1))))

        font.setPixelSize(21)
        painter.setFont(font)
        painter.drawText(QtCore.QRectF(x, y + size + 54, size, 32),
                         QtCore.Qt.AlignCenter, "Scored Residues")
        painter.save()
        painter.translate(x - 116, y + size / 2)
        painter.rotate(-90)
        painter.drawText(QtCore.QRectF(-size / 2, -16, size, 32),
                         QtCore.Qt.AlignCenter, "Aligned Residues")
        painter.restore()

        # Fixed colorbar: 31 Å at top (near-white), 0 Å at bottom
        # (dark green). Use many solid vector rectangles, NOT a gradient
        # brush: reliably visible in PDF/SVG/PNG with identical colors.
        cb_x, cb_w = x + size + 35, 22
        bar = QtCore.QRectF(cb_x, y, cb_w, size)
        painter.save()
        painter.setClipRect(bar)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        steps = len(self.colorbar_rgb)
        for i, rgb in enumerate(self.colorbar_rgb):
            y0 = y + size * i / steps
            y1 = y + size * (i + 1) / steps
            painter.fillRect(
                QtCore.QRectF(cb_x, y0, cb_w, (y1 - y0) + 0.25),
                QtGui.QColor(int(rgb[0]), int(rgb[1]), int(rgb[2]))
            )
        painter.restore()
        painter.setPen(QtGui.QPen(QtGui.QColor("#252525"), 1))
        painter.drawRect(bar)

        font.setPixelSize(19)
        painter.setFont(font)
        for value in (0, 10, 20, 31):
            py = y + size * (1 - value / VMAX)
            painter.drawText(QtCore.QRectF(cb_x + 31, py - 15, 48, 30),
                             QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                             str(value))

        font.setPixelSize(21)
        painter.setFont(font)
        painter.save()
        painter.translate(cb_x + 103, y + size / 2)
        painter.rotate(-90)
        painter.drawText(QtCore.QRectF(-size / 2, -16, size, 32),
                         QtCore.Qt.AlignCenter, "PAE (Å)")
        painter.restore()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        try:
            self.render_plot(painter, self.width(), self.height())
        finally:
            painter.end()


class PAEWindow(QtWidgets.QDialog):
    def __init__(self, array, chain_ids=None, res_ids=None, title="PAE Matrix"):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1040, 900)
        self.chain_ids = chain_ids
        self.res_ids = res_ids
        self.atom_mapping = None
        self.original_colors = None
        self.associated_object = None
        self.selection_name = cmd.get_unused_name("pae_region")

        layout = QtWidgets.QVBoxLayout(self)
        toolbar = QtWidgets.QHBoxLayout()
        layout.addLayout(toolbar)
        toolbar.addWidget(QtWidgets.QLabel("Palette:"))
        self.palette_box = QtWidgets.QComboBox()
        self.palette_box.addItems(PALETTES)
        toolbar.addWidget(self.palette_box)

        toolbar.addWidget(QtWidgets.QLabel("Associate object:"))
        self.object_box = QtWidgets.QComboBox()
        self.object_box.setMinimumWidth(180)
        toolbar.addWidget(self.object_box, 1)
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        toolbar.addWidget(self.refresh_btn)

        actions = QtWidgets.QHBoxLayout()
        layout.addLayout(actions)
        self.reset_btn = QtWidgets.QPushButton("Restore colors")
        actions.addWidget(self.reset_btn)
        actions.addStretch()
        self.png_btn = QtWidgets.QPushButton("PNG 300 dpi")
        self.pdf_btn = QtWidgets.QPushButton("PDF")
        self.svg_btn = QtWidgets.QPushButton("SVG")
        for btn in (self.png_btn, self.pdf_btn, self.svg_btn):
            actions.addWidget(btn)
        if QtSvg is None:
            self.svg_btn.setEnabled(False)
            self.svg_btn.setToolTip("QtSvg is not available in this PyMOL build")

        self.canvas = PAECanvas(array, chain_ids=chain_ids)
        self.boundaries_box = QtWidgets.QCheckBox("Chain boundaries")
        self.boundaries_box.setChecked(True)
        self.boundaries_box.setEnabled(bool(self.canvas.chain_boundaries))
        self.boundaries_box.setToolTip(
            "Show separators where token_chain_ids changes; applies to exports"
        )
        toolbar.addWidget(self.boundaries_box)
        layout.addWidget(self.canvas, 1)
        self.status = QtWidgets.QLabel(
            "Choose a matching structure, then drag a rectangle across the PAE plot."
        )
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.palette_box.currentTextChanged.connect(self.canvas.set_palette)
        self.boundaries_box.toggled.connect(self.canvas.set_chain_boundaries)
        self.refresh_btn.clicked.connect(self.refresh_objects)
        self.object_box.currentTextChanged.connect(self.associate_object)
        self.reset_btn.clicked.connect(self.restore_colors)
        self.png_btn.clicked.connect(self.save_png)
        self.pdf_btn.clicked.connect(self.save_pdf)
        self.svg_btn.clicked.connect(self.save_svg)
        self.canvas.on_region_selected = self.highlight_region

        self.refresh_objects()

    def refresh_objects(self):
        current = self.object_box.currentText()
        objects = [n for n in cmd.get_names("objects")
                   if cmd.get_type(n) == "object:molecule"]
        self.object_box.blockSignals(True)
        self.object_box.clear()
        self.object_box.addItem("— Choose structure —")
        self.object_box.addItems(objects)
        if current in objects:
            self.object_box.setCurrentText(current)
        else:
            self.object_box.setCurrentIndex(0)
        self.object_box.blockSignals(False)
        if self.object_box.currentIndex() == 0 and self.associated_object:
            self.associate_object("")

    def associate_object(self, name):
        # Revert previous object before changing the association.
        self.restore_colors()
        self.associated_object = None
        self.atom_mapping = None
        self.original_colors = None
        self.canvas.region = None
        self.canvas.update()
        if not name or name.startswith("—"):
            self.status.setText("Choose a molecular object to enable selections.")
            return
        try:
            mapping, colors, summary = token_atom_mapping(
                name, self.chain_ids, self.res_ids, self.canvas.array.shape[0]
            )
        except Exception as exc:
            self.status.setText(f"Cannot associate '{name}': {exc}")
            return
        self.associated_object = name
        self.atom_mapping = mapping
        self.original_colors = colors
        self.status.setText(f"Associated '{name}': {summary}. Drag to select PAE region.")

    def highlight_region(self, region):
        if self.atom_mapping is None or self.associated_object is None:
            self.status.setText("No valid associated structure: choose one before selecting.")
            return
        if self.associated_object not in cmd.get_names("objects"):
            self.status.setText("Associated object was deleted. Refresh and select another.")
            return
        x0, x1, y0, y1 = region
        # Highlight BOTH partners of the selected PAE rectangle (union).
        token_ids = set(range(x0, x1 + 1)) | set(range(y0, y1 + 1))
        atom_ids = sorted({idx for token in token_ids
                           for idx in self.atom_mapping[token]})
        if not atom_ids:
            self.status.setText("This PAE region does not map to any modeled atoms.")
            return
        try:
            # select_list uses PyMOL atom *indices* specific to one object.
            cmd.select_list(self.selection_name, self.associated_object,
                            atom_ids, mode="index")
            obj = "(%" + self.associated_object + ")"
            cmd.color("gray70", obj)
            cmd.color("yellow", "(%" + self.selection_name + ")")
            cmd.enable(self.selection_name)
            self.status.setText(
                f"{self.selection_name}: scored {x0}–{x1}; aligned {y0}–{y1}; "
                f"{len(token_ids)} tokens, {len(atom_ids)} atoms."
            )
        except Exception as exc:
            self.status.setText(f"Selection error: {exc}")

    def restore_colors(self):
        if self.associated_object and self.original_colors is not None:
            if self.associated_object in cmd.get_names("objects"):
                obj = "(%" + self.associated_object + ")"
                try:
                    cmd.alter(obj, "color=original.get(index, color)",
                              space={"original": self.original_colors})
                    cmd.recolor(obj)
                except Exception as exc:
                    self.status.setText(f"Could not restore colors: {exc}")
        if self.selection_name in cmd.get_names("selections"):
            cmd.delete(self.selection_name)
        self.canvas.region = None
        self.canvas.update()

    def _choose_path(self, title, suffix, filter_text):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, title, "pae." + suffix, filter_text
        )
        if path and not path.lower().endswith("." + suffix):
            path += "." + suffix
        return path

    def _export(self, painter):
        # Exports deliberately omit the interactive yellow selection rectangle.
        self.canvas.render_plot(painter, FIG_W, FIG_H, draw_selection=False)

    def save_png(self):
        path = self._choose_path("Save 300-dpi PNG", "png", "PNG (*.png)")
        if not path:
            return
        w = round(FIGURE_WIDTH_MM / 25.4 * PNG_DPI)
        h = round(w * FIG_H / FIG_W)
        image = QtGui.QImage(w, h, QtGui.QImage.Format_ARGB32)
        image.fill(QtGui.QColor("white"))
        dpm = round(PNG_DPI * 1000 / 25.4)
        image.setDotsPerMeterX(dpm)
        image.setDotsPerMeterY(dpm)
        painter = QtGui.QPainter(image)
        try:
            painter.setViewport(QtCore.QRect(0, 0, w, h))
            painter.setWindow(QtCore.QRect(0, 0, FIG_W, FIG_H))
            self._export(painter)
        finally:
            painter.end()
        if not image.save(path, "PNG"):
            QtWidgets.QMessageBox.warning(self, "PNG export", "Could not save PNG.")

    def save_pdf(self):
        path = self._choose_path("Save vector PDF", "pdf", "PDF (*.pdf)")
        if not path:
            return
        # The printable area is exactly 200 mm wide, with 5 mm margins.
        content_h_mm = FIGURE_WIDTH_MM * FIG_H / FIG_W
        writer = QtGui.QPdfWriter(path)
        writer.setResolution(300)
        writer.setPageSize(QtGui.QPageSize(
            QtCore.QSizeF(FIGURE_WIDTH_MM + 10, content_h_mm + 10),
            QtGui.QPageSize.Millimeter
        ))
        writer.setPageMargins(QtCore.QMarginsF(5, 5, 5, 5))
        painter = QtGui.QPainter(writer)
        try:
            printable = writer.pageLayout().paintRectPixels(writer.resolution())
            painter.setViewport(printable)
            painter.setWindow(QtCore.QRect(0, 0, FIG_W, FIG_H))
            self._export(painter)
        finally:
            painter.end()

    def save_svg(self):
        if QtSvg is None:
            return
        path = self._choose_path("Save vector SVG", "svg", "SVG (*.svg)")
        if not path:
            return
        generator = QtSvg.QSvgGenerator()
        generator.setFileName(path)
        generator.setSize(QtCore.QSize(FIG_W, FIG_H))
        generator.setViewBox(QtCore.QRect(0, 0, FIG_W, FIG_H))
        generator.setTitle("AlphaFold 3 PAE matrix")
        generator.setDescription("PAE image with vector axes and labels")
        painter = QtGui.QPainter(generator)
        try:
            self._export(painter)
        finally:
            painter.end()


def show_array(array, chain_ids=None, res_ids=None, title="PAE Matrix"):
    array = np.asarray(array, dtype=float)
    if array.ndim != 2 or not array.size or array.shape[0] != array.shape[1]:
        raise ValueError("Expected a nonempty square PAE matrix.")
    window = PAEWindow(array, chain_ids=chain_ids, res_ids=res_ids, title=title)
    window.show()
    _image_windows.append(window)  # Hold a reference: Qt window remains alive.
    return window


def display_pae(confidence_path):
    path = Path(confidence_path).expanduser()
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if "pae" not in data:
        raise ValueError(f"No 'pae' matrix in {path}")
    return show_array(
        data["pae"],
        chain_ids=data.get("token_chain_ids"),
        res_ids=data.get("token_res_ids"),
        title=f"PAE — {path.name}"
    )

# PyMOL CLI usage: display_pae path/to/confidences.json
cmd.extend("display_pae", display_pae)
