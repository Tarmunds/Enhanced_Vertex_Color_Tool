# Enhanced Vertex Color Tool (VCT)

A Blender addon that provides advanced vertex color editing and visualization tools. It enhances the default vertex color workflow with powerful operations such as gradients, randomization, AO baking, channel management, and inspection.

---

## ✨ Features

- **Viewport Utilities**
  - Toggle between **Vertex Color** and **Material** viewport display.
  - Switch between **Flat** and **Studio** lighting for better visualization.
  
- **Fill Tools**
  - Fill with custom color, black, white, or single channel values.
  - Per-channel fill with adjustable intensity.

- **Gradient Tools**
  - Linear and radial gradient fills.
  - World-space, local, or active-object-inherited direction.
  - Invert gradient, global/local control.
  - Interactive **Trace Gradient** directly in the viewport.

- **Randomization**
  - Random fill across entire mesh, per connected component, or per UV island.
  - Optional normalization of values.

- **Channel Management**
  - Clear channels to 0 or 1.
  - Invert channel values.
  - Switch channels (e.g., R → G).

- **Ambient Occlusion Baking**
  - Bake AO into a chosen vertex color channel.
  - Control resolution, UV map, and progress tracking.

- **Inspection Mode**
  - Preview a single channel as grayscale.
  - Accept or discard changes after editing in inspect mode.
  - Special tools available while inspecting (fill value, randomize, gradients, etc.).

---

## 📦 Installation

1. Download the addon folder (containing `Panels.py`, `Properties.py`, `Functions.py`, `Operators.py`).
2. In Blender, go to **Edit > Preferences > Add-ons > Install**.
3. Select the addon `.zip` or the folder.
4. Enable **Enhanced Vertex Color Tool** in the Add-ons list.

---

## 🖥️ Usage

Once installed, the addon appears in the **3D Viewport > Sidebar (N-panel) > Tarmunds Addons > Enhanced Vertex Color Tool**.

### Workflow Example
1. Select a mesh.
2. Toggle **See Vertex Color** to preview vertex colors in the viewport.
3. Use **Fill Color** or **Gradient Fill** to apply vertex color data.
4. Optionally use **AO to Vertex Color** to bake lighting data.

---

## 🛠️ Operators (`Operators.py`)

| Operator | ID | Description |
|----------|----|-------------|
| **See Vertex Color** | `vct.see_vcolor` | Toggle viewport shading between Vertex Color & Material. |
| **Shade Flat** | `vct.shade_flat` | Toggle between Flat and Studio lighting. |
| **Fill Color** | `vct.fill_color` | Fill selected meshes with chosen color. |
| **Fill Black/White** | `vct.fill_black`, `vct.fill_white` | Quick fill with black/white. |
| **Fill 1 Channel** | `vct.fill_1channel` | Fill a single channel with constant value. |
| **Gradient Fill** | `vct.gradient_fill` | Fill with directional gradient. |
| **Random Fill** | `vct.random_fill` | Fill with randomized values. |
| **Inspect Color** | `vct.inspect_color` | Enable inspect mode for a channel. |
| **Discard Inspect Changes** | `vct.discard_inspect_changes` | Exit inspection, discard changes. |
| **Inspect Fill Value** | `vct.inspect_fill_value` | Fill inspection channel with set value. |
| **Clear Channel** | `vct.clear_channel` | Reset channel values (0 or 1). |
| **Switch Channel** | `vct.switch_channel` | Swap two channels. |
| **AO to Vertex Color** | `vct.ao_to_vertex_color` | Bake AO into vertex colors. |
| **Invert Channel** | `vct.invert_channel` | Invert channel values. |
| **Trace Gradient** | `vct.trace_gradient` | Interactive gradient tool in 3D View. |

---

## 🧩 Development

- Code organized into:
  - `Panels.py` → UI
  - `Properties.py` → Addon properties
  - `Functions.py` → Core logic
  - `Operators.py` → Blender operators

- Each module registers/unregisters its classes independently.


---

## 📜 License

MIT License 
