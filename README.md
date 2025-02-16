# Vertex Color Tool for Blender

The **Enhanced Vertex Color Tool** is a Blender addon designed to streamline the process of working with vertex colors in 3D models. It offers a set of advanced tools for filling, gradient-based coloring, randomizing vertex colors, baking texture or AO, switch or clear channel, all within an intuitive panel interface.

## Features

- **Vertex Color Preview**: Preview the vertex color on all meshes. This allows for quick visual feedback on the color selection, or effect you want to apply.
- **Vertex Color RGB fill**: Fill the object vertex color with the selected color in the RGB channels.
- **Vertex Color Alpha Fill**: Fill the object vertex color with the selected value in the ALPHA channel.
- **Vertex Color Gradient Fill**: Apply a gradient to the vertex colors based on object coordinates (e.g., bottom-top, left-right, front-back) and target a specific color channel (Red, Green, Blue). You can invert the gradient if needed. Also make the gradient based on the world coordinate. You can make the gradient based on multiple selection, to have the gradient that''s spread accross selected meshes (in world space only). And lastly you can adjust, if needed, the range of the gradient by changing the start and end value.
- **Randomize Vertex Colors**: Randomize the vertex color value of in one channel, on selected mesh objects. You can also "noramlized" it, what it does is that it ensure that you do have the same vallue offset between each meshes, all meshes will have a unique value, and the range is fully used, but it's a bit less organic (depending of what you do with it afterward)
- **Bake Texture to Channel**: Bake the texture to the specified channel, using the UV index you choosed
- **Bake Ao to Channel**: compute with Cycle an ambiant occlusion, and bake it to the specify vertex color. Note that this can take several times based on you mesh density. (I'm aware of one issue with multiple meshes, where you have to launch the operation two time before it apply it to the channel for all meshes, working on it)
- **Switch Channel Data**: this allow you to exchange data from one channel to another. Quite useful for tweaking or rearanging your channels use.
- **Clear Channel Data**: This allow you to clear a specific channel without affecting other, you can clear to 0 or 1
  
### Panel Interface

The addon introduces a custom panel in the **3D View** under the **Tarmunds Addons** tab.
All the operator are in dropdown section to ease the readability
On top of it you can find the boolean operator to turn on/off the vertex color preview

## Installation

1. Download on github or gumorad the latest version
2. Open Blender and go to **Edit > Preferences > Add-ons**.
3. Click **Install**, navigate to the downloaded addon file, and select it.
4. Enable the addon by checking the box next to **Enhanced Vertex Color Tool** in the **Add-ons** tab.
5. Enjoy 

## Usage

- After installation, the **Enhanced Vertex Color Tool** panel can be found in the **3D View > Tarmunds Addons** tab.
- Select the meshes objects you want to modify, and use the provided operators. All operator iterate throught all selected meshes to ease the workflow.
  

## Credits

- **Author**: Tarmunds - Kostia Perry

## License

Distributed under the MIT License. See `LICENSE` for more information.
