#! /usr/bin/env python

import json
import sys

t = json.load(open(sys.argv[1]))
json.dump(t, open(sys.argv[1], "w"), indent=4, sort_keys=True)
