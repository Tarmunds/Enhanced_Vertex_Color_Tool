import importlib

bl_info = {
    "name": "Enhanced Vertex Color Tool",
    "blender": (4, 2, 0),
    "category": "Object",
    "version": (3, 0, 1),
    "author": "Tarmunds",
    "description": "Advanced vertex color tools: fill, gradients, randomization, baked AO in vertex color, bake texture in vertex color, and switch/clear channels.",
    "doc_url": "https://tarmunds.gumroad.com/l/EnhancedVertexColorTool",
    "tracker_url": "https://discord.gg/h39W5s5ZbQ",
    "location": "View3D > Tarmunds Addons > Export Unreal",
}


_SubModules = [
    "VCT.Functions",
    "VCT.Properties",
    "VCT.Operators",
    "VCT.Panels",
]

_modules = tuple(importlib.import_module(f".{name}", __name__) for name in _SubModules)

for module in _modules:
    importlib.reload(module)

def register():
    for module in _modules:
        if hasattr(module, "register"):
            module.register()

def unregister():
    for module in reversed(_modules):
        if hasattr(module, "unregister"):
            module.unregister()

