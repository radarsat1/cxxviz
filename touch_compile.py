#!/usr/bin/env python3

import sys, os, json, time

wd = '/home/wall/siconos/siconos'
file_list_fn = wd.replace('/','_') + '-file-list.json'

configure_cmd = 'cd "{0}/bld"; cmake .. -DUSER_OPTIONS_FILE="$PWD/myoptions.cmake" >/dev/null 2>&1'.format(wd)

compile_cmd = 'make -C "{0}/bld" >/dev/null 2>&1'.format(wd)

if not os.path.isdir(wd):
    print('Error, {0} is not a directory.'.format(wd))
    sys.exit(1)

def save_results(results):
    with open(file_list_fn, 'w') as f:
        json.dump(results, f, indent=1)

def read_file_list():
    try:
        with open(file_list_fn, 'r') as lst:
            print('=== Recovering file list')
            results = json.load(lst)
    except IOError:
        print('=== Making file list')
        results = {}
        reject = lambda x,y: '.git' in x
        for d in os.walk(wd):
            for f in d[2]:
                if not reject(d[0],f):
                    fn = os.path.join(d[0],f)
                    results[fn] = None
        results['initial_compile_time'] = None
        results['first_recompile_time'] = None
        save_results(results)
    return results

def do_configure():
    print('=== Configuring')
    print(configure_cmd)
    if os.system(configure_cmd) != 0:
        print('Error running configure command.')
        sys.exit(1)

def do_compile():
    print('=== Compiling')
    print(compile_cmd)
    t0 = time.time()
    if os.system(compile_cmd) != 0:
        print('Error running compile command.')
        return None
    t1 = time.time() - t0
    print('Time: {0}'.format(t1))
    return t1

def do_touch(path):
    print('=== Touching "{0}"'.format(path))
    if os.system('touch "{0}"'.format(path)) != 0:
        print('Error running touch command.')
        return False
    return True

if __name__=='__main__':
    results = read_file_list()
    print('Total number of files: {0}'.format(len(results)))

    do_configure()

    if results['initial_compile_time'] is None:
        results['initial_compile_time'] = do_compile()
    if results['initial_compile_time'] is None:
        print('Error on initial compile.')
        sys.exit(1)

    if results['first_recompile_time'] is None:
        results['first_recompile_time'] = do_compile()
    if results['first_recompile_time'] is None:
        print('Error on first recompile.')
        sys.exit(1)
    save_results(results)

    for fn,tm in results.items():
        if tm is None:
            do_touch(fn)
            results[fn] = do_compile()
            save_results(results)
