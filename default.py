# -*- coding: utf-8 -*-
"""
    Crunchyroll
    Copyright (C) 2012 - 2014 Matthew Beacher
    This program is free software; you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
"""

import sys
import xbmc
import xbmcaddon
from resources.lib import abtv2

_plugId = 'plugin.video.animebaka'

# Plugin constants
__plugin__    = "AnimeBaka"
__version__   = "1.0.0"
__XBMCBUILD__ = xbmc.getInfoLabel("System.BuildVersion")
__settings__  = xbmcaddon.Addon(id=_plugId)
__language__  = __settings__.getLocalizedString

xbmc.log("[PLUGIN] '%s: version %s' initialized!" % (__plugin__, __version__))

if __name__ == "__main__":
    abtv2.main()

sys.modules.clear()
