__version__ = "0.0.1"


def register_nodes_metadata():
    return {
        "description": "Nodes specific to the GEM-STEP data collection setup.",
        "nodes": [
            "gsdcp.umc1820_node:UMC1820",
            "gsdcp.files_watcher_node:FilesWatcher",
            "gsdcp.droidcam_node:DroidCam",
            "gsdcp.ipwebcam_node:IPWebCam",
            "gsdcp.screen_subscriber_node:ScreenSubscriber",
        ],
    }
