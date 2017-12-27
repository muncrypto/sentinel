#!/bin/bash
set -evx

mkdir ~/.muncore

# safety check
if [ ! -f ~/.muncore/.mun.conf ]; then
  cp share/mun.conf.example ~/.muncore/mun.conf
fi
