#!/bin/bash
git submodule init
git submodule update
git config -f .gitmodules submodule.SDM-SHACL.branch Trav-SHACL
git submodule update --remote
cd travshacl
git checkout Trav-SHACL
git branch -D local
git branch local
git checkout local
git am --abort
git am ../0001-required-changes.patch
cd ..