# -*- coding: utf-8 -*-

import os
import yaml
import codecs

from oak.utils import Atom
import oak.processors as procs

HEADER_MARK = '---'

class PostError(Exception):
    """Custom exception for invalid posts."""
    def __init__(self, msg):
        self.msg = msg


class Post(dict):
    """
    A class to hold the contents of a post file.
    A post file is a text file which must contain a YAML header
    defining its metadata, and it must be the first content
    of the file, for example:

    ---
      title: 'post title'
      author: 'post author name'
      pub_date: '2010-05-02 17:00:00'
      tags: ['tag1','tag2',...]
    ---
    
    Post title
    ==========

    This is a sample post.

    Other dashes --- may appear here, obviously.


    As seen in the example, three dashes (---) determines the
    header start and end.

    """
    def __init__(self, f, url, settings, processor=None):
        """The Post class __init__

        :param f: the path to the post file
        :param settings: the blog settings
        :param processor: the processor to render post's contents
        :processor type: class

        :raises: PostError
        """
        try:
            _f = codecs.open(f, mode='r', encoding='utf-8')
        except:
            raise PostError('Unable to open file. Hint: isn\'t it UTF-8 encoded?')
        
        metadata = settings['posts']['default_info']

        # Set metadata to the app defaults
        self['metadata'] = metadata.copy()
        self.f = _f.read()
        if not self.f.startswith(HEADER_MARK):
            raise PostError('Post file invalid, no header found.')
        _, metadata, self['raw'] = self.f.split(HEADER_MARK, 2)
        # update the metadata with the header's contents
        self['metadata'].update(yaml.load(metadata))
        # TODO auto determine processor based on metadata['markup']
        if processor:
            p = processor()
            self = p.process(self)

        # Partial refactoring
        filename = os.path.basename(f)
        name, extension = os.path.splitext(filename)

        # TODO add sanity check on source filename (count of - ...)
        self['output_path'] = self._post_path(name, settings['physical_paths']['output']) 
        self['url'] = "%s%s" % (url, self._post_url(name))
        self['id'] = Atom.gen_id(self)

    def _post_url(self, name):
        """Calculates the URL of a post given a name

        :param name: the name of the output (generated) file
        :type name: string

        :return: string
        """
        year, month = name.split('-')[:2]
        newfilename = "%s.html" % name
        return "/".join(['', year, month, newfilename])

    def _post_path(self, name, output_path):
        """Calculates the final path for a post given a name
        
        :param name: the name of the input file
        :type name: string

        :returns: string
        """
        year, month = name.split('-')[:2]
        newfilename = "%s.html" % name
        return os.path.sep.join([output_path, year, month, newfilename])

    @staticmethod
    def _write_file(filename, content):
        """Writes content in filename.

        :param filename: the output file name
        :type filename: string

        :param content: the content to write
        :type content: string

        """
        if filename.count(os.path.sep): # if it's a path, check for directories
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
        outfile = codecs.open(filename, mode='w', encoding='utf-8')
        outfile.write(content)
        outfile.close()

    @classmethod
    def pick_up_acorns(cls, acorn_dir, acorn_extension, base_url, settings, post_template, tpl_vars):
        import glob
        import logging
        logger = logging.getLogger('oak')

        from oak.processors import processor
        from oak.models.tag import Tag
        from oak.models.author import Author

        post_list = []
        tags = {}
        authors = {}
        acorn_pattern = os.path.sep.join([acorn_dir, '*.' + acorn_extension])
        for acorn in glob.glob(acorn_pattern):

            logger.info("Processing %s..." % (acorn,))
            post = cls(acorn, base_url, settings, processor.MarkdownProcessor)
            post_list.append(post)

            # cache the tags of the current post
            for tag in post['metadata']['tags']:
                if tag not in tags.keys():
                    tags[tag] = Tag(tag=tag, settings=settings, posts=[post])
                else:
                    tags[tag]['posts'].append(post)

            # cache the author of the current post
            author = post['metadata']['author']
            if author not in authors.keys():
                authors[author] = Author(author=author,
                                         url="/".join([settings['url_paths']['authors'], "%s.html" % (author,)]),
                                         posts=[post])
            else:
                authors[author]['posts'].append(post)
            
            # make sure we have the final path created
            if not os.path.exists(os.path.dirname(post['output_path'])) or not os.path.isdir(os.path.dirname(post['output_path'])):
                logger.debug("Output directory %s not found, creating" % (os.path.dirname(post['output_path']),))
                os.makedirs(os.path.dirname(post['output_path']))

            tpl_vars.update({'post': post})
            logger.debug("tpl_vars: %s" % (tpl_vars,))
            output = post_template.render(tpl_vars)
            logger.info("Generating output file in %s" % (post['output_path'],))
            cls._write_file(post['output_path'], output)
            tpl_vars.pop('post') # remove the aded key

        return post_list, tags, authors