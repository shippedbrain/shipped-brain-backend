# Shipped Brain App

This the official Shipped Brain application repository.

## Tech Stack
* anaconda
* python >= 3.8
* SQLAlchemy
* FastAPI
* MLflow
* PostgreSQL
* Docker
* Docker Compose

## Structure
* `./resources/`: apps's resources; including scripts, sql schemas and env file
* `./api/`: the app's backend and services source code and Docker image
* `./api/src/`: app's source code
* `./app/`: the app's frontend

## How to run
You can run the whole app or solo application services. Nevertheless, you must always run the `mlflow` service and `postgres` service that are the app's core dependencies.<br>
The application can be launched using `docker-compose` (recommended) or directly via scripts.<br>

### Building the Database
Once you have a postgres databse up and running you must create the tables' schemas and basic initializations.<br>
Regardless the way postgres was launched - docker, systemd, external, etc. - the processe is the same, *note that this should be done only once*.<br>
Run from the root's path
1. Create schemas: `bash ./resources/scripts/create_db_tables.sh`
2. Init. db: `bash ./resources/scripts/init_db.sh`

### Run without Docker
...

### Run with Docker
Launch all services using `docker-compose`.

Before running you must setup the `.env` file. You can do this by simply copying the `./resources/.env.example` file to the root path (`.`) and to the `./api/` path. When copying the `.env.example*` file you must rename to `.env` in the target directories. 

Secondly, you must create a conda environment directory for the different containers to share. Run: `bash ./resources/scripts/create_local_conda_envs.sh`.


The `docker-compose` service lifts all required services to run the app:
* PostgreSQL database
* API Server
* Upload Server
* Prediciton Server
* Application UI: *nginx service*

**IMPORTANT**
Before running the application you must build the frontend's static files and add the `.env` file to the project's root and `./api/` path.

To build the frontend run the following command from the `./app/` path: `bash build.sh` (runs in ditatched mode).

#### Build and Run
If you're running the services for the first time or you've committed some changes to the source code, then you should run:

`bash build_and_run.sh` (runs in ditatched mode).

#### Run
If you've already build the app and just want to launch it then run: `bash run.sh`.