from setuptools import setup, find_packages, Extension
import re
import os
import subprocess



setup(name = 'nysol_view',
			packages=['nysol','nysol/view'],
			version = '0.0.1',
			description = 'This is nysol tools view',
			long_description="""\
NYSOL (read as nee-sol) is a generic name of software tools and project activities designed for supporting big data analysis.

NYSOL runs in UNIX environment (Linux and Mac OS X, not Windows).
""",
			author='nysol',
			author_email='info@nysol.jp',
			license='AGPL3',
			url='http://www.nysol.jp/',
      classifiers=[ 
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: C',
        'Programming Language :: C++',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
        ],
			install_requires=[
      	  "nysol"
	    ],
			scripts=['scripts/mbar.py','scripts/mpie.py','scripts/mnetpie.py','scripts/mdtree.py','scripts/msankey.py',
				'scripts/mautocolor.py','scripts/mnest2tree.py','scripts/mgv.py'
			]
			)
       
