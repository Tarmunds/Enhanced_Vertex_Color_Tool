# Vertex Color Tool for Blender

The **Enhanced Vertex Color Tool** is a powerful Blender addon designed to streamline the process of working with vertex colors in 3D models. It offers a set of advanced tools for filling, gradient-based coloring, randomizing vertex colors, and previewing the color changes before applying them, all within an intuitive panel interface.

## Features

- **Vertex Color Fill Preview**: Preview the vertex color fill on selected mesh objects before committing the change. This allows for quick visual feedback on the color selection.
- **Vertex Color Gradient Fill**: Apply a gradient to the vertex colors based on object coordinates (e.g., bottom-top, left-right, front-back) and target a specific color channel (Red, Green, Blue).
- **Randomize Vertex Colors**: Randomize the vertex colors on selected mesh objects for a more organic and varied appearance, with control over the target color channel.
  
### Key Operators

1. **Preview Vertex Color Fill** (`object.vertex_color_fill_preview`): Preview the vertex color fill before applying it.
2. **Apply Gradient to Vertex Color** (`object.vertex_color_gradient_fill`): Apply a gradient to the selected mesh vertices based on chosen direction and target color channel.
3. **Randomize Vertex Colors** (`object.vertex_color_randomize`): Randomly modify the colors of selected vertices in the chosen channel.

### Panel Interface

The addon introduces a custom panel in the **3D View** under the **Tarmunds Addons** tab with the following sections:
- **Fill Colors**: Choose a fill color and preview/apply the color to the selected mesh.
- **Gradient Fill**: Select the gradient direction and target color channel, then apply the gradient to the vertices.
- **Randomize Colors**: Randomize the colors in the chosen channel for selected mesh objects.

## Installation

1. Download or clone the repository.
2. Open Blender and go to **Edit > Preferences > Add-ons**.
3. Click **Install**, navigate to the downloaded addon file, and select it.
4. Enable the addon by checking the box next to **Enhanced Vertex Color Tool** in the **Add-ons** tab.

## Usage

- After installation, the **Enhanced Vertex Color Tool** panel can be found in the **3D View > Tarmunds Addons** tab.
- Select the mesh objects you want to modify, and use the provided operators to fill, apply gradients, or randomize the vertex colors.
  
## Custom Properties

- **Vertex Fill Color**: Choose the color to fill for the **Preview Fill** or **Apply Fill** actions.
- **Gradient Direction**: Choose the direction for applying the gradient (Bottom-Top, Left-Right, Front-Back).
- **Gradient Target Channel**: Select the color channel (Red, Green, Blue) to apply the gradient to.
- **Random Target Channel**: Select the color channel (Red, Green, Blue) to randomize.

## Requirements

- Blender 2.80 or higher.

## Credits

- **Author**: Tarmunds

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

This README provides a concise overview of the tool's features, installation steps, and usage instructions. It will help users understand the capabilities of your addon and how to get started.