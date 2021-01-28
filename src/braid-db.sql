
/*
    BRAID DB SQL
*/

/* The main list of records */
create table records(
       /* auto-generated integer */
       record_id integer primary key,
       /* string name */
       name text,
       /* creation time */
       time timestamp
);

/* Each record has some number of dependencies here */
create table dependencies(
       record_id integer,
       dependency integer,
       /* creation time */
       time timestamp
);

/* Each record has some number of URIs here */
create table uris(
       record_id integer,
       uri text
);

/* Each record has some number of tags here
   type: 1=string, 2=integer, 3=float
   Cf. BraidTagType
*/
create table tags(
       record_id integer,
       key   text,
       value text,
       type  integer
);
