#!/bin/bash

cd /home/homeassistant/.homeassistant
git rev-list --count master..origin/master
