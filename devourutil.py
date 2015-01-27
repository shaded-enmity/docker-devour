#!/bin/python -tt
#vim: set fileencoding=utf-8 :

def flag_gen(num):
	return [0]+[1<<x for x in range(0, num-1)]
