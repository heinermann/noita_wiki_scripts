# This is an automatically generated file. You can find more
# configuration parameters in 'config.py' file or refer
# https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.config.html
from typing import Optional, Union

from pywikibot.backports import Dict, List, Tuple

# The family of sites to be working on.
# Pywikibot will import families/xxx_family.py so if you want to change
# this variable, you have to ensure that such a file exists. You may use
# generate_family_file to create one.
family = 'noita'

# The site code (language) of the site to be working on.
mylang = 'en'

# The dictionary usernames should contain a username for each site where you
# have a bot account. If you have a unique username for all sites of a
# family , you can use '*'
usernames['noita']['en'] = 'Heinermann'
usernames['noita']['zh'] = 'Heinermann'
usernames['noita']['ja'] = 'Heinermann'
usernames['noita']['tr'] = 'Heinermann'

# The list of BotPasswords is saved in another file. Import it if needed.
# See https://www.mediawiki.org/wiki/Manual:Pywikibot/BotPasswords to know how
# use them.
password_file = None

# ############# INTERWIKI SETTINGS ##############

# Should interwiki.py report warnings for missing links between foreign
# languages?
interwiki_backlink = True

# Should interwiki.py display every new link it discovers?
interwiki_shownew = True

# Should interwiki.py output a graph PNG file on conflicts?
# You need pydot for this:
# https://pypi.org/project/pydot/
interwiki_graph = False

# Specifies that the robot should process that amount of subjects at a time,
# only starting to load new pages in the original language when the total
# falls below that number. Default is to process (at least) 100 subjects at
# once.
interwiki_min_subjects = 100

# If interwiki graphs are enabled, which format(s) should be used?
# Supported formats include png, jpg, ps, and svg. See:
# https://graphviz.org/docs/outputs/
# If you want to also dump the dot files, you can use this in your
# user config file:
# interwiki_graph_formats = ['dot', 'png']
# If you need a PNG image with an HTML image map, use this:
# interwiki_graph_formats = ['png', 'cmap']
# If you only need SVG images, use:
# interwiki_graph_formats = ['svg']
interwiki_graph_formats = ['png']

# You can post the contents of your autonomous_problems.dat to the wiki,
# e.g. to https://de.wikipedia.org/wiki/Wikipedia:Interwiki-Konflikte .
# This allows others to assist you in resolving interwiki problems.
# To help these people, you can upload the interwiki graphs to your
# webspace somewhere. Set the base URL here, e.g.:
# 'https://www.example.org/~yourname/interwiki-graphs/'
interwiki_graph_url = None

# Save file with local articles without interwikis.
without_interwiki = False

