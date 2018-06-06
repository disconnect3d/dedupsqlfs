# -*- coding: utf8 -*-
"""
@todo: Update argument parser options
"""


# Imports. {{{1

import sys

# Try to load the required modules from Python's standard library.
try:
    import os
    import traceback
    import argparse
    from time import time
    import hashlib
except ImportError as e:
    msg = "Error: Failed to load one of the required Python modules! (%s)\n"
    sys.stderr.write(msg % str(e))
    sys.exit(1)

from dedupsqlfs.lib import constants
from dedupsqlfs.log import logging
import dedupsqlfs


def fuse_mount(options, compression_methods=None):
    from dedupsqlfs.fuse.dedupfs import DedupFS
    from dedupsqlfs.fuse.operations import DedupOperations

    ops = None
    ret = -1
    try:
        ops = DedupOperations()
        _fuse = DedupFS(
            ops, options.mountpoint,
            options,
            use_ino=True, default_permissions=True, fsname="dedupsqlfs")

        _fuse.saveCompressionMethods(compression_methods)

        for modname in compression_methods:
            _fuse.appendCompression(modname)

        _fuse.operations.init()
        _fuse.operations.destroy()

        ret = 0
    except Exception:
        import traceback
        print(traceback.format_exc())
    if ops:
        ops.getManager().close()

    return ret

