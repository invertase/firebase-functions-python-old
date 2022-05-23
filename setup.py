from setuptools import setup

install_requires = [
    'pyyaml<6',
    'flask<2',
    'gunicorn<21',
    'functions-framework>=3.0.0',
]

setup(
    name='firebase_functions',
    version='0.0.1',
    description='Firebase Functions Python SDK',
    install_requires=install_requires,
    packages=["firebase_functions"],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: Apache Software License',
    ],
)
