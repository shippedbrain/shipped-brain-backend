#!/bin/bash


# Run from project's root
source .env
sudo mkdir ${CONDA_ENVS_PATH}
sudo chown -R $USER:$USER ${CONDA_ENVS_PATH}