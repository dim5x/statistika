from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    rows = [
        [1, 2, 3, 4, 1, 2, 3, 4, 7],
        [1, 2, 3, 4, 1, 2, 3, 4, 7],
        [1, 2, 3, 4, 1, 2, 3, 4, 7],
        [1, 2, 3, 4, 1, 2, 3, 4, 7],
    ]
    return render_template('index.html', rows=rows, adjusted_sums=[1, 2, 3, 4], sums=[1, 2, 3, 4])


@app.route('/update', methods=['POST'])
def update():
    """
    Update a specific cell in the dataframe with the provided value.

    This function is an endpoint for a POST request to '/update'. It expects the request to contain the following
    parameters:
    - row_id: The index of the row to update.
    - column_id: The name of the column to update.
    - value: The new value to set in the specified cell.
"""

    try:
        row_id = int(request.form['row_id'])
        column_id = int(request.form['column_id'])
        value = request.form['value']

        print(f"Received data - row_id: {row_id}, column_id: {column_id}, value: {value}")

        # Update the dataframe
        # data.at[row_id, column_name] = value
        # print(data)
        # # Save back to CSV
        # data.to_csv('data.csv', index=False, header=False)

        return jsonify(success=True)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e))


if __name__ == '__main__':
    app.run(debug=True)
