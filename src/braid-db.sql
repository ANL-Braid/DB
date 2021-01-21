
create table records(
       /* auto-generated integer */
       record_int integer primary key,
       /* string name */
       name character varying(128),
       /* creation time */
       time timestamp
);

create table dependencies(
       /* auto-generated integer */
       record_int integer,
       dependency integer,
       /* creation time */
       time timestamp
);
