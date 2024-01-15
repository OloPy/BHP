#!/bin/bash

USER="Wolf"
EMAIL="wolf@x.local"

git init

git config core.autocrlf true
git config --global user.name "$USER"
git config --global user.email $EMAIL

git add *

git commit -m 'original commit'
