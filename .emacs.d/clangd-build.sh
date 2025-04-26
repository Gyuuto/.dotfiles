#!/bin/bash

git clone https://github.com/llvm/llvm-project.git
cd llvm-project

git checkout llvmorg-20.1.3

cmake -B ./build ./llvm -DCMAKE_INSTALL_PREFIX=${HOME}/tools/ -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra"
cmake --build ./build -j8
cmake --build ./build --target install
