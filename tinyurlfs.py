#!/usr/bin/env python

# TinyURL file uploading and downloading
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

"""
TinyURL file uploading and downloading.

@see: U{http://breakingcode.wordpress.com/}

@type block_size: int
@var  block_size: Size in bytes of each chunk to be uploaded. The data that's
    actually uploaded will be larger due to encoding.

    The larger the chunks the less URLs will have to be created - but if the
    chunk size is too large it may fail. I found a size of 32 Kb to be good
    enough but feel free to tweak it to better suit your needs.

@type verbose: bool
@var  verbose: Global verbose flag. Set to C{True} to print debug messages, or
    C{False} for the default behavior (don't print anything).
    This is a private variable and you shouldn't need to use it.
"""

# Example file (Plaza_Congreso__2_by_QvasiModo.jpg, 217,730 bytes)
# http://qvasimodo.deviantart.com/art/Plaza-Congreso-2-148633734
#
# Uploading
#    $ ./tinyurlfs.py upload Plaza_Congreso__2_by_QvasiModo.jpg Plaza_Congreso__2_by_QvasiModo.txt
#    Created: http://tinyurl.com/yhbj6q6
#
# Downloading
#    $ ./tinyurlfs.py download Plaza_Congreso__2_by_QvasiModo.txt Plaza_Congreso__2_by_QvasiModo\ \(1\).jpg
#    Reading: http://preview.tinyurl.com/yhbj6q6

# Example file (BigBillBroonzy-BabyPleaseDontGo1.mp3, 3,915,875 bytes)
# http://www.publicdomain2ten.com/2009/09/big-bill-broonzy-baby-please-dont-go-mp3/
#    $ ./tinyurlfs.py upload BigBillBroonzy-BabyPleaseDontGo1.mp3 BigBillBroonzy-BabyPleaseDontGo1.txt
#    Created: http://tinyurl.com/y9kqqgk
#    Created: http://tinyurl.com/ybkmjyc
#    Created: http://tinyurl.com/yfx3xt6
#    Created: http://tinyurl.com/yd8d4wf
#    Created: http://tinyurl.com/y9ozqog
#    Created: http://tinyurl.com/yjqj72c
#    Created: http://tinyurl.com/ycclscw
#    Created: http://tinyurl.com/yd2webd
#    Created: http://tinyurl.com/ycmnp4v
#    Created: http://tinyurl.com/yctbjom
#    Created: http://tinyurl.com/y9n4d22
#    Created: http://tinyurl.com/ybsrkfg
#    Created: http://tinyurl.com/y9qoto5
#    Created: http://tinyurl.com/yf2cp7o
#    Created: http://tinyurl.com/yd94r9n
#    $ ./tinyurlfs.py download BigBillBroonzy-BabyPleaseDontGo1.txt BigBillBroonzy-BabyPleaseDontGo1\ \(1\).mp3
#    Reading: http://preview.tinyurl.com/y9kqqgk
#    Reading: http://preview.tinyurl.com/ybkmjyc
#    Reading: http://preview.tinyurl.com/yfx3xt6
#    Reading: http://preview.tinyurl.com/yd8d4wf
#    Reading: http://preview.tinyurl.com/y9ozqog
#    Reading: http://preview.tinyurl.com/yjqj72c
#    Reading: http://preview.tinyurl.com/ycclscw
#    Reading: http://preview.tinyurl.com/yd2webd
#    Reading: http://preview.tinyurl.com/ycmnp4v
#    Reading: http://preview.tinyurl.com/yctbjom
#    Reading: http://preview.tinyurl.com/y9n4d22
#    Reading: http://preview.tinyurl.com/ybsrkfg
#    Reading: http://preview.tinyurl.com/y9qoto5
#    Reading: http://preview.tinyurl.com/yf2cp7o
#    Reading: http://preview.tinyurl.com/yd94r9n
#    $ cmp -l BigBillBroonzy-BabyPleaseDontGo1.mp3 BigBillBroonzy-BabyPleaseDontGo1\ \(1\).mp3
#    $

__all__ = ['upload', 'download']

import re
import time
import urllib2

verbose     = False
timeout     = 10            # 10 seconds timeout for HTTP requests
block_size  = (1024 * 256)  # 256 Kb blocks seemed to work well for me

def upload(original, encoded):
    """Upload a file and write the encoded version.

    The file can be downloaded passing the encoded file to the L{download}
    function.

    @type  original: str
    @param original: Name of the local file to upload.

    @type  encoded: str
    @param encoded: Name of the output file that will contain the information
        needed to download the original file later.

    @raise RuntimeError: An error occured while trying to upload the file.
    @raise urllib2.HTTPError: A network error occured while accessing the URL
        shortener service.
    """
    global verbose
    global block_size
    with open(original, 'rb') as infile:
        with open(encoded, 'w') as outfile:
            pos = 0
