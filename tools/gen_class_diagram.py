"""Sinh ảnh class diagram cho NomNaSite."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np

# ── Palette ──────────────────────────────────────────────────────────────────
C_KERAS   = "#2563eb"   # TF/Keras classes
C_SERVICE = "#7c3aed"   # Services
C_HANDLER = "#059669"   # Handlers
C_PAGE    = "#d97706"   # Pages
C_MODULE  = "#64748b"   # External/base

WHITE   = "#ffffff"
HEADER  = "#1e293b"
TXT     = "#1e293b"
DIVIDER = "#cbd5e1"

FIG_W, FIG_H = 28, 20

# ── Class definitions ─────────────────────────────────────────────────────────
classes = [
    # (id, label, section_color, x, y, w, h,
    #  attributes_list, methods_list)

    # ── Keras base (external) ────────────────────────────────────────────────
    ("tf_model", "tf.keras.Model",
     C_MODULE, 0.02, 0.87, 0.13, 0.10,
     [], []),

    ("tf_layer", "tf.keras.layers.Layer",
     C_MODULE, 0.17, 0.87, 0.17, 0.10,
     [], []),

    # ── Layers ───────────────────────────────────────────────────────────────
    ("ConvBnRelu", "ConvBnRelu",
     C_KERAS, 0.02, 0.68, 0.16, 0.14,
     ["filters: int", "kernel_size: int", "padding: str"],
     ["call(inputs, training)"]),

    ("DeConvMap", "DeConvMap",
     C_KERAS, 0.21, 0.68, 0.16, 0.14,
     ["filters: int"],
     ["call(inputs, training)"]),

    # ── Models ───────────────────────────────────────────────────────────────
    ("CRNN", "CRNN",
     C_KERAS, 0.02, 0.42, 0.20, 0.22,
     ["max_length: int = 24", "height: int = 432",
      "width:  int = 48",   "num2char: StringLookup",
      "model:  keras.Model"],
     ["_build_model()",
      "distortion_free_resize(image)",
      "process_image(image)",
      "ctc_decode(predictions, max_length)",
      "tokens2texts(batch_tokens)",
      "predict_one_patch(patch_img)"]),

    ("DBNet", "DBNet",
     C_KERAS, 0.25, 0.42, 0.20, 0.22,
     ["model:         keras.Model",
      "post_processor: PostProcessor"],
     ["_build_model(k=50)",
      "resize_image_short_side(image)",
      "predict_one_page(raw_image)"]),

    ("PostProcessor", "PostProcessor",
     C_KERAS, 0.48, 0.42, 0.20, 0.22,
     ["thresh:          float = 0.3",
      "min_box_score:   float = 0.7",
      "max_candidates:  int   = 500",
      "shrink_ratio:    float = 1.1",
      "dilate_ratio:    float = 1.5"],
     ["__call__(binarize_map, batch_sizes)",
      "bitmap2quads(pred, bitmap, size)",
      "shrink_and_dilate(box)",
      "box_score_fast(bitmap, box)",
      "get_mini_boxes(contour)"]),

    # ── Services ─────────────────────────────────────────────────────────────
    ("OcrSession", "ocr_session",
     C_SERVICE, 0.02, 0.14, 0.20, 0.24,
     ["_USE_CLOUD: bool",
      "_supa: SupabaseClient",
      "_SQLITE_PATH: str"],
     ["get_or_create_session()",
      "save_boxes(session_id, data)",
      "get_boxes(session_id)",
      "save_correction(session_id, idx, text)",
      "get_sessions(username)",
      "toggle_favorite(session_id)",
      "delete_session(session_id)",
      "upload_image() / download_image()"]),

    ("TranslationLog", "translation_log",
     C_SERVICE, 0.25, 0.14, 0.18, 0.24,
     ["DB_PATH: str"],
     ["create_table()",
      "save_entry(username, in, out)",
      "get_entries(username, limit)",
      "toggle_star(entry_id)",
      "delete_entry(entry_id)",
      "sync_from_local(username, raw)"]),

    ("FirebaseRoles", "firebase_roles",
     C_SERVICE, 0.46, 0.14, 0.16, 0.24,
     ["_firebase: pyrebase.App",
      "_db: Database"],
     ["get_role(email, id_token)",
      "set_role(email, role, token)",
      "is_admin_role(email, token)"]),

    # ── Handlers ─────────────────────────────────────────────────────────────
    ("Translator", "translator",
     C_HANDLER, 0.65, 0.68, 0.17, 0.22,
     ["_phrase_phonetic: dict",
      "_phrase_meaning:  dict",
      "_char_dict:       dict"],
     ["_load_db()",
      "db_hanviet(text)",
      "db_meaning(text)",
      "ai_nom_to_vi(text)",
      "ai_vi_to_nom(text)"]),

    ("BBox", "bbox",
     C_HANDLER, 0.65, 0.42, 0.17, 0.22,
     [],
     ["generate_initial_drawing(boxes)",
      "transform_fabric_box(box)",
      "order_points_clockwise(pts)",
      "order_boxes4nom(boxes)",
      "get_patch(image, box)"]),

    ("Asset", "asset",
     C_HANDLER, 0.84, 0.68, 0.14, 0.14,
     ["DBNet model",
      "CRNN  model"],
     ["load_models()",
      "hash_bytes(data)",
      "retrieve_image(file)"]),

    # ── Pages ─────────────────────────────────────────────────────────────────
    ("PageNomna", "nomnasite",
     C_PAGE, 0.65, 0.14, 0.16, 0.24,
     [],
     ["show()",
      "→ load_models()",
      "→ predict_one_page()",
      "→ predict_one_patch()",
      "→ db_hanviet / meaning()",
      "→ get_or_create_session()"]),

    ("PageHistory", "history",
     C_PAGE, 0.83, 0.14, 0.15, 0.24,
     [],
     ["show()",
      "→ get_sessions()",
      "→ get_session_boxes()",
      "→ toggle_favorite()",
      "→ delete_session()",
      "→ export TXT/DOCX/PDF"]),
]

# ── Relations: (from_id, to_id, style, label) ────────────────────────────────
# style: 'inherit' | 'compose' | 'use'
relations = [
    ("ConvBnRelu", "tf_layer",   "inherit", ""),
    ("DeConvMap",  "tf_layer",   "inherit", ""),
    ("CRNN",       "tf_model",   "inherit", ""),
    ("DBNet",      "tf_model",   "inherit", ""),

    ("DeConvMap",  "ConvBnRelu", "compose", "uses"),
    ("CRNN",       "ConvBnRelu", "compose", "uses"),
    ("DBNet",      "ConvBnRelu", "compose", "uses"),
    ("DBNet",      "DeConvMap",  "compose", "uses"),
    ("DBNet",      "PostProcessor", "compose", "has"),

    ("DBNet",      "BBox",       "use", "calls"),
    ("PageNomna",  "Asset",      "use", "loads"),
    ("PageNomna",  "DBNet",      "use", "detects"),
    ("PageNomna",  "CRNN",       "use", "recognizes"),
    ("PageNomna",  "Translator", "use", "translates"),
    ("PageNomna",  "OcrSession", "use", "saves"),
    ("PageHistory","OcrSession", "use", "reads"),
]

# ── Draw helper ───────────────────────────────────────────────────────────────
def draw_class(ax, cid, label, color, x, y, w, h, attrs, methods):
    """Draw a UML class box."""
    # Shadow
    shadow = mpatches.FancyBboxPatch(
        (x + 0.003, y - 0.003), w, h,
        boxstyle="round,pad=0.005", linewidth=0,
        facecolor="#94a3b8", alpha=0.35, zorder=1,
        transform=ax.transAxes,
    )
    ax.add_patch(shadow)

    # Body
    body = mpatches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.005", linewidth=1.4,
        edgecolor=color, facecolor=WHITE, zorder=2,
        transform=ax.transAxes,
    )
    ax.add_patch(body)

    # Header bar
    rows = 1 + len(attrs) + (1 if attrs else 0) + len(methods)
    row_h = h / max(rows, 1)
    header_h = row_h

    header = mpatches.FancyBboxPatch(
        (x, y + h - header_h), w, header_h,
        boxstyle="round,pad=0.005", linewidth=0,
        facecolor=color, zorder=3,
        transform=ax.transAxes,
    )
    ax.add_patch(header)

    ax.text(x + w / 2, y + h - header_h / 2, label,
            ha='center', va='center', fontsize=7.5, fontweight='bold',
            color=WHITE, zorder=4, transform=ax.transAxes,
            clip_on=True)

    cursor = y + h - header_h
    pad = 0.006

    # Attributes section
    if attrs:
        cursor -= row_h * 0.15
        ax.plot([x, x + w], [cursor, cursor], color=DIVIDER,
                linewidth=0.8, zorder=4, transform=ax.transAxes)
        for a in attrs:
            cursor -= row_h * 0.85 / max(len(attrs), 1)
            ax.text(x + pad, cursor + row_h * 0.3, f"  {a}",
                    ha='left', va='center', fontsize=5.8,
                    color="#475569", zorder=4, transform=ax.transAxes,
                    clip_on=True)

    # Methods section
    if methods:
        ax.plot([x, x + w], [cursor, cursor], color=DIVIDER,
                linewidth=0.8, zorder=4, transform=ax.transAxes)
        for m in methods:
            cursor -= row_h * 0.85 / max(len(methods), 1)
            prefix = "+" if not m.startswith("→") else " "
            ax.text(x + pad, cursor + row_h * 0.3, f"  {prefix}{m}",
                    ha='left', va='center', fontsize=5.8,
                    color="#0f172a", zorder=4, transform=ax.transAxes,
                    clip_on=True)


def center(cls_map, cid):
    _, _, _, x, y, w, h, _, _ = cls_map[cid]
    return (x + w / 2, y + h / 2)


def top_center(cls_map, cid):
    _, _, _, x, y, w, h, _, _ = cls_map[cid]
    return (x + w / 2, y + h)


def bottom_center(cls_map, cid):
    _, _, _, x, y, w, h, _, _ = cls_map[cid]
    return (x + w / 2, y)


def right_center(cls_map, cid):
    _, _, _, x, y, w, h, _, _ = cls_map[cid]
    return (x + w, y + h / 2)


def left_center(cls_map, cid):
    _, _, _, x, y, w, h, _, _ = cls_map[cid]
    return (x, y + h / 2)


# ── Main ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.axis('off')
fig.patch.set_facecolor("#f8fafc")
ax.set_facecolor("#f8fafc")

# Title
ax.text(0.5, 0.975, "NomNaSite — Class Diagram",
        ha='center', va='top', fontsize=16, fontweight='bold',
        color=HEADER, transform=ax.transAxes)

# Section labels
for label, x, y, color in [
    ("«Keras Layers»",   0.02,  0.83, C_KERAS),
    ("«Models»",         0.02,  0.65, C_KERAS),
    ("«Services»",       0.02,  0.39, C_SERVICE),
    ("«Handlers»",       0.65,  0.65, C_HANDLER),
    ("«Pages»",          0.65,  0.39, C_PAGE),
]:
    ax.text(x, y, label, fontsize=7, color=color, style='italic',
            fontweight='bold', transform=ax.transAxes, alpha=0.7)

# Index classes by id
cls_map = {c[0]: c for c in classes}

# Draw classes
for c in classes:
    cid, label, color, x, y, w, h, attrs, methods = c
    draw_class(ax, cid, label, color, x, y, w, h, attrs, methods)

# Draw relations
ARROW_CFG = {
    'inherit': dict(arrowstyle='-|>', color='#475569', lw=1.3, linestyle='solid'),
    'compose': dict(arrowstyle='->', color='#2563eb', lw=1.0, linestyle='dashed'),
    'use':     dict(arrowstyle='->', color='#059669', lw=0.9, linestyle='dotted'),
}

drawn_labels = []
for (fid, tid, style, lbl) in relations:
    if fid not in cls_map or tid not in cls_map:
        continue
    cfg = ARROW_CFG[style]
    fx, fy = bottom_center(cls_map, fid)
    tx, ty = top_center(cls_map, tid)

    # Prefer horizontal arrow if same horizontal band
    _, _, _, fx0, fy0, fw, fh, _, _ = cls_map[fid]
    _, _, _, tx0, ty0, tw, th, _, _ = cls_map[tid]
    mid_f = fy0 + fh / 2
    mid_t = ty0 + th / 2

    if abs(mid_f - mid_t) < 0.12:
        if fx0 > tx0 + tw:
            fx, fy = left_center(cls_map, fid)
            tx, ty = right_center(cls_map, tid)
        elif tx0 > fx0 + fw:
            fx, fy = right_center(cls_map, fid)
            tx, ty = left_center(cls_map, tid)

    ax.annotate("", xy=(tx, ty), xytext=(fx, fy),
                xycoords='axes fraction', textcoords='axes fraction',
                arrowprops=dict(
                    arrowstyle=cfg['arrowstyle'],
                    color=cfg['color'],
                    lw=cfg['lw'],
                    linestyle=cfg['linestyle'],
                    connectionstyle="arc3,rad=0.0",
                ),
                zorder=0)

    if lbl:
        mx, my = (fx + tx) / 2, (fy + ty) / 2
        ax.text(mx, my, lbl, fontsize=5, color=cfg['color'],
                ha='center', va='bottom', transform=ax.transAxes,
                bbox=dict(facecolor='#f8fafc', edgecolor='none', pad=1),
                zorder=5)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(facecolor=C_KERAS,   label='TF/Keras (Model & Layer)'),
    mpatches.Patch(facecolor=C_SERVICE, label='Services (DB / Cloud)'),
    mpatches.Patch(facecolor=C_HANDLER, label='Handlers (Logic)'),
    mpatches.Patch(facecolor=C_PAGE,    label='Pages (UI)'),
    mpatches.Patch(facecolor=C_MODULE,  label='External / Base class'),
    plt.Line2D([0],[0], color='#475569', lw=1.3, label='Inheritance'),
    plt.Line2D([0],[0], color='#2563eb', lw=1.0, linestyle='dashed',  label='Composition / uses'),
    plt.Line2D([0],[0], color='#059669', lw=0.9, linestyle='dotted',  label='Dependency / calls'),
]
ax.legend(handles=legend_items, loc='lower right',
          fontsize=7, framealpha=0.92, edgecolor='#cbd5e1',
          bbox_to_anchor=(1.0, 0.0))

plt.tight_layout(pad=0.3)
out = "class_diagram.png"
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f"Saved: {out}")
