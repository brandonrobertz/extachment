'''
The MIT License (MIT)

Copyright (c) 2014 Patrick Olsen
Updated in 2021 by Brandon Roberts <brandon@bxroberts.org>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Author: Patrick Olsen

Reference: http://www.decalage.info/python/oletools
Reference: https://github.com/mattgwwalker/msg-extractor
'''
from __future__ import print_function
import os, re
import email
import argparse
import olefile
import mimetypes


def printIT(eml_filename, magic, filename):
    print('Email Name: %s\n\tMagic: %s\n\tSaved File as: %s\n' % (eml_filename, magic, filename))


def payload_filename(payload, eml_filename, attachment_n=None):
    filename = payload.get_filename()
    print("Payload filename", filename)
    if filename is None:
        mime = payload.get_content_type()
        print("mime", mime)
        if mime == "text/plain":
            ext = ".txt"
        else:
            ext = mimetypes.guess_extension(mime, strict=False)
        print("ext", ext)
        n = "-%s" % (attachment_n) if attachment_n is not None else ""
        filename = eml_filename + "-attachment" + n + ext
        print("filename",filename)
    return filename


def extractAttachment(msg, eml_filename, output_path):
    print("Payloads", len(msg.get_payload()))
    print("Payload", msg.get_payload())
    if len(msg.get_payload()) > 2:
        if isinstance(msg.get_payload(), str):
            try:
                print("Trying extractOLEFormat")
                extractOLEFormat(eml_filename, output_path)
            except IOError:
                print('Could not process %s. Try manual extraction.' % (eml_filename))
                print('\tHeader of file: %s\n' % (msg.get_payload()[:8]))

        elif isinstance(msg.get_payload(), list):
            print("Processing payload list")
            n = 1
            for payload in msg.get_payload():
                print("Payload", payload)
                filename = payload_filename(payload, eml_filename)
                try:
                    magic = payload.get_payload(decode=True)[:4]
                except TypeError:
                    magic = "None"
                print("Magic", magic)
                # Print the magic deader and the filename for reference.
                printIT(eml_filename, magic, filename)
                # Write the payload out.
                writeFile(filename, payload, output_path)
                n += 1

    elif len(msg.get_payload()) == 2:
        payload = msg.get_payload()[1]
        filename = payload_filename(payload, eml_filename)
        try:
            magic = payload.get_payload(decode=True)[:4]
        except TypeError:
            magic = "None"
        # Print the magic deader and the filename for reference.
        printIT(eml_filename, magic, filename)
        # Write the payload out.
        writeFile(filename, payload, output_path)

    elif len(msg.get_payload()) == 1:
        attachment = msg.get_payload()[0]
        payload = attachment.get_payload()[1]
        filename = payload_filename(payload, eml_filename)
        try:
            magic = payload.get_payload(decode=True)[:4]
        except TypeError:
            magic = "None"
        # Print the magic deader and the filename for reference.
        printIT(eml_filename, magic, filename)
        # Write the payload out.
        writeFile(filename, payload, output_path)

    else:
        print('Could not process %s\t%s' % (eml_filename, len(msg.get_payload())))


def extractOLEFormat(eml_filename, output_path):
    data = '__substg1.0_37010102'
    filename = olefile.OleFileIO(eml_filename)
    msg = olefile.OleFileIO(eml_filename)
    attachmentDirs = []
    for directories in msg.listdir():
        if directories[0].startswith('__attach') and directories[0] not in attachmentDirs:
            attachmentDirs.append(directories[0])

    for dir in attachmentDirs:
        filename = [dir, data]
        if isinstance(filename, list):
            filenames = "/".join(filename)
            filename = msg.openstream(dir + '/' + '__substg1.0_3707001F').read().replace('\000', '')
            payload = msg.openstream(filenames).read()
            magic = payload[:4]
            # Print the magic deader and the filename for reference.
            printIT(eml_filename, magic, filename)
            # Write the payload out.
            writeOLE(filename, payload, output_path)


def writeFile(filename, payload, output_path):
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    try:
        file_location = output_path + filename
        open(os.path.join(file_location), 'wb').write(payload.get_payload(decode=True))
    except (TypeError, IOError) as e:
        print("Error saving %s: %s" % (filename, e))
        pass


def writeOLE(filename, payload, output_path):
    open(os.path.join(output_path + filename), 'wb')


def main():
    parser = argparse.ArgumentParser(description='Attempt to parse the attachment from EML messages.')
    parser.add_argument('-p', '--path', help='Path to EML files.')
    parser.add_argument('-o', '--out', help='Path to write attachments to.')
    args = parser.parse_args()

    if args.path:
        input_path = args.path
    else:
        print("You need to specify a path to your EML files.")
        exit(0)

    if args.out:
        output_path = args.out
    else:
        print("You need to specify a path to write your attachments to.")
        exit(0)

    for root, subdirs, files in os.walk(input_path):
        for file_names in files:
            if not file_names.lower().endswith(".eml"):
                continue
            print("file_names", file_names)
            eml_filename = os.path.join(root, file_names)
            print("eml_filename", eml_filename)
            msg = email.message_from_file(open(eml_filename))
            print("msg", msg)
            extractAttachment(msg, eml_filename, output_path)

if __name__ == "__main__":
    main()
