===========
 csv2mysql
===========


csv2mysql.py automatically parses a CSV file, creates MySQL table with appropriate field types, and then writes CSV data to the table.



Here is the usage: ::

    $ python csv2mysql.py -h
      usage: csv2mysql.py [-h] [--table TABLE] [--database DATABASE] [--user USER]
                          [--password PASSWORD] [--host HOST]
                          input_file
    
    Automatically insert CSV contents into MySQL
    
    positional arguments:
      input_file           The input CSV file
    
    optional arguments:
      -h, --help           show this help message and exit
      --table TABLE        Set the name of the table. If not set the CSV filename
                           will be used
      --database DATABASE  Set the name of the database. If not set the test
                           database will be used
      --user USER          The MySQL login username
      --password PASSWORD  The MySQL login password
      --host HOST          The MySQL host


Here is an example spreadsheet: ::

    Name  Age Height DOB        Active
    John  29  180.3  1980-11-20 12:30:20
    Sarah 25  174.5  1990-01-01 07:12:32
    Peter 45  156.4  1965-05-02 23:09:33
    
And now run the script: ::

    $ python csv2mysql.py --user=root --password=password --database=test --table=test test.csv
    Importing `test.csv' into MySQL database `test.test'
    Analyzing column types ...
    ['varchar(255)', 'integer', 'double', 'date', 'time']
    Inserting rows ...
    Committing rows to database ...
    Done!

Now check the results in MySQL: ::

    $ mysql -uroot -p test
    mysql> describe test;
    +--------+--------------+------+-----+---------+----------------+
    | Field  | Type         | Null | Key | Default | Extra          |
    +--------+--------------+------+-----+---------+----------------+
    | id     | int(11)      | NO   | PRI | NULL    | auto_increment |
    | name   | varchar(255) | YES  |     | NULL    |                |
    | age    | int(11)      | YES  |     | NULL    |                |
    | height | double       | YES  |     | NULL    |                |
    | dob    | date         | YES  |     | NULL    |                |
    | active | time         | YES  |     | NULL    |                |
    +--------+--------------+------+-----+---------+----------------+
    6 rows in set (0.01 sec)
    
    mysql> SELECT * FROM test;
    +----+-------+------+--------+------------+----------+
    | id | name  | age  | height | dob        | time     |
    +----+-------+------+--------+------------+----------+
    |  1 | John  |   29 |  180.3 | 30-10-1980 | 12:30:20 |
    |  2 | Sarah |   25 |  174.5 | 01-01-1990 | 07:12:32 |
    |  3 | Peter |   45 |  156.4 | 22-05-1965 | 23:09:33 |
    +----+-------+------+--------+------------+----------+
    3 rows in set (0.00 sec)

As you can see above the name has been stored as a varchar, age as an int, height as a double, dob as a date, and active as a time type.
