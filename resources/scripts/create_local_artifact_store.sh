#!/bin/bash


# Run from project's root
source .env
sudo mkdir /var/lib/${ARTIFACT_DIR_NAME}
sudo chown -R $USER:$USER /var/lib/${ARTIFACT_DIR_NAME}