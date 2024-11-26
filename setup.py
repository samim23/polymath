from setuptools import setup

setup(
    name='polymath',
    version='0.1.0',
    packages=['.'],
    install_requires=[
        "nendo>=0.1.2",
        "nendo_plugin_classify_core>=0.2.3",
        "nendo_plugin_quantize_core>=0.1.2",
        "nendo_plugin_stemify_demucs>=0.1.0",
        "nendo_plugin_loopify>=0.1.1",
        "yt_dlp>=2023.11.16",
        "tensorflow",
    ],
)
