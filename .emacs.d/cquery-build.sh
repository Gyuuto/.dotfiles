#!/bin/sh

if [ ! -d ./cquery ]; then
    git clone --recursive https://github.com/cquery-project/cquery.git
fi

cd cquery
git submodule update --init
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=~/.emacs.d/cquery -DCMAKE_EXPORT_COMPILE_COMMANDS=YES -DCMAKE_GENERATOR_PLATFORM=x64
cmake --build .
cmake --build . --target install
