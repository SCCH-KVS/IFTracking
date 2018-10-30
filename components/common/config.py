#
# Copyright (C) Software Competence Center Hagenberg GmbH (SCCH)
# All rights reserved.
#
# This document contains proprietary information belonging to SCCH.
# Passing on and copying of this document, use and communication of its
# contents is not permitted without prior written authorization.
#
# Created by: Dmytro Kotsur
#

import sys
import configparser


class SectionConfig(object):

    def __init__(self, config, section_name):
        self.__config = config
        self.__section_name = section_name

    def __str__(self):
        return "Section_Config"

    def __getitem__(self, key):
        if len(key) > 2 and key[-2] == '_':
            dtype = key[-1]
            if dtype == 'i':
                return self.__config.getint(self.__section_name, key[:-2])
            if dtype == 'f' or dtype == 'd':
                return self.__config.getfloat(self.__section_name, key[:-2])
            if dtype == 'b':
                return self.__config.getboolean(self.__section_name, key[:-2])
        return self.__config.get(self.__section_name, key)


class Config(object):

    def __init__(self, filename):
        self.__config = configparser.ConfigParser()
        self.__config.read(filename)
        self.__sections = {section: SectionConfig(self.__config, section) for section in self.__config.sections()}

    def __getitem__(self, key):
        return self.__sections[key]

    def get(self, group, option, default=None):
        try:
            return self.__sections[group][option]
        except:
            return default

    def get_sections(self):
        return self.__sections.keys()

def print_config(filename):
    with open(filename) as f_in:
        lines = filter(lambda l: not l.startswith('#'), f_in.readlines())
        for line in lines:
            print '  |', line.strip()
    print '\n'
    sys.stdout.flush()
