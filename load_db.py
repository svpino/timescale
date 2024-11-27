import os
from dotenv import load_dotenv
from datasets import load_dataset
import psycopg

load_dotenv()

DATABASE = os.environ["DATABASE"]

dataset = load_dataset("cnn_dailymail", "3.0.0")
test = dataset["test"]
test = test.shuffle(seed=42).select(range(0,1000))


with psycopg.connect(DATABASE) as con:
   with con.cursor(binary=True) as cur:
       with cur.copy("copy public.cnn_daily_mail (highlights, article) from stdin (format binary)") as cpy:
           cpy.set_types(['text', 'text'])
           for row in test:
               cpy.write_row((row["highlights"], row["article"]))

print("Data loading complete!")
