#!/bin/bash

# copy this file into: /home/FooBar/PyLucid_env/manage.sh

function verbose_eval {
    echo - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    echo $*
    echo - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    eval $*
    echo
}

echo _____________________________________________________________________
echo activate the virtual environment:
verbose_eval source bin/activate

echo _____________________________________________________________________
echo execute manage.py
verbose_eval python src/pylucid/pylucid_project/manage.py $*

echo ---------------------------------------------------------------------