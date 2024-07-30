from flask import Flask, jsonify, request, render_template,  redirect, url_for
import requests
import time
import random
import redis
import os
import json
from flask_cors import CORS


app = Flask(__name__)
CORS(app)


# Initialize Redis client
redis_url = os.getenv('REDIS_URL', 'localhost')

if redis_url.startswith('redis://'):
    print("redis prod connected")
    r = redis.Redis.from_url(redis_url, db=0, decode_responses=True)
else:
    print("redis local connected")
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    
@app.route('/')
def docs():
    return render_template('docs.html')


def safe_request(url, json_payload, retries=5, initial_delay=3):
    """Make API requests with handling for rate limits using exponential backoff."""
    delay = initial_delay
    for attempt in range(retries):
        response = requests.post(url, json=json_payload)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429 or response.status_code == 503:
            sleep_time = delay + random.uniform(0, delay / 2)
            print(f"Rate limited or service unavailable. Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
            delay *= 2
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")
            return None
    raise Exception("Maximum retries exceeded with status code 429 or 503. Consider increasing retry count or delay.")


def fetch_proposals_paginated(space, order_direction='asc', initial_created_gt=None, force_refresh=False):
    """Fetch paginated proposals from Snapshot Hub GraphQL API, handling pagination only if a cursor is provided."""
    cache_key = f"proposals-{space}-{order_direction}-{initial_created_gt}"
    if not force_refresh:
        cached_data = r.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

    url = "https://hub.snapshot.org/graphql"

    query = """
    query ($where: ProposalWhere!, $orderDirection: OrderDirection!) {
      proposals(where: $where, orderDirection: $orderDirection) {
        id
        ipfs
        author
        created
        updated
        network
        symbol
        type
        plugins
        title
        body
        discussion
        choices
        start
        end
        quorum
        quorumType
        privacy
        snapshot
        state
        link
        scores
        scores_by_strategy
        scores_state
        scores_total
        scores_updated
        votes
        flagged
      }
    }
    """
    variables = {
        "where": {"space": space, "created_gt": initial_created_gt},
        "orderDirection": order_direction,
    }

    if initial_created_gt:
        variables['where']['created_gt'] = initial_created_gt  # Pagination based on cursor

    data = safe_request(url, {'query': query, 'variables': variables})
    proposals = []
    if data and 'data' in data and 'proposals' in data['data']:
        proposals = data['data']['proposals']
        if proposals:
            last_cursor = proposals[-1]['created']
            print("Cursor set: " + str(last_cursor))

        print("Setting Cache for 10 Hours")
        r.set(cache_key, json.dumps((proposals, last_cursor)), ex=36000)  # Cache for 10 hours

    return proposals, last_cursor


@app.route('/proposals/<space>', methods=['GET'])
def get_proposals(space):
    """Endpoint to fetch proposals."""
    print("Fetching Proposals Data...")
    cursor_str = request.args.get('cursor')
    refresh_cache = request.args.get('refresh', 'false').lower() == 'true'
    
    try:
        cursor = int(cursor_str) if cursor_str is not None else None
    except ValueError:
        return jsonify({"error": "Invalid cursor format. Cursor must be an integer."}), 400

    proposals_list, last_cursor = fetch_proposals_paginated(space, initial_created_gt=cursor, force_refresh=refresh_cache)

    formatted_proposals = {
        "proposals": proposals_list,
        "next_cursor": last_cursor,
        "@context": "http://daostar.org/schemas",
        "name": space
    }

    return jsonify(formatted_proposals)

@app.errorhandler(404)
def page_not_found(e):
    """Redirect to root if an incorrect endpoint is accessed."""
    return redirect(url_for('docs'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
