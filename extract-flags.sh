#!/bin/bash
# Part of Docker Devour project

docker $1 --help 2>&1 | grep -wo '  -.*   ' | sed 's/^ *//g'