def main(): # {{{1
    """
    This function enables using dedupsqlfs.py as a shell script that creates FUSE
    mount points. Execute "dedupsqlfs -h" for a list of valid command line options.
    """

    logger = logging.getLogger("dedupsqlfs.main")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stderr))

    parser = argparse.ArgumentParser(
        prog="%s/%s fsck/%s" % (dedupsqlfs.__name__, dedupsqlfs.__version__, dedupsqlfs.__fsversion__),
        conflict_handler="resolve")

    # Register some custom command line options with the option parser.

    parser.add_argument('-h', '--help', action='help', help="show this help message followed by the command line options defined by the Python FUSE binding and exit")
    parser.add_argument('-v', '--verbose', action='count', dest='verbosity', default=0, help="increase verbosity: 0 - error, 1 - warning, 2 - info, 3 - debug, 4 - verbose")
    parser.add_argument('-y', '--yes', dest='questions_yes', action='store_true',
                        help="Assume an answer of `yes' to all questions; allows fsck to be used non-interactively. This option may not be specified at the same time as the -p or -y options.")
    parser.add_argument('-n', '--no', dest='questions_no', action='store_true',
                        help="Open the filesystem read-only, and assume an answer of `no' to all questions. Allows fsck to be used non-interactively. This option may not be specified at the same time as the -p  or -y options.")
    parser.add_argument('-p', '--autorepair', dest='auto_repair', action='store_true',
                        help="Automatically repair ('preen') the file system. This option will cause e2fsck to automatically fix any filesystem problems that can be safely fixed without human intervention. If fsck discovers a problem which may require the system administrator to take additional corrective action, e2fsck will print a description of the problem and then exit with the value 4 logically or'ed into the exit code. (See the EXIT CODE section.) This option is normally used by the system's boot scripts. It may not be specified at the same time as the -n or -y options.")

    parser.add_argument('--log-file', dest='log_file', help="specify log file location")
    parser.add_argument('--log-file-only', dest='log_file_only', action='store_true',
                        help="Don't send log messages to stderr.")

    parser.add_argument('--data', dest='data', metavar='DIRECTORY', default="~/data", help="Specify the base location for the files in which metadata and blocks data is stored. Defaults to ~/data")
    parser.add_argument('--name', dest='name', metavar='DATABASE', default="dedupsqlfs", help="Specify the name for the database directory in which metadata and blocks data is stored. Defaults to dedupsqlfs")
    parser.add_argument('--temp', dest='temp', metavar='DIRECTORY', help="Specify the location for the files in which temporary data is stored. By default honour TMPDIR environment variable value.")

    parser.add_argument('--mount-subvolume', dest='subvolume', metavar='NAME', help="Use subvolume as root fs.")

    parser.add_argument('--memory-limit', dest='memory_limit', action='store_true', help="Use some lower values for less memory consumption.")

    parser.add_argument('--cpu-limit', dest='cpu_limit', metavar='NUMBER', default=0, type=int, help="Specify the maximum CPU count to use in multiprocess compression. Defaults to 0 (auto).")


    parser.add_argument('--no-cache', dest='use_cache', action='store_false', help="Don't use cache in memory and delayed write to storage files (@todo).")
    parser.add_argument('--cache-meta-timeout', dest='cache_meta_timeout', metavar='NUMBER', type=int, default=20, help="Delay flush expired metadata for NUMBER of seconds. Defaults to 20 seconds.")
    parser.add_argument('--cache-block-write-timeout', dest='cache_block_write_timeout', metavar='NUMBER', type=int, default=10, help="Expire writed data and flush from memory after NUMBER of seconds. Defaults to 10 seconds.")
    parser.add_argument('--cache-block-write-size', dest='cache_block_write_size', metavar='BYTES', type=int,
                        default=1024*1024*1024,
                        help="Write cache for blocks: potential size in BYTES. Set to -1 for infinite. Defaults to 1024 MB.")
    parser.add_argument('--cache-block-read-timeout', dest='cache_block_read_timeout', metavar='NUMBER', type=int, default=10, help="Expire readed data and flush from memory after NUMBER of seconds. Defaults to 10 seconds.")
    parser.add_argument('--cache-block-read-size', dest='cache_block_read_size', metavar='BYTES', type=int,
                        default=1024*1024*1024,
                        help="Readed cache for blocks: potential size in BYTES. Set to -1 for infinite. Defaults to 1024 MB.")
    parser.add_argument('--flush-interval', dest='flush_interval', metavar="N", type=int, default=5, help="Call expired cache callector every Nth seconds on FUSE operations. Defaults to 5.")

    parser.add_argument('--no-transactions', dest='use_transactions', action='store_false', help="Don't use transactions when making multiple related changes, this might make the file system faster or slower (?).")
    parser.add_argument('--nosync', dest='synchronous', action='store_false', help="Disable SQLite's normal synchronous behavior which guarantees that data is written to disk immediately, because it slows down the file system too much (this means you might lose data when the mount point isn't cleanly unmounted).")
    parser.add_argument('--nogc-on-umount', dest='gc_umount_enabled', action='store_false', help="Disable garbage collection on umount operation (only do this when you've got disk space to waste or you know that nothing will be be deleted from the file system, which means little to no garbage will be produced).")
    parser.add_argument('--gc', dest='gc_enabled', action='store_true', help="Enable the periodic garbage collection because it degrades performance (only do this when you've got disk space to waste or you know that nothing will be be deleted from the file system, which means little to no garbage will be produced).")
    parser.add_argument('--gc-vacuum', dest='gc_vacuum_enabled', action='store_true', help="Enable data vacuum after the periodic garbage collection.")
    parser.add_argument('--gc-fast', dest='gc_fast_enabled', action='store_true', help="Enable faster periodic garbage collection. Don't collect hash and block garbage.")
    parser.add_argument('--gc-interval', dest='gc_interval', metavar="N", type=int, default=60, help="Call garbage callector after Nth seconds on FUSE operations, if GC enabled. Defaults to 60.")

    # Dynamically check for supported compression methods.
    compression_methods = [constants.COMPRESSION_TYPE_NONE]
    compression_methods_cmd = [constants.COMPRESSION_TYPE_NONE]
    for modname in constants.COMPRESSION_SUPPORTED:
        try:
            module = __import__(modname)
            if hasattr(module, 'compress') and hasattr(module, 'decompress'):
                compression_methods.append(modname)
                if modname not in constants.COMPRESSION_READONLY:
                    compression_methods_cmd.append(modname)
        except ImportError:
            pass
    if len(compression_methods) > 1:
        compression_methods_cmd.append(constants.COMPRESSION_TYPE_BEST)
        compression_methods_cmd.append(constants.COMPRESSION_TYPE_CUSTOM)

    msg = "Enable compression of data blocks using one of the supported compression methods: one of %s"
    msg %= ', '.join('%r' % mth for mth in compression_methods_cmd)
    msg += ". Defaults to %r." % constants.COMPRESSION_TYPE_NONE
    msg += " You can use <method>:<level> syntax, <level> can be integer or value from --compression-level."
    if len(compression_methods_cmd) > 1:
        msg += " %r will try all compression methods and choose one with smaller result data." % constants.COMPRESSION_TYPE_BEST
        msg += " %r will try selected compression methods (--custom-compress) and choose one with smaller result data." % constants.COMPRESSION_TYPE_CUSTOM

    parser.add_argument('--compress', dest='compression', metavar='METHOD', action="append",
                        default=[constants.COMPRESSION_TYPE_NONE], help=msg)

    msg = "Enable compression of data blocks using one or more of the supported compression methods: %s"
    msg %= ', '.join('%r' % mth for mth in compression_methods_cmd[:-2])
    msg += ". To use two or more methods select this option in command line for each compression method."
    msg += " You can use <method>=<level> syntax, <level> can be integer or value from --compression-level."

    parser.add_argument('--force-compress', dest='compression_forced', action="store_true",
                        help="Force compression even if resulting data is bigger than original.")
    parser.add_argument('--minimal-compress-size', dest='compression_minimal_size', metavar='BYTES', type=int,
                        default=1024,
                        help="Minimal block data size for compression. Defaults to 1024 bytes. Value -1 means auto - per method absolute minimum. Do not compress if data size is less than BYTES long. If not forced to.")
    parser.add_argument('--minimal-compress-ratio', dest='compression_minimal_ratio', metavar='RATIO', type=float, default=0.05, help="Minimal data compression ratio. Defaults to 0.05 (5%%). Do not compress if ratio is less than RATIO. If not forced to.")

    levels = (constants.COMPRESSION_LEVEL_DEFAULT, constants.COMPRESSION_LEVEL_FAST, constants.COMPRESSION_LEVEL_NORM,
              constants.COMPRESSION_LEVEL_BEST)

    parser.add_argument('--compression-level', dest='compression_level', metavar="LEVEL",
                        default=constants.COMPRESSION_LEVEL_DEFAULT,
                        help="Compression level ratio: one of %s; or INT. Defaults to %r. Not all methods support this option." % (
                            ', '.join('%r' % lvl for lvl in levels), constants.COMPRESSION_LEVEL_DEFAULT
                        ))

    # Dynamically check for profiling support.
    try:
        # Using __import__() here because of pyflakes.
        for p in 'cProfile', 'pstats': __import__(p)
        parser.add_argument('--profile', action='store_true', default=False, help="Use the Python modules cProfile and pstats to create a profile of time spent in various function calls and print out a table of the slowest functions at exit (of course this slows everything down but it can nevertheless give a good indication of the hot spots).")
    except ImportError:
        logger.warning("No profiling support available, --profile option disabled.")
        logger.warning("If you're on Ubuntu try 'sudo apt-get install python-profiler'.")

    parser.add_argument('--mountpoint', help="specify mount point")

    args = parser.parse_args()

    if args.profile:
        sys.stderr.write("Enabling profiling..\n")
        import cProfile, pstats
        profile = '.dedupsqlfs.cprofile-%i' % time()
        profiler = cProfile.Profile()
        result = profiler.runcall(fuse_mount, args, compression_methods)
        profiler.dump_stats(profile)
        sys.stderr.write("\n Profiling statistics:\n\n")
        s = pstats.Stats(profile)
        s.sort_stats('calls').print_stats(0.1)
        s.sort_stats('cumtime').print_stats(0.1)
        s.sort_stats('tottime').print_stats(0.1)
        os.unlink(profile)
    else:
        result = fuse_mount(args, compression_methods)

    return result

if __name__ == '__main__':
    main()

# vim: ts=2 sw=2 et
