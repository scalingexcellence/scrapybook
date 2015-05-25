#!/usr/bin/env python

import subprocess
import re
import string
import sys

def pip_get_deps(module):
    cmd = ['pip', 'show', module]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    out, err = p.communicate()

    deps = set()


    for line in out.split('\n'):
        result = re.match(r"Requires: (.*)", line)
        if result and result.group(1):
            deps |= set(map(string.lower, re.split(', ', result.group(1))))

    return deps

def find_dependencies(seed, installed, dont_regress=[]):
    installed_set = set(map(string.lower, installed))
    done_set = set(map(string.lower, installed))
    dont_regress_set = set(map(string.lower, dont_regress))
    todo_set = set(map(string.lower, seed))

    while len(todo_set):
        module = todo_set.pop()
    
        dependencies = pip_get_deps(module)
    
        done_set.add(module)
    
        new_ones = dependencies - done_set - todo_set
    
        done_set |= new_ones & dont_regress_set
    
        new_ones -= dont_regress_set
    
        todo_set |= new_ones
    
        print "New dependencies for module", module, ": ", new_ones, "(original ", dependencies, ")"

    return list(done_set - installed_set)

def pip_download(modules):
    if not modules:
        return
    
    cmd = ['pip', 'install', '--no-deps', '--no-use-wheel','--download', '.'] + modules
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    out, err = p.communicate()
    
    module = []
    zipfile = []
    for line in out.split('\n'):
        result = re.match(r"Downloading/unpacking (.*)", line)
        if result:
            module.append(result.group(1))
        result = re.match(r".*File was already downloaded (.*)", line)
        if result:
            zipfile.append(result.group(1))
        result = re.match(r".*Saved (.*)", line)
        if result:
            zipfile.append(result.group(1))

    return dict(zip(module, zipfile))

def install(module, filen):
    subprocess.call(["rm", "-rf", module])
    subprocess.call(["mkdir", module])
    subprocess.call(["tar", "-xzf", filen, "-C", module, "--strip-components", "1"])
    with open(module + '/__init__.py', 'w+') as f:
        f.write("__all__ = ['" + module + "']\n")
    subprocess.call(["rm", "-f", filen])

modules = find_dependencies(['txredisapi', 'treq'], ['Twisted', 'pyOpenSSL'], ['service-identity'])

files = pip_download(modules)

for module in modules:
    if module in files:
        filen = files[module]
        print "installing module: ", module, " from file: ", filen
        
        install(module, filen)
