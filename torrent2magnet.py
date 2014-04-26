#! /usr/bin/python3

import sys, os, hashlib, urllib.parse, collections

def bencode(elem):
    if type(elem) == str:
        elem = str.encode(elem)
    if type(elem) == bytes:
        result = str.encode(str(len(elem)))+b":"+elem
    elif type(elem) == int:
        result = str.encode("i"+str(elem)+"e")
    elif type(elem) == list:
        result = b"l"
        for item in elem:
            result += bencode(item)
        result += b"e"
    elif type(elem) in [dict, collections.OrderedDict]:
        result = b"d"
        for key in elem:
            result += bencode(key)+bencode(elem[key])
        result += b"e"
    return result

def bdecode(bytestr, recursiveCall=False):
    startingChars = dict({
            b"i" : int,
            b":" : str,
            b"l" : list,
            b"d" : dict
            })
    digits = [b"0", b"1", b"2", b"3", b"4", b"5", b"6", b"7", b"8", b"9"]
    started = ended = False
    curtype = None
    numstring = b"" # for str, int
    result = None   # for list, dict
    key = None      # for dict
    while len(bytestr) > 0:
        # reading and popping from the beginning
        char = bytestr[:1]
        if not started:
            bytestr = bytestr[1:]
            if char in digits:
                numstring += char
            elif char in startingChars:
                started = True
                curtype = startingChars[char]
                if curtype == str:
                    size = int(bytes.decode(numstring))
                    # try to decode strings
                    try:
                        result = bytes.decode(bytestr[:size])
                    except UnicodeDecodeError:
                        result = bytestr[:size]
                    bytestr = bytestr[size:]
                    ended = True
                    break

                elif curtype == list:
                    result = []
                elif curtype == dict:
                    result = collections.OrderedDict()
            else:
                raise ValueError("Expected starting char, got ‘"+bytes.decode(char)+"’")
        else: # if started
            if not char == b"e":
                if curtype == int:
                    bytestr = bytestr[1:]
                    numstring += char
                elif curtype == list:
                    item, bytestr = bdecode(bytestr, recursiveCall=True)
                    result.append(item)
                elif curtype == dict:
                    if key == None:
                        key, bytestr = bdecode(bytestr, recursiveCall=True)
                    else:
                        result[key], bytestr = bdecode(bytestr, recursiveCall=True)
                        key = None
            else: # ending: char == b"e"
                bytestr = bytestr[1:]
                if curtype == int:
                    result = int(bytes.decode(numstring))
                ended = True
                break
    if ended:
        if recursiveCall:
            return result, bytestr
        else:
            return result
    else:
        raise ValueError("String ended unexpectedly")

def torrent2magnet(torrentdic, new_trackers=None):
    result = []

    # add hash info
    if "info" not in torrentdic:
        raise ValueError("No info dict in torrent file")
    encodedInfo = bencode(torrentdic["info"])
    sha1 = hashlib.sha1(encodedInfo).hexdigest()
    result.append("xt=urn:btih:"+sha1)

    # add display name
    #if "name" in torrentdic["info"]:
        #quoted = urllib.parse.quote(torrentdic["info"]["name"], safe="")
        #result.append("dn="+quoted)

    # add trackers list
    #trackers = []
    #if "announce-list" in torrentdic:
        #for urllist in torrentdic["announce-list"]:
            #trackers += urllist
    #elif "announce" in torrentdic:
        #trackers.append(torrentdic["announce"])
    #if new_trackers:
        #trackers += new_trackers

    # eliminate duplicates without sorting
    #seen_urls = []
    #for url in trackers:
        #if [url] not in seen_urls:
            #seen_urls.append([url])
            #quoted = urllib.parse.quote(url, safe="")
            #result.append("tr="+quoted)
    #torrentdic["announce-list"] = seen_urls

    # output magnet or torrent file
    #if output == sys.stdout:
    magnet_link = "magnet:?" + "&".join(result)
    return magnet_link
    #else:
        #out = open(output, 'bw')
        #out.write(bencode.bencode(torrentdic))
        #out.close()

def writer(cwd, i):
    with open(cwd, 'a') as g:
        g.write(i + '\n\n')

def main(directory):
    directory = os.path.abspath(directory)
    cwd = os.path.join(os.getcwd(), 'magnet_links')
    for a, b, c in os.walk(directory):
        for i in c:
            file_ext = os.path.splitext(i)[-1]
            if file_ext == '.torrent':
                file_name = os.path.join(a, i)
                byte_stream  = open(file_name, 'br').read()
                try:
                    torrentdic = bdecode(byte_stream)
                    magnet_link = torrent2magnet(torrentdic)
                    tt = '## ' + i + ':\n' + magnet_link
                    writer(cwd, tt)
                except:
                    pass

if __name__ == '__main__':
    argv = sys.argv
    main(argv[1])
