#!/bin/bash

# Run from project's root
# NB: db must be runnning
source .env
export PGPASSWORD=$POSTGRES_PASSWORD

# Initialize db
# NB: Mlflow tables must exist
psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -a -f ./resources/sql/seed.sql