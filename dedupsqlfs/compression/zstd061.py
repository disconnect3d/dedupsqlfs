# -*- coding: utf8 -*-

__author__ = 'sergey'

"""
Class for Zstd compression helper
New version 0.6.1
"""

from dedupsqlfs.compression import BaseCompression

class Zstd061Compression(BaseCompression):

    _method_name = "zstd061"

    _minimal_size = 25

    _has_comp_level_options = True

    _deprecated = True

    def getFastCompressionOptions(self):
        return ( 1, )

    def getNormCompressionOptions(self):
        return ( 7, )

    def getBestCompressionOptions(self):
        return ( 9, )

    def getDefaultCompressionOptions(self):
        return ( 4, )

    def getCustomCompressionOptions(self):
        try:
            level = int(self._custom_comp_level)
            if level < 1:
                level = 1
            elif level > 20:
                level = 20
            opts = (level, )
        except:
            opts = False
            pass
        return opts

    def isDataMayBeCompressed(self, data, data_len):
        """
        Disallow compression
        It's deprecated version of ZSTD

        @param data:
        @return:
        """
        return False

    pass
