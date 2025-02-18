# Enhanced Vertex Color Tool for Blender

The **Enhanced Vertex Color Tool** is a Blender addon designed to streamline the process of working with vertex colors in 3D models. It offers a set of advanced tools for filling, gradient-based coloring, randomizing vertex colors, baking textures or AO, switching or clearing channels, all within an intuitive panel interface.

## Features

- **Vertex Color Preview**: Preview the vertex color on all meshes. This allows for quick visual feedback on the color selection or effect you want to apply.
- **Vertex Color RGB Fill**: Fill the object vertex color with the selected color in the RGB channels.
- **Vertex Color Alpha Fill**: Fill the object vertex color with the selected value in the ALPHA channel.
- **Vertex Color Gradient Fill**: Apply a gradient to the vertex colors based on object coordinates (e.g., bottom-top, left-right, front-back). You can target specific color channels (Red, Green, Blue) and invert the gradient if needed. The gradient can also be based on world coordinates. Additionally, you can spread the gradient across multiple selected meshes in world space only. Lastly, you can adjust the gradient range by modifying the start and end values.
- **Randomize Vertex Colors**: Randomize the vertex color value in one channel on selected mesh objects. You can also "normalize" the values, which ensures that all meshes have a unique value offset, fully utilizing the color range. This approach is less organic but can be useful for certain effects.
- **Bake Texture to Channel**: Bake the texture to the specified channel, using the UV index you chose.
- **Bake AO to Channel**: Compute an ambient occlusion using Cycles and bake it to the specified vertex color channel. Note that this process can take some time depending on your mesh density. (Currently aware of an issue with multiple meshes, where you need to launch the operation twice for it to apply to all meshes. This is being worked on.)
- **Switch Channel Data**: This allows you to exchange data between channels. It is useful for tweaking or rearranging your channel usage.
- **Clear Channel Data**: Clear a specific channel without affecting others. You can clear the channel to 0 or 1.

### Panel Interface

The addon introduces a custom panel in the **3D View** under the **Tarmunds Addons** tab.  
All the operators are organized into dropdown sections to ease readability.  
At the top of the panel, you'll find the boolean operator to turn the vertex color preview on or off.

## Demo
Showcase of the vertex color preview, fill color and fill alpha :
![seeandapply](https://github.com/Tarmunds/Enhanced_Vertex_Color_Tool/blob/main/Images/VCT_SeeAndApply.gif)

Showcase of the vertex color gradient :
![gradient](https://github.com/Tarmunds/Enhanced_Vertex_Color_Tool/blob/main/Images/VCT_Gradient.gif)

Showcase of the vertex color Randomize :
![random](https://github.com/Tarmunds/Enhanced_Vertex_Color_Tool/blob/main/Images/VCT_Random.gif)

Showcase of the Bake Texture :
![baketexture](https://github.com/Tarmunds/Enhanced_Vertex_Color_Tool/blob/main/Images/VCT_Texture.gif)

Showcase of the Bake Ambiant Occlusion, Switch Channels and Clear Channels :
![ao](https://github.com/Tarmunds/Enhanced_Vertex_Color_Tool/blob/main/Images/VCT_AoSwitchClear.gif)

## Installation

1. Download the latest version from GitHub or Gumroad.
2. Open Blender and go to **Edit > Preferences > Add-ons**.
3. Click **Install**, navigate to the downloaded addon file, and select it.
4. Enable the addon by checking the box next to **Enhanced Vertex Color Tool** in the **Add-ons** tab.
5. Enjoy!

## Usage

- After installation, the **Enhanced Vertex Color Tool** panel can be found in the **3D View > Tarmunds Addons** tab.
- Select the mesh objects you want to modify, and use the provided operators. All operators iterate through all selected meshes to streamline your workflow.

## Credits

- **Author**: Tarmunds - Kostia Perry

## License

Distributed under the GNU General Public License v3. See `LICENSE` for more information.
