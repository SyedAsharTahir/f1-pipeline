import os,time,psycopg2,requests
from datetime import date

base="https://api.jolpi.ca/ergast/f1"#api
schema="raw"
pause=0.5
NULL=r"\N"

def get(path,**params):
    #get the jolpica endpoint and retry every 429s with backoff
    url=f"{base}/{path}.json"
    for attempt in range(6):
        response=requests.get(url,params=params,timeout=(10,90))
        if response.status_code==429 or response.status_code>=500:
            wait=2**attempt*2
            print(f"limited rate,sleeping {wait}s")
            time.sleep(wait)
            continue
        response.raise_for_status()
        time.sleep(pause)
        return response.json()["MRData"]
    raise RuntimeError(f"No lonnger using {url} after repeated 429s")

def getPages(path,limit=100):
    #each page of MRData for an endpoint
    offset=0
    while True:
        data=get(path,limit=limit,offset=offset)
        yield data
        offset+=limit
        if offset>=int(data["total"]):
            break

def fetchSchedule(year):
    races=[]
    for page in getPages(f"{year}/races"):
        races.extend(page["RaceTable"]["Races"])
    return races

def fetchResults(year,round):
    results=[]
    for page in getPages(f"{year}/{round}/results"):
        races=page["RaceTable"]["Races"]
        if races:
            results.extend(races[0]["Results"])
    return results


class RAW:
    def __init__(self,cur):
        self.cur=cur
        self.cols={}

    def columns(self,table):
        if table not in self.cols:
            self.cur.execute(
                "select column_name from information_schema.columns "
                "WHERE table_schema=%s and table_name=%s "
                "order by ordinal_position ",
                (schema,table)
                )
            self.cols[table]=[r[0] for r in self.cur.fetchall()]
            if not self.cols[table]:
                raise RuntimeError(f"Table {schema}.{table} not found")
        return self.cols[table]

    def col(self,table,name):
        for c in self.columns(table):
            if c.lower()==name.lower():
                return c
        raise KeyError(f"{table} has no column like '{name}'")

    def lookup(self,table,keyCol,value,idCol):
        k,i=self.col(table,keyCol),self.col(table,idCol)
        self.cur.execute(
            f'select "{i}" from {schema}."{table}" where "{k}"=%s limit 1',
            (value,),
        )
        row=self.cur.fetchone()
        return int(row[0]) if row else None

    def insert(self,table,row):
        lower={k.lower(): v for k, v in row.items()}
        cols=self.columns(table)
        Values=[]
        for c in cols:
            v=lower.get(c.lower())
            Values.append(NULL if v is None else str(v))
        colsSql=", ".join(f'"{c}"' for c in cols)
        ph=", ".join(["%s"]*len(cols))
        self.cur.execute(
            f'insert into {schema}."{table}" ({colsSql}) values ({ph})',Values
        )
    def get_or_create(self,table,id_col,ref_col,ref_value,build_row):
        existing=self.lookup(table, ref_col, ref_value, id_col)
        if existing is not None:
            return existing
        new_id=self.next_id(table,id_col)
        row =build_row(new_id)
        row[id_col]=new_id
        self.insert(table,row)
        print(f"+new {table} row: {ref_value}->{new_id}")
        return new_id

    def next_id(self,table,idCol):
        c=self.col(table,idCol)
        self.cur.execute(f'select coalesce(max("{c}"::int),0)+1 from {schema}."{table}"')
        return self.cur.fetchone()[0]

def splitDt(block):
    if not block:
        return None, None
    t = block.get("time")
    return block.get("date"),(t.rstrip("Z") if t else None)
 
 
def circuitRow(c):
    loc=c.get("Location",{})
    return {
        "circuitRef":c["circuitId"],
        "name":c.get("circuitName"),
        "location":loc.get("locality"),
        "country":loc.get("country"),
        "lat":loc.get("lat"),
        "lng":loc.get("long"),
        "alt":None,
        "url":c.get("url"),
    }
 
 
def driver_row(d):
    return {
        "driverRef":d["driverId"],
        "number":d.get("permanentNumber"),
        "code":d.get("code"),
        "forename":d.get("givenName"),
        "surname":d.get("familyName"),
        "dob":d.get("dateOfBirth"),
        "nationality":d.get("nationality"),
        "url":d.get("url"),
    }
 
 
