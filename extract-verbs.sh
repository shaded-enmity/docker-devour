#!/bin/bash
# Part of Docker Devour project

docker 2>&1 | sed '1,/^Commands:/d' | grep -oh '^    [a-z]*  ' | sed 's/ //g'
