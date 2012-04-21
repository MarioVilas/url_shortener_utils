#!/usr/bin/env python

# Ito.mx file uploading and downloading
# Copyright (c) 2009, Mario Vilas
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice,this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""Ito.mx file uploading and downloading.

@type nonce_size: int
@var  nonce_size: Size in bytes of the nonce used to mitigate collisions.
    The actual size in each URL is twice as much because it's hex encoded.
    This is a private variable and you shouldn't need to use it.

@type tag_size: int
@var  tag_size: Size in bytes of each chunk of data to be stored in the URL tag.
    The actual size in each URL is twice as much because it's hex encoded.
    This is a private variable and you shouldn't need to use it.

@type pause: float
@var  pause: Time to wait between requests. Use this to avoid being blocked as
    a bot. It's also good netiquette to pause between queries so they don't
    consume too much bandwidth.
    This is a private variable and you shouldn't need to use it.

@type max_tries: int
@var  max_tries: Number of retries when trying to create a shortened URL and
    it already exists.
    This is a private variable and you shouldn't need to use it.

@type verbose: bool
@var  verbose: Global verbose flag. Set to C{True} to print debug messages, or
    C{False} for the default behavior (don't print anything).
    This is a private variable and you shouldn't need to use it.
"""

__all__ = ['upload', 'download']

import zlib
import time
import random
import urllib2
from os import path

nonce_size  = 2             # size in bytes of the random nonce, before encoding
tag_size    = 128           # size in bytes of each data chunk, before encoding
pause       = 0.5           # pause between HTTP requests
max_tries   = 3             # number of retries in case of error
verbose     = False         # set to true to print debug messages

def add_url(url, tag, password):
    """Adds a new shortened URL to the ito.mx database.

    This is a private function and you shouldn't need to use it.

    @type  url: str
    @param url: Target of the shortened URL. It must be a valid URL but not
        necessarily point to an existent resource. The ito.mx service also
        lets you create shortened URLs to other shortened URLs.

    @type  tag: str
    @param tag: Desired URL tag. If the URL was already taken the call fails.

    @type  password: str
    @param password: Password to protect the target of the shortened URL.

    @rtype:  str
    @return: Shortened URL.

    @raise RuntimeError: An error occured while trying to shorten the URL.
    @raise urllib2.HTTPError: A network error occured while accessing the URL
        shortener service.
    """
    global verbose
    url      = urllib2.quote(url)
    tag      = urllib2.quote(tag)
    password = urllib2.quote(password)
    request  = 'pass=%(password)s&tag=%(tag)s&url=%(url)s' % vars()
    response = urllib2.urlopen('http://ito.mx/?module=ShortURL&file=Add&mode=API', request)
    headers  = response.info()
    url      = response.read()
    if headers.get('Content-Type', None) == 'application/x-www-form-urlencoded':
        url = urllib2.unquote(url)
    url = url.strip()
    if not url.startswith('http://ito.mx/'):
        url = url.replace('<h3>', '')
        url = url.replace('</h3>', '')
        raise RuntimeError, "Failed to create new URL, reason: %s" % url
    if verbose:
        print "Created: %s" % url
    return url

def calc_nonce():
    """Returns a randomly generated nonce.

    This is a private function and you shouldn't need to use it.

    @rtype:  str
    @return: Random binary nonce.
        You have to encode it to be able to use it in an URL.
    """
    global nonce_size
    return ''.join([ chr(random.randint(0, 255)) for i in xrange(0, nonce_size) ])

def compress(data):
    """Compress the data using zlib. If the compressed data is larger the
        uncompressed data is returned.

    This is a private function and you shouldn't need to use it.

    @type  data: str
    @param data: Data to compress.

    @rtype:  tuple (str, bool)
    @return: Data, may be compressed or not. The boolean value is C{True} when
        the data is compressed or C{False} otherwise.
    """
    # comment all but the last line to disable compression
    zipped = zlib.compress(data, zlib.Z_BEST_COMPRESSION)
    if len(zipped) < len(data):
        return zipped, True
    return data, False

def decompress(data):
    """Decompress the data using zlib. If the data wasn't compressed just
        return it unchanged.

    This is a private function and you shouldn't need to use it.

    @type  data: str
    @param data: Compressed data.

    @rtype:  str
    @return: Decompressed data.
    """
    return zlib.decompress(data)

def upload(filename, password):
    """Upload a file and write the encoded version.

    The file can be downloaded passing the encoded file to the L{download}
    function.

    @type  filename: str
    @param filename: Name of the local file to upload.

    @type  password: str
    @param password: Password to protect the uploaded file.

    @raise RuntimeError: An error occured while trying to upload the file.
    @raise urllib2.HTTPError: A network error occured while accessing the URL
        shortener service.
    """
    global tag_size
    global pause
    global max_tries
    global verbose

    data = open(filename, 'rb').read()
    data, zipped = compress(data)
    data = data.encode('hex')
    data = [ data[ i : i + tag_size ] for i in xrange(0, len(data), tag_size) ]
    data.reverse()

    hex_filename = path.split(filename)[1].encode('hex')
    first_nonce  = calc_nonce().encode('hex')
    if zipped:
        tag_filename = 'z%s-%s' % (first_nonce, hex_filename)
    else:
        tag_filename = 'p%s-%s' % (first_nonce, hex_filename)
    url = 'http://ito.mx/%s' % tag_filename
    if verbose:
        print "Uploading: %s" % url
    try:
        temp = urllib2.urlopen(url).read()
        if not '<H3 class="error">' in temp:
            raise RuntimeError, "URL already exists: %s" % url
        del temp
    except urllib2.HTTPError:
        pass

    for tag in data:
        tries = 0
        while 1:
            try:
                time.sleep(pause)
                nonce = calc_nonce().encode('hex')
                url   = add_url(url, '%s-%s' % (nonce, tag), password)
                break
            except urllib2.HTTPError, e:
                if verbose:
                    print "Error: %s" % str(e)
                tries += 1
                if tries > max_tries:
                    raise
    url = add_url(url, tag_filename, password)
    return url

def download(url, password):
    """Download a file uploaded with L{upload}.

    @type  url: str
    @param url: URL returned by L{upload}.
        Any other URL in the chain will also work.

    @type  password: str
    @param password: Password used to protect the file.

    @rtype:  tuple(str, str)
    @return: The name and contents of the downloaded file.

    @raise RuntimeError: An error occured while trying to download the file.
    @raise urllib2.HTTPError: A network error occured while accessing the URL
        shortener service.
    """
    global pause
    global max_tries
    global verbose

    ordered = list()
    visited = set()
    first   = None
    zipped  = None
    while 1:
        if not url.startswith('http://ito.mx/'):
            raise RuntimeError, "Broken chain! Bad URL: %s" % url
        url_path = url[14:]
        p = url_path.find('-')
        if p < 1:
            raise RuntimeError, "Broken chain! Bad tag: %s" % url
        nonce = url_path[ : p ]
        tag   = url_path[ p + 1 : ]
        try:
            tag = tag.decode('hex')
        except Exception:
            raise RuntimeError, "Broken chain! Bad tag: %s" % url
        if tag in visited:
            break
        is_p = nonce.startswith('p')
        is_z = nonce.startswith('z')
        if is_p or is_z:
            if first is not None:
                raise RuntimeError, "Broken chain! Duplicate headers found"
            first  = len(ordered)
            zipped = is_z
        visited.add(tag)
        ordered.append(tag)
        if verbose:
            print "Reading: %s" % url
        response = urllib2.urlopen(url, 'pass=%s' % password)
        url = response.geturl()
    if first is None:
        raise RuntimeError, "Broken chain! No header found"

    if verbose:
        print "Merging %d parts" % (len(ordered) - 1)
    filename = ordered[first]
    if first == 0:
        ordered.pop(0)
        merged = ordered
    else:
        merged = ordered[ first + 1 : len(ordered) ]
        merged.extend( ordered[ 0 : first ] )
        del ordered
    merged = ''.join(merged)
    if zipped:
        merged = decompress(merged)
    return filename, merged

def main(argv):
    """Main function. Uploads and downloads files from the commandline.

    This is a private function and you shouldn't need to use it.

    @type  argv: list of str
    @param argv: Command line arguments.
    """
    global verbose
    if '--help' in argv or '-h' in argv or len(argv) != 4 or argv[1].lower() not in ('upload', 'download'):
        print "Ito.mx file uploading and downloading"
        print "by Mario Vilas (mvilas at gmail dot com)"
        print
        print "%s upload <filename> <password>" % argv[0]
        print "%s download <url> <password>" % argv[0]
        return
    _, command, target, password = argv
    command = command.lower()
    if command == 'download':
        filename, data = download(target, password)
        if verbose:
            print "Writing: %s" % filename
        open(filename, 'w+b').write(data)
    else:
        url = upload(target, password)
        if not verbose:
            print url

# Run the main() function when invoked from the command line.
if __name__ == "__main__":
    from sys import argv
    verbose = True
    main(argv)

# XXX TODO
# List of things that could be improved:
#
# * Encription? For now that's up to the user...
#
# * A more efficient encoding could be used. Maybe base64?
#
# * HTTP requests could be made in parallel to speed things up a bit.
#
# * The block size could be calculated dynamically, to make shorter URLs for
#   smaller files and longer URLs for bigger files.
#
# * Decent command line parsing, plus more options:
#   * Configurable block size.
#   * Configurable pause between requests.
#   * Resume an upload or a download.
#
# * Measure the speed of the trasfers.
