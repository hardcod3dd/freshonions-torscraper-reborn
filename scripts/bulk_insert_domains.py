import pymysql

conn = pymysql.connect(host='db', user='root', password='8SLK3Bny', database='tor', autocommit=True)
cur = conn.cursor()

hosts = [h.strip() for h in open('/tmp/o.txt') if h.strip()]

sql = ("INSERT IGNORE INTO domain "
       "(host, port, `ssl`, is_up, title, created_at, visited_at, last_alive, "
       "next_scheduled_check, whatweb_at, portscanned_at, path_scanned_at, "
       "useful_404_scanned_at, dead_in_a_row) "
       "VALUES (%s, 80, 0, 0, '', NOW(), '1970-01-01', '1970-01-01', NOW(), "
       "'1970-01-01', '1970-01-01', '1970-01-01', '1970-01-01', 0)")

for h in hosts:
    cur.execute(sql, (h,))

print('Done:', len(hosts))
conn.close()
