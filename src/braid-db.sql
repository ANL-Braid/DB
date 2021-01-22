
/*
    BRAID DB SQL
*/

/* The main list of records */
create table records(
       /* auto-generated integer */
       record_int integer primary key,
       /* string name */
       name character varying(128),
       /* creation time */
       time timestamp
);

/* Each record has some number of dependencies here */
create table dependencies(
       record_int integer,
       dependency integer,
       /* creation time */
       time timestamp
);

/* Each record has some number of URIs here */
create table uris(
       record_int integer,
       uri character varying(1024)
)
