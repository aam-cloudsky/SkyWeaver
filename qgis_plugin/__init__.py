# __init__.py


def classFactory(iface):
    from .mainPlugin import SkyWeaverPlugin

    return SkyWeaverPlugin(iface)
