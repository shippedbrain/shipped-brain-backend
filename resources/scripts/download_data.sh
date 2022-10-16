#!/bin/bash

# Run from applications' root dir

wget -P ./resources/data "https://paperswithcode.com/media/about/papers-with-abstracts.json.gz"
wget -P ./resources/data "https://paperswithcode.com/media/about/links-between-papers-and-code.json.gz"
wget -P ./resources/data "https://paperswithcode.com/media/about/evaluation-tables.json.gz"
wget -P ./resources/data "https://paperswithcode.com/media/about/methods.json.gz"
wget -P ./resources/data "https://paperswithcode.com/media/about/datasets.json.gz"