#            do_pause = False
            while 1:
#                if do_pause:
#                    if verbose:
#                        print "Waiting 10 seconds before making another request..."
#                    time.sleep(10)
#                else:
#                    do_pause = True
                data = infile.read(block_size)
                if not data:
                    break
                data = data.encode('hex')
                request = ('http://tinyurl.com/api-create.php', 'url=%s' % data, timeout)
                tries = 3
                while 1:
                    try:
                        url = urllib2.urlopen(*request).read()
                        break
                    except IOError, e:
                        tries = tries - 1
                        if tries <= 0:
                            raise
                        if verbose:
                            print "Error: %s" % str(e)
                            print "Waiting 10 seconds before making another request..."
                        time.sleep(10)
                url = url.strip()
                if not url.startswith('http://tinyurl.com/'):
                    raise RuntimeError, "Error creating link for position %d, reason: %r" % (pos, url)
                if verbose:
                    print "Created: %s" % url
                code = url[-7:]
                print >> outfile, code
                pos = pos + block_size

def download(encoded, original):
    """Download a file uploaded with L{upload}.

    @type  encoded: str
    @param encoded: File that contains the information needed to download the
        file. It was generated by the L{upload} function.

    @type  original: str
    @param original: Output file that will contain the downloaded data.

    @raise RuntimeError: An error occured while trying to download the file.
    @raise urllib2.HTTPError: A network error occured while accessing the URL
        shortener service.
    """
    global verbose
    start   = re.compile('<blockquote>')
    end     = re.compile('</blockquote>')
    garbage = re.compile('</?[^>]*>')
    with open(encoded, 'r') as infile:
        with open(original, 'w+b') as outfile:
            for code in infile:
                code = code.strip()
                if not code:
                    continue
                url = 'http://preview.tinyurl.com/%s' % code
                if verbose:
                    print "Reading: %s" % url
                page = urllib2.urlopen(url).read()
                start_m = start.search(page)
                if start_m is None:
                    raise RuntimeError, "Failed to extract data from URL %s" % url
                end_m = end.search(page, start_m.end())
                if end_m is None:
                    raise RuntimeError, "Failed to extract data from URL %s" % url
                page = page[ start_m.end() : end_m.start() ]
                pos  = 0
                while 1:
                    garbage_m = garbage.search(page, pos)
                    if garbage_m is None:
                        break
                    pos  = garbage_m.start()
                    page = page[ : pos ] + page[ garbage_m.end() : ]
                page = page.replace(' ',  '')
                page = page.replace('\t', '')
                page = page.replace('\r', '')
                page = page.replace('\n', '')
                page = page.decode('hex')
                outfile.write(page)

def main(argv):
    """Main function. Uploads and downloads files from the commandline.

    This is a private function and you shouldn't need to use it.

    @type  argv: list of str
    @param argv: Command line arguments.
    """
    global verbose
    verbose = True
    if '--help' in argv or '-h' in argv or len(argv) != 4 or argv[1].lower() not in ('upload', 'download'):
        print "TinyURL file uploading and downloading."
        print "by Mario Vilas (mvilas at gmail dot com)"
        print
        print "%s upload <local file (input)> <encoded file (output)>" % argv[0]
        print "%s download <encoded file (input)> <downloaded file (output)>" % argv[0]
        return
    if argv[1].lower() == 'upload':
        upload(argv[2], argv[3])
    else:
        download(argv[2], argv[3])

# Run the main() function when invoked from the command line.
if __name__ == "__main__":
    from sys import argv
    main(argv)

# XXX TODO
# List of things that could be improved:
#
# * Compression and encription? For now that's up to the user...
#
# * A more efficient encoding could be used. Maybe base64?
#
# * HTTP requests could be made in parallel to speed things up a bit.
#
# * Since the same data will always produce the same short URL we could cache
#   the results of our queries to avoid sending repeated blocks of data. The
#   question is how to do it efficiently. This could also be thought of as a
#   compression scheme - if we can find repeated data in large enough blocks
#   we could reuse the short URLs and resolve each of them only once when
#   downloading.
#
# * Decent command line parsing, plus more options:
#   * Configurable block size, timeout and verbosity.
#   * Resume an upload or a download.
#   * Default value for the output filename.
#
# * Measure the speed of the trasfers.
#
# * Use the GET method and the Location: header for really small block sizes.
#
# * Give a better feedback than just printing URLs, something like a percentage.
