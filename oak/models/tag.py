# -*- coding: utf-8 -*-

import os

class Tag(dict):
    def __init__(self, tag, settings, posts=[]):
        self['tag'] = tag
        self['url'] = self._tag_url(settings['url_paths']['tags'], tag)
        self['posts'] = posts
        self['path'] = self._tag_path(settings['physical_paths']['output'], settings['url_paths']['tags'], tag) 

    def _tag_path(self, output_path, tags_prefix, tagname=None):
        """Calculates the final path for a tag page given a tag name

        :param tagname: the name of the tag. If None, return just the directory where tag files are write to
        :type tagname: string

        :returns: string
        """
        if tagname:
            return os.path.sep.join([output_path, tags_prefix, "%s.html" % (tagname,)])
        return os.path.sep.join([output_path, tags_prefix])
    
    def _tag_url(self, tags_prefix, tagname):
        """Calculates the URL for a tag page given a tag name

        :param tagname: the name of the tag
        :type tagname: string

        :return: string
        """
        return "/".join([tags_prefix, "%s.html" % (tagname,)])


