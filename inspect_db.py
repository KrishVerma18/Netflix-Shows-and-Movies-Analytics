import sqlite3
conn = sqlite3.connect('netflix_analytics.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [r[0] for r in c.fetchall()])
c.execute('PRAGMA table_info(netflix_titles)')
cols = c.fetchall()
print('Columns:')
for col in cols:
    print(f"  {col[1]} ({col[2]})")
conn.close()
