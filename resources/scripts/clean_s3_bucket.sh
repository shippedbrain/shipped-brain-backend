#!/bin/bash
source .env

aws s3 rm s3://${ARTIFACT_DIR_NAME}/ --recursive
