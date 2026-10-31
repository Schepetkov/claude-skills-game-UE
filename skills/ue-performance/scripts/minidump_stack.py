"""Readable call stack from an Unreal crash minidump without WinDbg/cdb (Windows only).

The crash reporter's CrashContext.runtime-xml often holds only "ntdll + offset" lines. This script reads
UEMinidump.dmp, takes the crashing thread's stack, scans it for return addresses inside the engine / game modules and
resolves them through dbghelp.dll (in System32) with the PDBs next to the DLLs - function, offset, file:line.

    pip install --user minidump
    python minidump_stack.py <Saved/Crashes/<id>/UEMinidump.dmp> [--depth 45] [--filter unrealeditor]

It is a stack SCAN, not an unwind: stale return addresses between real frames show up too (they look unrelated, e.g. a
template helper from another subsystem). Read it top-down: the first project-module frames under the faulting engine
frames are almost always the culprit. The PDBs must match the DLLs that crashed (rebuilding since then breaks it).
"""
import argparse
import ctypes
import logging
import os
import struct
from ctypes import wintypes as W

logging.disable(logging.CRITICAL)   # the minidump package logs a PEB error on UE dumps; harmless
from minidump.minidumpfile import MinidumpFile


class SYMBOL_INFOW(ctypes.Structure):
    _fields_ = [('SizeOfStruct', W.ULONG), ('TypeIndex', W.ULONG), ('Reserved', ctypes.c_uint64 * 2), ('Index', W.ULONG),
                ('Size', W.ULONG), ('ModBase', ctypes.c_uint64), ('Flags', W.ULONG), ('Value', ctypes.c_uint64),
                ('Address', ctypes.c_uint64), ('Register', W.ULONG), ('Scope', W.ULONG), ('Tag', W.ULONG),
                ('NameLen', W.ULONG), ('MaxNameLen', W.ULONG), ('Name', ctypes.c_wchar * 1024)]


class IMAGEHLP_LINEW64(ctypes.Structure):
    _fields_ = [('SizeOfStruct', W.DWORD), ('Key', ctypes.c_void_p), ('LineNumber', W.DWORD), ('FileName', W.LPWSTR),
                ('Address', ctypes.c_uint64)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dump')
    ap.add_argument('--depth', type=int, default=45, help='distinct frames to print')
    ap.add_argument('--filter', default='unrealeditor', help='substring of module paths to resolve (lower case); '
                                                             'use the game exe name for a packaged build')
    a = ap.parse_args()

    mf = MinidumpFile.parse(a.dump)
    raw = open(a.dump, 'rb').read()
    exc = mf.exception.exception_records[0]
    er = exc.ExceptionRecord
    print('exception %x at %x, thread %d, info %s' % (er.ExceptionCode_raw, er.ExceptionAddress, exc.ThreadId,
                                                      er.ExceptionInformation[:2]))
    ctx = raw[exc.ThreadContext.Rva:exc.ThreadContext.Rva + exc.ThreadContext.DataSize]
    rsp, rip = struct.unpack_from('<Q', ctx, 0x98)[0], struct.unpack_from('<Q', ctx, 0xF8)[0]   # x64 CONTEXT

    mods = [(m.baseaddress, m.baseaddress + m.size, m.name) for m in mf.modules.modules]

    def module_of(addr):
        for base, end, name in mods:
            if base <= addr < end:
                return base, end, name
        return None, None, None

    dbg = ctypes.WinDLL('dbghelp.dll')
    proc = W.HANDLE(0x1234)   # any unique value: no live process
    dbg.SymSetOptions(0x2 | 0x10 | 0x200)   # UNDNAME | LOAD_LINES | FAIL_CRITICAL_ERRORS
    dbg.SymInitializeW.argtypes = [W.HANDLE, W.LPCWSTR, W.BOOL]
    dbg.SymInitializeW(proc, None, False)
    dbg.SymLoadModuleExW.restype = ctypes.c_uint64
    dbg.SymLoadModuleExW.argtypes = [W.HANDLE, W.HANDLE, W.LPCWSTR, W.LPCWSTR, ctypes.c_uint64, W.DWORD, ctypes.c_void_p, W.DWORD]
    dbg.SymFromAddrW.argtypes = [W.HANDLE, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(SYMBOL_INFOW)]
    dbg.SymGetLineFromAddrW64.argtypes = [W.HANDLE, ctypes.c_uint64, ctypes.POINTER(W.DWORD), ctypes.POINTER(IMAGEHLP_LINEW64)]
    loaded = set()

    def resolve(addr):
        base, end, name = module_of(addr)
        if not name:
            return None
        short = os.path.basename(name)
        if a.filter not in name.lower():
            return '%s+%x' % (short, addr - base)
        if name not in loaded:
            dbg.SymLoadModuleExW(proc, None, name, None, base, end - base, None, 0)
            loaded.add(name)
        s = SYMBOL_INFOW()
        s.SizeOfStruct = ctypes.sizeof(SYMBOL_INFOW) - 1024 * 2
        s.MaxNameLen = 1024
        disp = ctypes.c_uint64()
        if not dbg.SymFromAddrW(proc, addr, ctypes.byref(disp), ctypes.byref(s)):
            return '%s+%x' % (short, addr - base)
        line, ldisp, where = IMAGEHLP_LINEW64(), W.DWORD(), ''
        line.SizeOfStruct = ctypes.sizeof(IMAGEHLP_LINEW64)
        if dbg.SymGetLineFromAddrW64(proc, addr, ctypes.byref(ldisp), ctypes.byref(line)):
            where = ' %s:%d' % (os.path.basename(line.FileName), line.LineNumber)
        return '%s!%s+%x%s' % (short, s.Name, disp.value, where)

    print('RIP', resolve(rip) or '%x (no module - a call through a null/freed pointer)' % rip)
    thread = [t for t in mf.threads.threads if t.ThreadId == exc.ThreadId][0]
    st = thread.Stack
    mem = raw[st.MemoryLocation.Rva:st.MemoryLocation.Rva + st.MemoryLocation.DataSize]
    shown, last = 0, None
    for off in range(max(0, rsp - st.StartOfMemoryRange), len(mem) - 7, 8):
        value = struct.unpack_from('<Q', mem, off)[0]
        _, _, name = module_of(value)
        if name and a.filter in name.lower():
            frame = resolve(value)
            if frame and frame != last:
                print('  ', frame)
                last, shown = frame, shown + 1
        if shown >= a.depth:
            break


if __name__ == '__main__':
    main()
