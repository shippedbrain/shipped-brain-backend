Create Table users(
    id serial primary key,
    name varchar(255),
    username varchar(255) unique,
    email varchar(255) unique,
    description text,
    password varchar(255),
    created_at timestamp default now(),
    updated_at timestamp default now()
);

Create table api_calls(
    id serial primary key,
    model_name varchar(256) NOT NULL,
    user_id int NOT NULL references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    call_time timestamp default now(),
    constraint registered_models_fk FOREIGN KEY (model_name) references registered_models(name) ON UPDATE CASCADE ON DELETE CASCADE
);

Create table hashtags(
    id serial primary key,
    key varchar(32) NOT NULL,
    value varchar(64) NOT NULL,
    unique(key, value)
);

Create table user_hashtags(
    user_id integer NOT NULL references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    hashtag_id integer NOT NULL NOT NULL references hashtags(id) ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (user_id, hashtag_id)
);

Create table model_hashtags(
    hashtag_id integer NOT NULL references hashtags(id) ON DELETE CASCADE,
    model_name varchar(256) NOT NULL,
    PRIMARY KEY (hashtag_id, model_name),
    constraint registered_models_fk FOREIGN KEY (model_name) references registered_models(name) ON UPDATE CASCADE ON DELETE CASCADE
);


Create table user_social_networks(
    user_id integer NOT NULL references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    social_network integer NOT NULL,
    link varchar(256) NOT NULL,
    PRIMARY KEY (user_id, social_network)
);

Create table password_resets(
    id serial primary key,
    user_id int NOT NULL references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    user_email varchar(255) NOT NULL,
    reset_token varchar(255) NOT NULL,
    created_at timestamp default now()
);

Create table user_limits(
    user_id int NOT NULL references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    max_predictions int NOT NULL,
    max_batch_predictions int NOT NULL,
    max_models int NOT NULL,
    max_model_versions int NOT NULL,
    max_model_space int NOT NULL,
    dashboard_access boolean NOT NULL DEFAULT FALSE,
    can_request_model boolean NOT NULL DEFAULT FALSE,
    extra_dashboard_features boolean DEFAULT FALSE
);

Create table model_requests(
    id serial primary key,
    requested_by int NOT NULL references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    title varchar(255) NOT NULL,
    description text NOT NULL,
    input_data text,
    output_data text,
    prize text,
    status varchar(255) NOT NULL,
    fulfilled_by int NULL references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    fulfilled_at timestamp,
    created_at timestamp default now(),
    updated_at timestamp default now()
);

create table model_uploads(
    id serial primary key,
    user_id int NOT NULL references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    started_at timestamp default now() not null,
    finished_at timestamp,
    status varchar(12) default 'running' not null,
    model_name varchar(256),
    model_version integer,
    constraint model_versions_fk FOREIGN KEY (model_name, model_version) references model_versions(name, version) ON UPDATE CASCADE ON DELETE CASCADE
);

create table model_likes(
    model_name varchar(256),
    user_id integer references users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    created_at timestamp default now(),
    constraint registered_models_fk FOREIGN KEY (model_name) references registered_models(name) ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (model_name, user_id)
);

create table model_comments(
    id serial primary key,
    model_name varchar(256) references registered_models(name) ON UPDATE CASCADE ON DELETE CASCADE NOT NULL,
    user_id integer references users(id) ON UPDATE CASCADE ON DELETE CASCADE NOT NULL,
    comment text NOT NULL,
    created_at timestamp default now()
);
