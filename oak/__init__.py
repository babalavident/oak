# -*- coding: utf-8 -*-
"""
.. module:: oak
    :platform: Unix
    :synopsys: A static blog generator

.. moduleauthor:: Marcos <marc0s@fsfe.org>

"""

import codecs
import glob
import os
import shutil
import sys

import logging
logger = logging.getLogger("oak")

from jinja2 import Environment, FileSystemLoader

from oak.models.post import Post
from oak.models.tag import Tag
from oak.models.author import Author
from oak.utils import copytree_, Filters
from oak.processors import processor

class Oak(object):
    """The main Oak class

    """

    logger = None
    settings = None
    posts = []
    authors = {}
    tags = {}
    base_url = None # old blog_url

    def __init__(self, settings):
        """Initializes the class

        The logger and the settings module are stored and the Jinja environment
        set up.

        :param logger: The logger object
        :param settings: The settings module to be used along the generation process
        :type settings: module
        """
	self.settings = settings

        if self.settings['url_paths']['base_path']:
            self.base_url = "http://%s/%s" % (self.settings['blog']['domain'].strip("/"), self.settings['url_paths']['base_path'].strip("/"))
        else:
            self.base_url = "http://%s" % (self.settings['blog']['domain'].strip("/"),)

        logger.info("Starting up...")
        # set up the Jinja environment
	loader_path = os.path.sep.join([self.settings['physical_paths']['layouts'], self.settings['blog']['default_layout']])
	logger.debug("Loader path: " + loader_path)
        self.jenv = Environment(loader=FileSystemLoader(loader_path),extensions=['jinja2.ext.i18n'])

        # get the filters
        self.jenv.filters['datetimeformat'] = Filters.datetimeformat
        self.jenv.filters['longdate'] = Filters.longdate
        self.jenv.filters['shortdate'] = Filters.shortdate
        self.jenv.filters['isodate'] = Filters.isodate
        logger.debug("Template environment ready.")

        self.tpl_vars = {
            'blog': {
                'title': self.settings['blog']['title'],
                'url': self.base_url,
                'id': "/".join([self.base_url, "atom.xml"]),
                'last_updated': None, # Will be updated when reading posts.
                'author': self.settings['author']['name'],
                'email': self.settings['author']['email'],
            },
            'license_text': self.settings['blog']['license_text'],
            'links': {
                'site': self.base_url,
                'taglist': self._get_complete_url(self.settings['pages']['taglist']),
                'archive': self._get_complete_url(self.settings['pages']['archive']),
                'authorlist': self._get_complete_url(self.settings['pages']['authorlist']),
                'feed': self._get_complete_url(self.settings['pages']['feed']),
                'css': self._get_complete_url( self.settings['pages']['css']),
            }
        }

    def _get_complete_url(self, path):
        if path.startswith('/'):
            return path
        else:
            return "/".join([self.base_url, path])

    def _get_complete_path(self, path):
        return  os.path.sep.join([self.settings['physical_paths']['output'], path])

    def _author_path(self, authorname=None):
        """Calculates the final path for a author page given a author name

        :param authorname: the name of the author. If None, return just the directory where author files are write to
        :type authorname: string

        :returns: string
        """
        if authorname:
            return os.path.sep.join([self.settings['physical_paths']['output'], self.settings['url_paths']['authors'], "%s.html" % (authorname,)])
        return os.path.sep.join([self.settings['physical_paths']['output'], self.settings['url_paths']['authors']])

    def _author_url(self, authorname):
        """Calculates the URL for a author page given a author name

        :param authorname: the name of the author
        :type authorname: string

        :return: string
        """
        return "/".join([self.settings['url_paths']['authors'], "%s.html" % (authorname,)])

    def _index_path(self):
        """Calculates the path of the index page

        :return: string
        """
        return os.path.sep.join([self.settings['physical_paths']['output'], self.settings['pages']['index']])

    def _index_url(self):
        """Calculates the URL for the index page

        :returns: string
        """
        return "/".join([self.settings['pages']['index']])

    def _tag_index_url(self):
        """Calculates the URL for the tags index page

        :returns: string
        """
        return "/".join([self.settings['pages']['taglist']])

    def _author_index_url(self):
        """Calculates the URL for the authors index page

        :returns: string
        """
        return "/".join([self.settings['pages']['authorlist']])

    def _tag_index_path(self):
        """Calculates the PATH for the tags index page

        :returns: string
        """
        return os.path.sep.join([self.settings['physical_paths']['output'], self.settings['pages']['taglist']])

    def _author_index_path(self):
        """Calculates the PATH for the author index page

        :returns: string
        """
        return os.path.sep.join([self.settings['physical_paths']['output'], self.settings['pages']['authorlist']])

    def _feed_path(self):
        """Calculates the PATH for the atom.xml feed

        :returns: string
        """
        return os.path.sep.join([self.settings['physical_paths']['output'], 'atom.xml'])

    def _archive_path(self):
        """Calculates the PATH for the archive page

        :returns: string
        """
        return os.path.sep.join([self.settings['physical_paths']['output'], self.settings['pages']['archive']])

    def _archive_url(self):
        return "/".join([self.settings['pages']['archive']])
        
    def _write_file(self, filename, content):
        """Writes content in filename.

        :param filename: the output file name
        :type filename: string

        :param content: the content to write
        :type content: string

        """
        logger.debug("Writing to file '%s'" % (filename,))
        if filename.count(os.path.sep): # if it's a path, check for directories
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
        outfile = codecs.open(filename, mode='w', encoding='utf-8')
        outfile.write(content)
        outfile.close()

    def _copy_statics(self):
        """Copies the static files to the output static path.
        """
        static_path = self._get_complete_path(self.settings['physical_paths']['static'])
        logger.debug("Using '%s' as static_path" % (static_path),)
        copytree_(self.settings['physical_paths']['static'], static_path)
        tpl_static = os.path.sep.join([
                                        self.settings['physical_paths']['layouts'],
                                        self.settings['blog']['default_layout'],
                                        self.settings['physical_paths']['static']
                                      ])
        logger.debug("Using '%s' as template static path" % (tpl_static),)

        # What if does not exists?
        if os.path.exists(tpl_static) and os.path.isdir(tpl_static):
            copytree_(tpl_static, static_path)

    def _do_posts(self):
        """Do the posts generation.
        """
        logger.info("Rendering posts...")
        logger.info("Using %s as source of content." % (self.settings['physical_paths']['content'],))

        post_pattern = os.path.sep.join([self.settings['physical_paths']['content'], '*.' + self.settings['posts']['extension']])
        for f in glob.glob(post_pattern):
            logger.info("Processing %s..." % (f,))
            post = Post(f, self.base_url, self.settings, processor.MarkdownProcessor)
            self.posts.append(post)
            # cache the tags of the current post
            for t in post['metadata']['tags']:
                if t not in self.tags.keys():
                    self.tags[t] = Tag(tag=t, settings=self.settings, posts=[post])
                else:
                    self.tags[t]['posts'].append(post)
            # cache the author of the current post
            author = post['metadata']['author']
            if author not in self.authors.keys():
                self.authors[author] = Author(author=author,url=self._author_url(author), posts=[post])
            else:
                self.authors[author]['posts'].append(post)
            
            # make sure we have the final path created
            if not os.path.exists(os.path.dirname(post['output_path'])) or not os.path.isdir(os.path.dirname(post['output_path'])):
                logger.debug("Output directory %s not found, creating" % (os.path.dirname(post['output_path']),))
                os.makedirs(os.path.dirname(post['output_path']))

            self.tpl_vars.update({'post': post})
            logger.debug("tpl_vars: %s" % (self.tpl_vars,))
            output = self.jenv.get_template(self.settings['templates']['post']).render(self.tpl_vars)
            logger.info("Generating output file in %s" % (post['output_path'],))
            self._write_file(post['output_path'], output)
            self.tpl_vars.pop('post') # remove the aded key

    def _do_tag(self, tag):
        """Create the page for the tag 'tag'
        """
        self.tpl_vars.update({'tag': tag})
        output = self.jenv.get_template(self.settings['templates']['tag']).render(self.tpl_vars)
        logger.info("Generating tag page for %s in %s" % (tag['tag'], tag['path']))
        self._write_file(tag['path'], output)
        # remove added keys
        self.tpl_vars.pop('tag') 

    def _do_tags(self):
        """Do the tags index page
        """
        tags_dir = os.path.sep.join([self.settings['physical_paths']['output'], self.settings['url_paths']['tags']]) 
        if not os.path.exists(tags_dir) or not os.path.isdir(tags_dir):
            logger.debug("Tag files directory %s not found, creating" % (tags_dir,))
            os.makedirs(tags_dir)
        self.tpl_vars.update({'tags': self.tags})
        output = self.jenv.get_template(self.settings['templates']['taglist']).render(self.tpl_vars)
        self._write_file(self._tag_index_path(), output)
        self.tpl_vars.pop('tags')
        for t in self.tags.keys():
            self._do_tag(self.tags[t])

    def _do_author(self, author):
        """Create the page for the author 'author'
        """
        self.tpl_vars.update({'author': author})
        output = self.jenv.get_template(self.settings['templates']['author']).render(self.tpl_vars)
        logger.info("Generating author page for %s in %s" % (author['author'], self._author_path(author['author'])))
        self._write_file(self._author_path(author['author']), output)
        # remove added keys
        self.tpl_vars.pop('author') 

    def _do_authors(self):
        """Do the authors index page
        """
        if not os.path.exists(self._author_path()) or not os.path.isdir(self._author_path()):
            logger.debug("Author files directory %s not found, creating" % (self._author_path(),))
            os.makedirs(self._author_path())
        self.tpl_vars.update({'authors': self.authors})
        output = self.jenv.get_template(self.settings['templates']['authorlist']).render(self.tpl_vars)
        self._write_file(self._author_index_path(), output)
        self.tpl_vars.pop('authors')
        for a in self.authors.keys():
            self._do_author(self.authors[a])

    def _do_index(self):
        # ------ POSTS INDEX ------
        # let's sort the posts in chronological order
        self.posts.sort(lambda x, y: cmp(x['metadata']['pub_date'], y['metadata']['pub_date']))
        # Update the blog.last_updated key for self.tpl_vars
        self.tpl_vars['blog']['last_updated'] = self.posts[0]['metadata']['pub_date']
        if self.settings['posts']['pagination']['sort_reverse']:
            self.posts.reverse()
        self.tpl_vars.update({'posts': self.posts[:self.settings['posts']['pagination']['max_posts']]})
        logger.info("Generating index page at %s" % (self._index_path(),))
        output = self.jenv.get_template(self.settings['templates']['index']).render(self.tpl_vars)
        self._write_file(self._index_path(), output)
        self.tpl_vars.pop('posts')

    def _do_archive(self):
        self.tpl_vars.update({'posts': self.posts[:]})
        logger.info("Generating archive page at %s " % (self._archive_path(),))
        output = self.jenv.get_template(self.settings['templates']['archive']).render(self.tpl_vars)
        self._write_file(self._archive_path(), output)
        self.tpl_vars.pop('posts')

    def _do_feed(self):
        """Generates an Atom feed of the blog posts

        """
        self.tpl_vars.update({'posts': self.posts})
        logger.info("Generating atom.xml at %s" % (self._feed_path(),))
        output = self.jenv.get_template(self.settings['templates']['feed']).render(self.tpl_vars)
        self._write_file(self._feed_path(), output)
        self.tpl_vars.pop('posts')
        logger.info("atom.xml file generated.")

    def generate(self):
        """Generates the HTML files to be published.

        :raises: MarkupError, RenderError
        """
        logger.info("Using '%s' as layout path." % (self.settings['blog']['default_layout'],))

        self._do_posts()
        self._do_tags()
        self._do_authors()
        self._copy_statics()
        self._do_index()
        # the feed MUST be done after the index
        if self.settings['blog']['generate_feed']:
            self._do_feed()
        self._do_archive()