def constructor_row(c):
    return {
        "constructorRef":c["constructorId"],
        "name":c.get("name"),
        "nationality":c.get("nationality"),
        "url":c.get("url"),
    }
 
 
def race_row(race_id, circuit_id, r):
    rd, rt = splitDt(r)
    fp1 = splitDt(r.get("FirstPractice"))
    fp2 = splitDt(r.get("SecondPractice"))
    fp3 = splitDt(r.get("ThirdPractice"))
    quali = splitDt(r.get("Qualifying"))
    sprint = splitDt(r.get("Sprint"))
    return {
        "raceId":race_id,
        "year":r["season"],
        "round":r["round"],
        "circuitId":circuit_id,
        "name":r.get("raceName"),
        "date":rd,
        "time":rt,
        "url":r.get("url"),
        "fp1_date":fp1[0], "fp1_time": fp1[1],
        "fp2_date":fp2[0], "fp2_time": fp2[1],
        "fp3_date":fp3[0], "fp3_time": fp3[1],
        "quali_date":quali[0], "quali_time": quali[1],
        "sprint_date":sprint[0], "sprint_time": sprint[1],
    }
 
 
def result_row(result_id, race_id, driver_id, constructor_id, status_id,
               position_order, res):
    fl=res.get("FastestLap", {})
    t =res.get("Time", {})
    pos_text=res.get("positionText", "")
    return {
        "resultId": result_id,
        "raceId": race_id,
        "driverId": driver_id,
        "constructorId": constructor_id,
        "number": res.get("number"),
        "grid": res.get("grid"),
        "position": res.get("position") if pos_text.isdigit() else None,
        "positionText": pos_text,
        "positionOrder": position_order,
        "points": res.get("points"),
        "laps": res.get("laps"),
        "time": t.get("time"),
        "milliseconds": t.get("millis"),
        "fastestLap": fl.get("lap"),
        "rank": fl.get("rank"),
        "fastestLapTime": fl.get("Time", {}).get("time"),
        "fastestLapSpeed": fl.get("AverageSpeed", {}).get("speed"),
        "statusId": status_id,
    }
 

def load_race(raw, race, results):
    label =f"{race['season']} R{race['round']}{race.get('raceName')}"
    print(f"Loading {label} ({len(results)} results)")
 
    circuit =race["Circuit"]
    circuit_id =raw.get_or_create(
        "circuits","circuitId","circuitRef",circuit["circuitId"],
        lambda _id: circuitRow(circuit),
    )
 
    race_id=raw.next_id("races", "raceId")
    raw.insert("races",race_row(race_id,circuit_id, race))
 
    result_id=raw.next_id("results", "resultId")
    for pos_order,res in enumerate(results, start=1):
        d,c=res["Driver"], res["Constructor"]
        driver_id=raw.get_or_create(
            "drivers","driverId","driverRef",d["driverId"],
            lambda _id, d=d:driver_row(d),
        )
        constructor_id =raw.get_or_create(
            "constructors","constructorId","constructorRef",c["constructorId"],
            lambda _id, c=c: constructor_row(c),
        )
        status_text =res.get("status", "Unknown")
        status_id =raw.get_or_create(
            "status","statusId","status",status_text,
            lambda _id, s=status_text:{"status": s},
        )
        raw.insert(
            "results",
            result_row(result_id,race_id,driver_id,constructor_id,
                       status_id,pos_order,res),
        )
        result_id += 1
 
def main():
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "f1"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
    )
    cur=conn.cursor()
    raw=RAW(cur)
    year_c,round_c=raw.col("races", "year"), raw.col("races", "round")
    cur.execute(f'select "{year_c}"::int, "{round_c}"::int from {schema}.races')
    have={(y, r) for y, r in cur.fetchall()}
    if not have:
        raise RuntimeError("raw.races is empty - load the Kaggle CSVs first")
    today = date.today()
    loaded = 0
    for year in range(max(y for y, _ in have), today.year + 1):
        for race in fetchSchedule(year):
            key =(int(race["season"]), int(race["round"]))
            if key in have or race["date"] > today.isoformat():
                continue
            results=fetchResults(*key)
            if not results:
                print(f"No results yet for {key}, M,oving ahead")
                continue
            try:
                load_race(raw,race,results)
                conn.commit()
                loaded+=1
            except Exception:
                conn.rollback()
                raise
    print(f"Done. Loaded {loaded} new race(s).")
    cur.close()
    conn.close()
 
if __name__=="__main__":
    main()