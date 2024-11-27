import os
from dotenv import load_dotenv
from flask import Flask, send_file, jsonify
import psycopg

load_dotenv()

app = Flask(__name__)
DATABASE = os.environ["DATABASE"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]


def query_database(query: str, api_key: str = None):
    try:
        with psycopg.connect(DATABASE) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                if api_key:
                    cursor.execute(query, (api_key,))
                else:
                    cursor.execute(query)

                results = cursor.fetchall()

        return results
        
    except psycopg.Error as e:
        print(f"Database error: {e}")
        return str(e)


def jsonify_results(db_results):
    truncated_results = []
    for result in db_results:
        truncated_article = result['article'][:250]
        truncated_results.append({'id': result['id'], 'article': truncated_article})

    return jsonify({'results': truncated_results})

@app.route("/")
def index():
    return send_file('src/index.html')

@app.route("/full_text_search")
def fts():
    query = """
        select id, article
        from cnn_daily_mail
        where article @@ to_tsquery('english', '(death | kill) & police & car & dog');
    """
    db_results = query_database(query)
    return jsonify_results(db_results)

@app.route("/embedding_search")
def es():
    query = """
        with q as
        (
            select ai.openai_embed(
                'text-embedding-ada-002', 
                'Show me stories about police reports of deadly happenings involving cars and dogs.',
                api_key=>%s
            ) as q
        )
        select id, article
        from cnn_daily_mail
        order by embedding <=> (select q from q limit 1)
        limit 10;
    """
    db_results = query_database(query, OPENAI_API_KEY)
    return jsonify_results(db_results)

def main():
    app.run(port=int(os.environ.get('PORT', 80)))

if __name__ == "__main__":
    main()
