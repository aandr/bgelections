# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from os import listdir
from collections import OrderedDict
from lxml import etree
import codecs

def scan():
    out = codecs.open('results.csv', 'w', 'cp1251')
    headers_out = False

    all_protos = []

    for area in range(1,33):
        area = str(area)
        if len(area) == 1:
            area = '0%s' % area

        files = listdir('results.cik.bg/pi2014/protokoli/%s' % area)
        for filename in files:
            if '.html' in filename and filename != 'list.html':
                res = parse_protocol(area + filename.split('.')[0])
                all_protos.append(res)

                if not headers_out:
                    out.write(",".join(res.keys()) + "\n")
                    headers_out = True

                out.write(",".join(res.values()) + "\n")

    out.close()

    return all_protos


def protocol_id_to_filepath(protocol_id):
    protocol_id = protocol_id
    return 'results.cik.bg/pi2014/protokoli/%s/%s.html' % (protocol_id[0:2], protocol_id[2:])

def parse_protocol(protocol_id):
    parser = ProtocolParser(protocol_id)

    filepath = protocol_id_to_filepath(protocol_id)
    fileobj = codecs.open(filepath, 'r', 'utf-8')
    contents = fileobj.read()
    fileobj.close()
    xmlp = etree.HTMLParser(target=parser)
    result = etree.XML(contents, xmlp)

    return parser.results

def coint(val):
    if not val:
        return 0
    val = val.replace(' ', '').replace('.', '')
    return val

class ProtocolParser(object):
    def __init__(self, protocol_id):
        self.protocol_id = str(protocol_id)
        self.cik_section = self.protocol_id[0:2]

        self.mode = 'head'
        self.section = None
        self.extra_section = None
        self.td_pos = -1
        self.line = None
        self.party = -1
        
        self.skip_until = None

        self.results = OrderedDict()
        self.results['area'] = self.protocol_id[0:2]
        self.results['protocol'] = self.protocol_id[2:]

    def start(self, tag, attrib):
        if tag == 'h4':
            self.mode = 'newsection'
            self.section = None
            return

        if self.mode == 'skip':
            return

        if self.mode == 'wait_for_tbody':
            if tag == 'tbody':
                self.mode = 'data'
            else:
                return

        if self.mode == 'data':
            if tag == 'tr':
                self.td_pos = 0

    def end(self, tag):
        if self.skip_until and self.skip_until == tag:
            self.skip_until = None

        if tag == 'tbody':
            self.mode = None

        if tag == 'td':
            self.td_pos += 1

    def data(self, data):
        data = data.strip()

        if self.mode == 'head':
            if data.startswith('населено място '):
                if not 'town' in self.results:
                    self.results['town'] = data[15:]
            elif data.startswith('община '):
                if not 'disctrict' in self.results:
                    self.results['district'] = data[7:]
            elif data.startswith('Държава'):
                parts = data.split(',')
                self.results['town'] = parts[1][6:]
                self.results['district'] = parts[0][7:]

        if self.mode == 'newsection':
            if data.startswith('ДАННИ ОТ ИЗБИРАТЕЛНИТЕ СПИСЪЦИ'):
                self.section = 'lists'
            elif data.startswith('ДАННИ ИЗВЪН ИЗБИРАТЕЛНИТЕ СПИСЪЦИ'):
                self.section = 'extra'
            elif data.startswith('СЛЕД КАТО ОТВОРИ ИЗБИРАТЕЛНАТА КУТИЯ,'):
                self.section = 'inbox'
            elif data.startswith('9. РАЗПРЕДЕЛЕНИЕ'): 
                self.section = 'results'

            if self.section:
                self.mode = 'wait_for_tbody'

        if self.mode == 'data':
            if self.section != 'results':
                if self.td_pos == 0:
                    if data.startswith('1.'):
                        self.line = 'num voters 1.'
                    elif data.startswith('2.'):
                        self.line = 'extras 2.'
                    elif data.startswith('3.'):
                        self.line = 'votes 3.'
                    elif data.startswith('6.'):
                        self.line = 'ballots in box 6.'
                    elif data.startswith('7'):
                        self.line = 'invalid ballots 7.'
                    elif data.startswith('8'):
                        self.line = 'good ballots 8.'
                    else:
                        self.line = None
                elif self.td_pos == 1:
                    if self.line:
                        self.results[self.line] = coint(data)
            elif self.section == 'results':
                if self.td_pos == 0:
                    self.party = data.strip('.') if data else -1
                elif self.td_pos == 2:
                    if self.party > 0:
                        self.results['party ' + self.party] = coint(data)

    def comment(self, text):
        pass
    def close(self):
        pass

if __name__ == '__main__':
    scan()
        
