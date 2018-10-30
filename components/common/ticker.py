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
from datetime import datetime


class Ticker():

    def __init__(self, lock=None):
        self.lock = lock
        self.start_time = None

    def tick(self, message):
        self.start_time = datetime.now()

        if self.lock is not None:
            self.lock.acquire()

        print message + " Now: " + str(self.start_time)
        sys.stdout.flush()

        if self.lock is not None:
            self.lock.release()

    def tock(self, message):
        if self.lock is not None:
            self.lock.acquire()

        print message + " Time elapsed: " + str(datetime.now() - self.start_time)
        sys.stdout.flush()

        if self.lock is not None:
            self.lock.release()


