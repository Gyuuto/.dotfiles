rem locate this file into .emacs.d/elpa/irony-XXXX/server/build

@echo off
setlocal

set LLVM_ROOT=D:\LLVM

set PATH=%PATH%;D:\mingw-w64\x86_64-7.2.0-posix-seh-rt_v5-rev1\mingw64\bin
set PATH=%PATH%;%LLVM_ROOT%\bin
set PATH=%PATH%;D:\cmake\bin
set PATH=%PATH%;%HOME%\.emacs.d\bin

set OPTS=^
-DLIBCLANG_LIBRARY="%LLVM_ROOT%/bin/libclang.dll" ^
-DLIBCLANG_INCLUDE_DIR="%LLVM_ROOT%/include" ^
-DCMAKE_INSTALL_PREFIX="%HOME%/.emacs.d/irony/"

set emacs_dir=%HOME%/Documents/Programming/emacs-25.3_1-x86_64

cmake %OPTS% -G "MinGW Makefiles" .. && cmake --build . --use-stderr --config Release --target install
