
create table records(
       /* auto-generated integer */
       record_int serial primary key,
       /* string name e.g. 'X-032' */
       expid character varying(128) unique,
       /* creation time */
       time timestamp
);
