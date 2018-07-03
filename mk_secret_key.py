#!/usr/bin/python
# -*- coding: utf-8 -*-
import random 
import string

print "".join([random.SystemRandom().choice(string.digits + string.letters) for i in range(100)])
