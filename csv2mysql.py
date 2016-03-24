import os
import re
import sys
import csv
import time
import argparse
import collections
import MySQLdb
import warnings 
# suppress annoying mysql warnings
warnings.filterwarnings(action='ignore', category=MySQLdb.Warning) 



def get_type(s):
    """Find type for this string
    """
    # try integer type
    try:
        v = int(s)
    except ValueError:
        pass
    else:
        if abs(v) > 2147483647:
            return 'bigint'
        else:
            return 'int'
    # try float type
    try:
        float(s)
    except ValueError:
        pass
    else:
        return 'double'

    # check for timestamp
    dt_formats = (
        ('%Y-%m-%d %H:%M:%S', 'datetime'),
        ('%Y-%m-%d %H:%M:%S.%f', 'datetime'),
        ('%Y-%m-%d', 'date'),
        ('%H:%M:%S', 'time'),
    )
    for dt_format, dt_type in dt_formats:
        try:
            time.strptime(s, dt_format)
        except ValueError:
            pass
        else:
            return dt_type
   
    # doesn't match any other types so assume text
    if len(s) > 255:
        return 'text'
    else:
        return 'varchar(255)'


def most_common(l):
    """Return most common value from list
    """
    # some formats trump others
    for dt_type in ('text', 'bigint'):
        if dt_type in l:
            return dt_type
    return max(l, key=l.count)


def get_col_types(input_file, max_rows=1000):
    """Find the type for each CSV column
    """
    csv_types = collections.defaultdict(list)
    reader = csv.reader(open(input_file))
    # test the first few rows for their data types
    for row_i, row in enumerate(reader):
        if row_i == 0:
            header = row
        else:
            for col_i, s in enumerate(row):
                data_type = get_type(s)
                csv_types[header[col_i]].append(data_type)
 
        if row_i == max_rows:
            break

    # take the most common data type for each row
    return [most_common(csv_types[col]) for col in header]


def get_schema(table, header, col_types):
    """Generate the schema for this table from given types and columns
    """
    schema_sql = """CREATE TABLE IF NOT EXISTS %s ( 
        id int NOT NULL AUTO_INCREMENT,""" % table 

    for col_name, col_type in zip(header, col_types):
        schema_sql += '\n%s %s,' % (col_name, col_type)

    schema_sql += """\nPRIMARY KEY (id)
        ) DEFAULT CHARSET=utf8;"""
    return schema_sql


def get_insert(table, header):
    """Generate the SQL for inserting rows
    """
    field_names = ', '.join(header)
    field_markers = ', '.join('%s' for col in header)
    return 'INSERT INTO %s (%s) VALUES (%s);' % \
        (table, field_names, field_markers)


def safe_col(s):
    return re.sub('\W+', '_', s.lower()).strip('_')


def mainToDatabase(input_file, user, password, host, table, database, max_inserts=10000):
    print "Importing `%s' into MySQL database `%s.%s'" % (input_file, database, table)
    db = MySQLdb.connect(host=host, user=user, passwd=password, charset='utf8')
    cursor = db.cursor()
    # create database and if doesn't exist
    cursor.execute('CREATE DATABASE IF NOT EXISTS %s;' % database)
    db.select_db(database)

    # define table
    print 'Analyzing column types ...'
    col_types = get_col_types(input_file)
    print col_types

    header = None
    for i, row in enumerate(csv.reader(open(input_file))):
        if header:
            cursor.execute(insert_sql, row)
            if i % max_inserts == 0:
                db.commit()
                print 'commit'
        else:
            header = [safe_col(col) for col in row]
            schema_sql = get_schema(table, header, col_types)
            print schema_sql
            # create table
            cursor.execute('DROP TABLE IF EXISTS %s;' % table)
            cursor.execute(schema_sql)
            # create index for more efficient access
            try:
                cursor.execute('CREATE INDEX ids ON %s (id);' % table)
            except MySQLdb.OperationalError:
                pass # index already exists

            print 'Inserting rows ...'
            # SQL string for inserting data
            insert_sql = get_insert(table, header)
            print insert_sql

    # commit rows to database
    print 'Committing rows to database ...'
    db.commit()
    print 'Done!'

def mainToFile(input_file, table, createtable):
    output_file = input_file + ".sql"
    print "Importing `%s' into MySQL file: `%s'" % (input_file, output_file)

    sql = []
    if createtable:
        sql.append('CREATE DATABASE IF NOT EXISTS %s;' % database)
        sql.append('USE DATABASE %s;' % database)

    # define table
    print 'Analyzing column types ...'
    col_types = get_col_types(input_file)
    print col_types
    
    header = None
    for i, row in enumerate(csv.reader(open(input_file))):
        if header:
            sql.append('INSERT INTO %s VALUES (%s);' % \
                       (table, ', '.join(['"%s"'%col for col in row])))
        else:
            header = [safe_col(col) for col in row]
            schema_sql = get_schema(table, header, col_types)
            print schema_sql
            # create table
            if createtable:
                sql.append('DROP TABLE IF EXISTS %s;' % table)
                sql.append(schema_sql)
                # create index for more efficient access
                sql.append('CREATE INDEX ids ON %s (id);' % table)

    ofile = open(output_file, "w")
    ofile.write("\n".join(sql))
    sys.stdout.write("\n".join(sql[:5]) + "\n...\n")
    ofile.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automatically insert CSV contents into MySQL')
    parser.add_argument('--table', dest='table', help='Set the name of the table. If not set the CSV filename will be used')
    parser.add_argument('--database', dest='database', default='test', help='Set the name of the database. If not set the test database will be used')
    parser.add_argument('--user', dest='user', default='root', help='The MySQL login username')
    parser.add_argument('--password', dest='password', default='', help='The MySQL login password')
    parser.add_argument('--host', dest='host', default='localhost', help='The MySQL host')
    parser.add_argument('--output', dest='output', default='database', help='Output to database or file. If set to file, script would only write {table name}.sql file')
    parser.add_argument('--createtable', dest='createtable', action='store_true', help='Excute "CREATE TABLE xxx" or not, default to NO')
    parser.set_defaults(createtable=False)
    #TODO: add argument to specify PRIMARY KEY
    parser.add_argument('input_file', help='The input CSV file')
    args = parser.parse_args(sys.argv[1:])
    if not args.table:
        # use input file name for table
        args.table = os.path.splitext(os.path.basename(args.input_file))[0]
    
    if args.output == "database":
        mainToDatabase(args.input_file, args.user, args.password, args.host, args.table, args.database)
    else:
        mainToFile(args.input_file, args.table, args.createtable)