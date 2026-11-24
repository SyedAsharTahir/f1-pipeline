#laoding the tables from csv as exact to postgres
import csv,os,sys,psycopg2 
from pathlib import Path
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()#load all values into env variables
DATA_DIR =Path("data")

def connect():#read those values from load_dotenv() with os.environ to open connection to postgres
    return psycopg2.connect(
        host="localhost",
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )

def load(conn,name):
    path=DATA_DIR /f"{name}.csv"
    if not path.exists():
        print(f"skip {name}:{path} not found")
        return
    with open(path,newline="",encoding="utf-8") as f:#open the csv file for reading and closes file automatically 
        header=next(csv.reader(f))#wraps file in an iterator that produces one row at a time
        #next is used to get the header only i.e->"circuits.csv"
        #that list is now my col name
    cols=sql.SQL(", ").join(sql.SQL("{} text").format(sql.Identifier(c)) for c in header)#"circuitId" text,"name" text...
    table=sql.Identifier("raw",name)#builds a schema qualified name
    with conn.cursor() as cur:
        cur.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(table))
        cur.execute(sql.SQL("CREATE TABLE {} ({})").format(table,cols))
        with open(path,newline="",encoding="utf-8")as f:
            cur.copy_expert(sql.SQL("COPY {} FROM STDIN WITH (FORMAT csv,HEADER true)").format(table).as_string(conn),f)
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(table))
            print(f"{name}:{cur.fetchone()[0]} rows")
    conn.commit()

def main():
    names=sys.argv[1:] or sorted(p.stem for p in DATA_DIR.glob("*.csv"))
    conn=connect()
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
    conn.commit()
    for name in names:
        load(conn,name)
    conn.close()


if __name__ =="__main__":
    main()
