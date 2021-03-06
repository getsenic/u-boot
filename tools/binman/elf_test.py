# SPDX-License-Identifier: GPL-2.0+
# Copyright (c) 2017 Google, Inc
# Written by Simon Glass <sjg@chromium.org>
#
# Test for the elf module

import os
import sys
import unittest

import elf
import test_util

binman_dir = os.path.dirname(os.path.realpath(sys.argv[0]))


class FakeEntry:
    def __init__(self, contents_size):
        self.contents_size = contents_size
        self.data = 'a' * contents_size

    def GetPath(self):
        return 'entry_path'

class FakeSection:
    def __init__(self, sym_value=1):
        self.sym_value = sym_value

    def GetPath(self):
        return 'section_path'

    def LookupSymbol(self, name, weak, msg):
        return self.sym_value

class TestElf(unittest.TestCase):
    def testAllSymbols(self):
        fname = os.path.join(binman_dir, 'test', 'u_boot_ucode_ptr')
        syms = elf.GetSymbols(fname, [])
        self.assertIn('.ucode', syms)

    def testRegexSymbols(self):
        fname = os.path.join(binman_dir, 'test', 'u_boot_ucode_ptr')
        syms = elf.GetSymbols(fname, ['ucode'])
        self.assertIn('.ucode', syms)
        syms = elf.GetSymbols(fname, ['missing'])
        self.assertNotIn('.ucode', syms)
        syms = elf.GetSymbols(fname, ['missing', 'ucode'])
        self.assertIn('.ucode', syms)

    def testMissingFile(self):
        entry = FakeEntry(10)
        section = FakeSection()
        with self.assertRaises(ValueError) as e:
            syms = elf.LookupAndWriteSymbols('missing-file', entry, section)
        self.assertIn("Filename 'missing-file' not found in input path",
                      str(e.exception))

    def testOutsideFile(self):
        entry = FakeEntry(10)
        section = FakeSection()
        elf_fname = os.path.join(binman_dir, 'test', 'u_boot_binman_syms')
        with self.assertRaises(ValueError) as e:
            syms = elf.LookupAndWriteSymbols(elf_fname, entry, section)
        self.assertIn('entry_path has offset 4 (size 8) but the contents size '
                      'is a', str(e.exception))

    def testMissingImageStart(self):
        entry = FakeEntry(10)
        section = FakeSection()
        elf_fname = os.path.join(binman_dir, 'test', 'u_boot_binman_syms_bad')
        self.assertEqual(elf.LookupAndWriteSymbols(elf_fname, entry, section),
                         None)

    def testBadSymbolSize(self):
        entry = FakeEntry(10)
        section = FakeSection()
        elf_fname = os.path.join(binman_dir, 'test', 'u_boot_binman_syms_size')
        with self.assertRaises(ValueError) as e:
            syms = elf.LookupAndWriteSymbols(elf_fname, entry, section)
        self.assertIn('has size 1: only 4 and 8 are supported',
                      str(e.exception))

    def testNoValue(self):
        entry = FakeEntry(20)
        section = FakeSection(sym_value=None)
        elf_fname = os.path.join(binman_dir, 'test', 'u_boot_binman_syms')
        syms = elf.LookupAndWriteSymbols(elf_fname, entry, section)
        self.assertEqual(chr(255) * 16 + 'a' * 4, entry.data)

    def testDebug(self):
        elf.debug = True
        entry = FakeEntry(20)
        section = FakeSection()
        elf_fname = os.path.join(binman_dir, 'test', 'u_boot_binman_syms')
        with test_util.capture_sys_output() as (stdout, stderr):
            syms = elf.LookupAndWriteSymbols(elf_fname, entry, section)
        elf.debug = False
        self.assertTrue(len(stdout.getvalue()) > 0)


if __name__ == '__main__':
    unittest.main()
